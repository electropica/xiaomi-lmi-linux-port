/* SPDX-License-Identifier: MIT
 * Native V4L2-to-PipeWire rear camera source for the Linux 7 line.
 *
 * Reads a V4L2 capture node (the CAMSS VFE output of the lmi board) and
 * publishes it as a PipeWire camera node, so that the GStreamer PipeWire
 * device provider of the session enumerates one camera and the camera
 * application gets a viewfinder instead of an empty window.
 *
 * Contract with the launcher:
 *   - "V4L2_SOURCE_READY <device> <width>x<height>" on stdout means that a
 *     real frame arrived, so the camera is there. The launcher uses that line
 *     to decide between the camera and the explanation window.
 *   - exit status 3 means that no candidate node delivered a frame, which is
 *     the case when the sensor is not bound.
 *   - the producer follows the foreground lease of the launcher: the video
 *     node is only streamed while the lease says the camera application is in
 *     the foreground, and the producer exits when the lease disappears.
 *
 * The initial probe, which lasts at most PROBE_SECONDS and exists only to
 * tell a real camera from an empty video node, is the one moment where the
 * sensor is powered outside the foreground state. It only happens when the
 * user has just asked for the camera application.
 *
 * Uses the public PipeWire stream API and the public V4L2 ioctls. It never
 * opens a microphone and never records.
 */
#include <errno.h>
#include <fcntl.h>
#include <glob.h>
#include <linux/videodev2.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include <spa/param/video/format-utils.h>
#include <pipewire/pipewire.h>

#define DEFAULT_LEASE "/run/user/1000/lmi-snapshot/foreground.json"
#define DEFAULT_WIDTH 1280
#define DEFAULT_HEIGHT 720
#define MAX_BUFFERS 4
#define TICK_NS 10000000LL
#define PROBE_SECONDS 3
#define PROBE_EXIT 3

struct v4l2_map {
	void *start;
	size_t length;
};

struct app {
	struct pw_main_loop *loop;
	struct pw_context *context;
	struct pw_core *core;
	struct pw_stream *stream;
	struct spa_hook listener;
	struct spa_source *tick;
	struct spa_video_info_raw format;

	const char *lease_path;
	int fd;
	struct v4l2_map maps[MAX_BUFFERS];
	unsigned map_count;
	unsigned char *frame;
	size_t frame_size;
	unsigned frames;
	unsigned drained;
	uint32_t width;
	uint32_t height;
	uint32_t bytesperline;
	uint32_t sizeimage;
	bool fresh;
	bool streaming;
	double first_frame;
};

/* The foreground lease of the launcher. The producer only streams while the
 * lease says the camera application is in the foreground, and it stops when
 * the lease is gone, which is what happens when the launcher dies. */
static int lease_state(const char *path, pid_t *pid)
{
	struct stat st;
	if (stat(path, &st) < 0)
		return -1;
	FILE *file = fopen(path, "r");
	if (!file)
		return -1;
	char text[512] = { 0 };
	size_t read = fread(text, 1, sizeof(text) - 1, file);
	fclose(file);
	if (!read)
		return -1;
	char *active = strstr(text, "\"active\":true");
	char *pid_field = strstr(text, "\"pid\":");
	if (!active || !pid_field)
		return 0;
	*pid = (pid_t)strtol(pid_field + 6, NULL, 10);
	return 1;
}

static void quit(void *opaque, uint64_t expirations)
{
	(void)expirations;
	struct app *a = opaque;
	pw_main_loop_quit(a->loop);
}

static void interrupted(void *opaque, int sig)
{
	(void)sig;
	struct app *a = opaque;
	pw_main_loop_quit(a->loop);
}

/* V4L2 side. The device is opened read/write, because the capture path of
 * this board needs the stream on commands and the ioctl interface. */
static int v4l2_open(const char *path)
{
	int fd = open(path, O_RDWR | O_NONBLOCK | O_CLOEXEC);
	if (fd < 0)
		return -1;
	struct v4l2_capability cap;
	memset(&cap, 0, sizeof(cap));
	if (ioctl(fd, VIDIOC_QUERYCAP, &cap) < 0) {
		close(fd);
		return -1;
	}
	if (!(cap.capabilities & V4L2_CAP_VIDEO_CAPTURE) ||
	    !(cap.capabilities & V4L2_CAP_STREAMING)) {
		close(fd);
		return -1;
	}
	return fd;
}

static int v4l2_configure(struct app *a, uint32_t width, uint32_t height)
{
	struct v4l2_format fmt;
	memset(&fmt, 0, sizeof(fmt));
	fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	fmt.fmt.pix.width = width;
	fmt.fmt.pix.height = height;
	fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_NV12;
	fmt.fmt.pix.field = V4L2_FIELD_NONE;
	if (ioctl(a->fd, VIDIOC_S_FMT, &fmt) < 0)
		return -1;

	memset(&fmt, 0, sizeof(fmt));
	fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	if (ioctl(a->fd, VIDIOC_G_FMT, &fmt) < 0)
		return -1;
	if (fmt.fmt.pix.pixelformat != V4L2_PIX_FMT_NV12) {
		fprintf(stderr, "V4L2_FORMAT_NOT_NV12 %s\n", a->lease_path);
		return -1;
	}
	a->width = fmt.fmt.pix.width;
	a->height = fmt.fmt.pix.height;
	a->bytesperline = fmt.fmt.pix.bytesperline;
	a->sizeimage = fmt.fmt.pix.sizeimage;
	return 0;
}

static int v4l2_stream_on(struct app *a)
{
	struct v4l2_requestbuffers req;
	memset(&req, 0, sizeof(req));
	req.count = MAX_BUFFERS;
	req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	req.memory = V4L2_MEMORY_MMAP;
	if (ioctl(a->fd, VIDIOC_REQBUFS, &req) < 0)
		return -1;
	if (req.count < 2)
		return -1;
	a->map_count = req.count;
	for (unsigned i = 0; i < req.count; i++) {
		struct v4l2_buffer buf;
		memset(&buf, 0, sizeof(buf));
		buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
		buf.memory = V4L2_MEMORY_MMAP;
		buf.index = i;
		if (ioctl(a->fd, VIDIOC_QUERYBUF, &buf) < 0)
			return -1;
		void *start = mmap(NULL, buf.length, PROT_READ | PROT_WRITE,
				   MAP_SHARED, a->fd, buf.m.offset);
		if (start == MAP_FAILED)
			return -1;
		a->maps[i].start = start;
		a->maps[i].length = buf.length;
	}
	for (unsigned i = 0; i < req.count; i++) {
		struct v4l2_buffer buf;
		memset(&buf, 0, sizeof(buf));
		buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
		buf.memory = V4L2_MEMORY_MMAP;
		buf.index = i;
		if (ioctl(a->fd, VIDIOC_QBUF, &buf) < 0)
			return -1;
	}
	int type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	if (ioctl(a->fd, VIDIOC_STREAMON, &type) < 0)
		return -1;
	a->streaming = true;
	return 0;
}

static void v4l2_stream_off(struct app *a)
{
	int type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	ioctl(a->fd, VIDIOC_STREAMOFF, &type);
	for (unsigned i = 0; i < a->map_count; i++)
		if (a->maps[i].start && a->maps[i].start != MAP_FAILED)
			munmap(a->maps[i].start, a->maps[i].length);
	a->map_count = 0;
	a->streaming = false;
}

/* Take one frame out of the video node. The frame is copied into the
 * application buffer, because the PipeWire buffer owns its own memory. */
static bool v4l2_take_frame(struct app *a)
{
	struct v4l2_buffer buf;
	memset(&buf, 0, sizeof(buf));
	buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	buf.memory = V4L2_MEMORY_MMAP;
	if (ioctl(a->fd, VIDIOC_DQBUF, &buf) < 0)
		return false;
	bool copied = false;
	if (buf.index < a->map_count && a->maps[buf.index].start) {
		size_t used = buf.bytesused ? buf.bytesused : a->sizeimage;
		if (used > a->frame_size)
			used = a->frame_size;
		memcpy(a->frame, a->maps[buf.index].start, used);
		copied = true;
	}
	ioctl(a->fd, VIDIOC_QBUF, &buf);
	a->drained++;
	return copied;
}

static void tick(void *opaque, uint64_t expirations)
{
	(void)expirations;
	struct app *a = opaque;
	if (v4l2_take_frame(a)) {
		a->fresh = true;
		pw_stream_trigger_process(a->stream);
	}
}

/* PipeWire side. */
static void state(void *opaque, enum pw_stream_state old, enum pw_stream_state now,
		  const char *error)
{
	(void)old;
	struct app *a = opaque;
	fprintf(stderr, "STATE %s %s\n", pw_stream_state_as_string(now),
		error ? error : "");
	if (now == PW_STREAM_STATE_ERROR) {
		pw_main_loop_quit(a->loop);
		return;
	}
	if (now == PW_STREAM_STATE_STREAMING) {
		struct timespec first = { 0, 1 };
		struct timespec period = { 0, TICK_NS };
		pw_loop_update_timer(pw_main_loop_get_loop(a->loop), a->tick, &first,
				     &period, false);
	} else {
		pw_loop_update_timer(pw_main_loop_get_loop(a->loop), a->tick, NULL, NULL,
				     false);
	}
}

static void format(void *opaque, uint32_t id, const struct spa_pod *param)
{
	struct app *a = opaque;
	if (id != SPA_PARAM_Format || !param)
		return;
	struct spa_video_info_raw proposed;
	memset(&proposed, 0, sizeof(proposed));
	if (spa_format_video_raw_parse(param, &proposed) < 0 ||
	    proposed.format != SPA_VIDEO_FORMAT_NV12 ||
	    proposed.size.width != a->width || proposed.size.height != a->height) {
		pw_stream_set_error(a->stream, -EINVAL,
				    "Expected NV12 %ux%u from the video node",
				    a->width, a->height);
		return;
	}
	a->format = proposed;
	uint8_t storage[512];
	struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(storage, sizeof(storage));
	const struct spa_pod *params[2];
	params[0] = spa_pod_builder_add_object(&builder, SPA_TYPE_OBJECT_ParamBuffers,
					       SPA_PARAM_Buffers,
					       SPA_PARAM_BUFFERS_buffers,
					       SPA_POD_CHOICE_RANGE_Int(8, 2, 16),
					       SPA_PARAM_BUFFERS_blocks, SPA_POD_Int(1),
					       SPA_PARAM_BUFFERS_size,
					       SPA_POD_Int((int)(a->bytesperline * a->height)),
					       SPA_PARAM_BUFFERS_stride,
					       SPA_POD_Int((int)a->bytesperline));
	params[1] = spa_pod_builder_add_object(&builder, SPA_TYPE_OBJECT_ParamMeta,
					       SPA_PARAM_Meta, SPA_PARAM_META_type,
					       SPA_POD_Id(SPA_META_Header),
					       SPA_PARAM_META_size,
					       SPA_POD_Int(sizeof(struct spa_meta_header)));
	pw_stream_update_params(a->stream, params, 2);
}

static void process(void *opaque)
{
	struct app *a = opaque;
	if (!a->fresh)
		return;
	struct pw_buffer *b = pw_stream_dequeue_buffer(a->stream);
	if (!b)
		return;
	a->fresh = false;
	struct spa_buffer *buf = b->buffer;
	if (!buf->n_datas || !buf->datas[0].data || !buf->datas[0].chunk ||
	    buf->datas[0].maxsize < a->bytesperline * a->height) {
		pw_stream_queue_buffer(a->stream, b);
		return;
	}
	memcpy(buf->datas[0].data, a->frame, a->bytesperline * a->height);
	struct spa_meta_header *head =
		spa_buffer_find_meta_data(buf, SPA_META_Header, sizeof(*head));
	if (head) {
		head->pts = -1;
		head->flags = 0;
		head->seq = a->frames;
		head->dts_offset = 0;
	}
	buf->datas[0].chunk->offset = 0;
	buf->datas[0].chunk->size = a->bytesperline * a->height;
	buf->datas[0].chunk->stride = a->bytesperline;
	buf->datas[0].chunk->flags = 0;
	b->size = 1;
	a->frames++;
	pw_stream_queue_buffer(a->stream, b);
}

static const struct pw_stream_events events = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = state,
	.param_changed = format,
	.process = process,
};

static double now_seconds(void)
{
	struct timespec now;
	clock_gettime(CLOCK_MONOTONIC, &now);
	return now.tv_sec + now.tv_nsec / 1e9;
}

/* Open one candidate node and wait for a real frame. Returns 0 when the
 * camera is there, and a negative value otherwise. */
static int probe_device(const char *device, uint32_t *width, uint32_t *height)
{
	struct app probe;
	memset(&probe, 0, sizeof(probe));
	probe.fd = v4l2_open(device);
	if (probe.fd < 0)
		return -1;
	if (v4l2_configure(&probe, DEFAULT_WIDTH, DEFAULT_HEIGHT) < 0) {
		close(probe.fd);
		return -1;
	}
	probe.frame_size = (size_t)probe.bytesperline * probe.height;
	probe.frame = malloc(probe.frame_size);
	if (!probe.frame) {
		close(probe.fd);
		return -1;
	}
	if (v4l2_stream_on(&probe) < 0) {
		free(probe.frame);
		close(probe.fd);
		return -1;
	}
	double deadline = now_seconds() + PROBE_SECONDS;
	bool got = false;
	while (now_seconds() < deadline) {
		if (v4l2_take_frame(&probe)) {
			got = true;
			break;
		}
		struct timespec pause = { 0, 20000000 };
		nanosleep(&pause, NULL);
	}
	v4l2_stream_off(&probe);
	free(probe.frame);
	close(probe.fd);
	if (!got)
		return -1;
	*width = probe.width;
	*height = probe.height;
	return 0;
}

/* Look for the video node that carries the camera. */
static int find_source(char *chosen, size_t size, uint32_t *width, uint32_t *height)
{
	char candidates[64][64];
	unsigned count = 0;
	if (strcmp(chosen, "auto") != 0) {
		snprintf(candidates[count++], sizeof(candidates[0]), "%s", chosen);
	} else {
		glob_t paths;
		memset(&paths, 0, sizeof(paths));
		if (glob("/dev/video*", 0, NULL, &paths) == 0) {
			for (size_t i = 0; i < paths.gl_pathc && count < 64; i++)
				snprintf(candidates[count++], sizeof(candidates[0]), "%s",
					 paths.gl_pathv[i]);
		}
		globfree(&paths);
	}
	for (unsigned i = 0; i < count; i++) {
		fprintf(stderr, "V4L2_CANDIDATE %s\n", candidates[i]);
		if (probe_device(candidates[i], width, height) == 0) {
			size_t length = strlen(candidates[i]);
			if (length < size) {
				memcpy(chosen, candidates[i], length + 1);
				return 0;
			}
			return -1;
		}
		fprintf(stderr, "V4L2_NO_FRAME %s\n", candidates[i]);
	}
	return -1;
}

/* The foreground lease of the launcher keeps the camera honest: the node is
 * only streamed while the camera application is in the foreground, and the
 * producer stops when the lease is gone, which is what happens when the
 * launcher dies. */
static void lease_tick(void *opaque, uint64_t expirations)
{
	(void)expirations;
	struct app *a = opaque;
	pid_t lease_pid = 0;
	int state = lease_state(a->lease_path, &lease_pid);
	if (state < 0) {
		fprintf(stderr, "V4L2_LEASE_GONE\n");
		pw_main_loop_quit(a->loop);
		return;
	}
	if (state == 1 && lease_pid != getpid() && lease_pid != getppid()) {
		fprintf(stderr, "V4L2_LEASE_OTHER\n");
		pw_main_loop_quit(a->loop);
		return;
	}
	if (state == 1 && !a->streaming) {
		if (v4l2_stream_on(a) == 0)
			fprintf(stderr, "V4L2_RESUMED\n");
	} else if (state == 0 && a->streaming) {
		v4l2_stream_off(a);
		fprintf(stderr, "V4L2_PAUSED\n");
	}
}

int main(int argc, char **argv)
{
	if (argc < 1 || argc > 4) {
		fprintf(stderr,
			"Usage: native-pipewire-v4l2-source [DEVICE|auto] [SECONDS:0..3600] [LEASE]\n"
			"  DEVICE   video node, or auto to look for the one that frames\n"
			"  SECONDS  lifetime, 0 means until the signal\n"
			"  LEASE    foreground lease of the launcher\n");
		return 2;
	}
	char device[64] = "auto";
	long seconds = 0;
	const char *lease = DEFAULT_LEASE;
	if (argc >= 2)
		snprintf(device, sizeof(device), "%s", argv[1]);
	if (argc >= 3) {
		char *end = NULL;
		seconds = strtol(argv[2], &end, 10);
		if (!end || *end || seconds < 0 || seconds > 3600)
			return 2;
	}
	if (argc >= 4)
		lease = argv[3];

	uint32_t width = 0, height = 0;
	if (find_source(device, sizeof(device), &width, &height) < 0) {
		fprintf(stderr, "V4L2_NO_FRAME_ALL\n");
		return PROBE_EXIT;
	}
	fprintf(stderr, "V4L2_SOURCE %s %ux%u\n", device, width, height);

	struct app a;
	memset(&a, 0, sizeof(a));
	a.lease_path = lease;
	a.fd = v4l2_open(device);
	if (a.fd < 0) {
		fprintf(stderr, "V4L2_OPEN_FAILED %s\n", device);
		return 1;
	}
	if (v4l2_configure(&a, width, height) < 0) {
		fprintf(stderr, "V4L2_CONFIGURE_FAILED %s\n", device);
		close(a.fd);
		return 1;
	}
	a.frame_size = (size_t)a.bytesperline * a.height;
	a.frame = malloc(a.frame_size);
	if (!a.frame) {
		close(a.fd);
		return 1;
	}
	if (v4l2_stream_on(&a) < 0) {
		fprintf(stderr, "V4L2_STREAM_FAILED %s\n", device);
		free(a.frame);
		close(a.fd);
		return 1;
	}
	a.first_frame = now_seconds();
	printf("V4L2_SOURCE_READY %s %ux%u\n", device, a.width, a.height);
	fflush(stdout);

	pw_init(&argc, &argv);
	a.loop = pw_main_loop_new(NULL);
	if (!a.loop) {
		v4l2_stream_off(&a);
		free(a.frame);
		close(a.fd);
		return 1;
	}
	struct pw_loop *loop = pw_main_loop_get_loop(a.loop);
	pw_loop_add_signal(loop, SIGINT, interrupted, &a);
	pw_loop_add_signal(loop, SIGTERM, interrupted, &a);
	a.context = pw_context_new(loop, NULL, 0);
	a.core = pw_context_connect(a.context, NULL, 0);
	if (!a.core) {
		fprintf(stderr, "No user PipeWire core\n");
		v4l2_stream_off(&a);
		free(a.frame);
		close(a.fd);
		return 1;
	}
	a.tick = pw_loop_add_timer(loop, tick, &a);
	if (seconds > 0) {
		struct spa_source *expiry = pw_loop_add_timer(loop, quit, &a);
		struct timespec limit = { seconds, 0 };
		pw_loop_update_timer(loop, expiry, &limit, NULL, false);
	}

	char description[128];
	snprintf(description, sizeof(description), "LMI rear camera (V4L2 %s)", device);
	a.stream = pw_stream_new(a.core, "LMI V4L2 rear camera source",
				 pw_properties_new(
					 PW_KEY_MEDIA_CLASS, "Video/Source",
					 PW_KEY_MEDIA_TYPE, "Video",
					 PW_KEY_MEDIA_CATEGORY, "Capture",
					 PW_KEY_MEDIA_ROLE, "Camera",
					 PW_KEY_NODE_NAME, "lmi-camera-rear-v4l2",
					 PW_KEY_NODE_DESCRIPTION, description,
					 "api.v4l2.device", device,
					 "api.v4l2.path", device,
					 "api.libcamera.location", "back",
					 PW_KEY_NODE_SUPPORTS_REQUEST, "1", NULL));
	if (!a.stream) {
		fprintf(stderr, "Cannot create the PipeWire stream\n");
		v4l2_stream_off(&a);
		free(a.frame);
		close(a.fd);
		return 1;
	}
	pw_stream_add_listener(a.stream, &a.listener, &events, &a);

	uint8_t storage[512];
	struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(storage, sizeof(storage));
	const struct spa_pod *param = spa_pod_builder_add_object(
		&builder, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat,
		SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
		SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
		SPA_FORMAT_VIDEO_format, SPA_POD_Id(SPA_VIDEO_FORMAT_NV12),
		SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&SPA_RECTANGLE(a.width, a.height)),
		SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&SPA_FRACTION(30, 1)));
	int rc = pw_stream_connect(a.stream, PW_DIRECTION_OUTPUT, PW_ID_ANY,
				    PW_STREAM_FLAG_DRIVER | PW_STREAM_FLAG_MAP_BUFFERS,
				    &param, 1);
	if (rc < 0) {
		fprintf(stderr, "Cannot connect the PipeWire stream: %s\n",
			strerror(-rc));
		v4l2_stream_off(&a);
		free(a.frame);
		close(a.fd);
		return 1;
	}

	/* The lease keeps the camera honest: the node is only streamed while the
	 * camera application is in the foreground, and the producer stops when
	 * the lease disappears with the launcher. */
	struct spa_source *lease_timer = pw_loop_add_timer(loop, lease_tick, &a);
	struct timespec lease_period = { 0, 250000000 };
	pw_loop_update_timer(loop, lease_timer, NULL, &lease_period, false);
	pw_main_loop_run(a.loop);

	fprintf(stderr, "FRAMES %u DRAINED %u\n", a.frames, a.drained);
	v4l2_stream_off(&a);
	pw_stream_destroy(a.stream);
	pw_core_disconnect(a.core);
	pw_context_destroy(a.context);
	pw_main_loop_destroy(a.loop);
	pw_deinit();
	free(a.frame);
	close(a.fd);
	return 0;
}
