/* SPDX-License-Identifier: MIT
 * Native V4L2 Bayer-to-PipeWire rear camera source for the Linux 7 line.
 *
 * The CAMSS VFE of this board has no process block: from a Bayer sensor it
 * only delivers the Bayer bytes, in the packed 10 bit layout of the V4L2
 * specification and on one plane. The camera application cannot show that
 * directly, and the producer of the OEM path expects a NV12 image that this
 * hardware does not deliver at all.
 *
 * This producer therefore does the whole job itself:
 *   - it opens the media controller and finds the chain that leads from the
 *     rear sensor to the video node, with the links that the driver leaves
 *     disabled;
 *   - it enables those two links and sets the format of the sensor, of the
 *     CSIPHY, of the CSID and of the VFE, and it restores all of it when it
 *     stops;
 *   - it captures the Bayer frames of the video node, converts them to BGRx
 *     with a bilinear demosaic, a measured black level and a white balance,
 *     and publishes them as a PipeWire camera node.
 *
 * The contract with the launcher is the one of the other producer:
 *   - "V4L2_SOURCE_READY <device> <width>x<height>" on stdout means that a
 *     real frame arrived, so the camera is there;
 *   - exit status 3 means that no candidate node delivered a frame;
 *   - the node is only streamed while the foreground lease of the launcher
 *     says that the camera application is in the foreground.
 */
#include <errno.h>
#include <fcntl.h>
#include <glob.h>
#include <linux/videodev2.h>
#include <signal.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <time.h>
#include <unistd.h>

#include <spa/param/video/format-utils.h>
#include <pipewire/pipewire.h>

#include "bayer10-convert.h"

#define DEFAULT_LEASE "/run/user/1000/lmi-snapshot/foreground.json"
#define DEFAULT_MEDIA "/dev/media0"
#define DEFAULT_WIDTH 1364
#define DEFAULT_HEIGHT 768
#define MAX_BUFFERS 4
#define TICK_NS 10000000LL
#define PROBE_SECONDS 3
#define PROBE_EXIT 3

/* The Bayer format of the sensor: MEDIA_BUS_FMT_SGRBG10_1X10. */
#define LMI_BUS_FMT_SGRBG10_1X10 0x300a
/* V4L2_PIX_FMT_SGRBG10P, the packed 10 bit form of that format. */
#define LMI_PIX_FMT_SGRBG10P 0x41416770

/* ---------------------------------------------------------------------------
 * The media controller of this kernel still exposes the older family of
 * ioctls, the one with a '|' type character. The structures are declared
 * here so that the producer does not depend on the version of the headers
 * of the machine that builds it.
 * ------------------------------------------------------------------------ */
#define LMI_IOC_NONE 0
#define LMI_IOC_WRITE 1
#define LMI_IOC_READ 2

#define LMI_IOC(direction, kind, number, size) \
	(((direction) << 30) | ((size) << 16) | ((kind) << 8) | (number))

struct lmi_media_device_info {
	char driver[16];
	char model[32];
	char serial[40];
	char bus_info[32];
	uint32_t media_version;
	uint32_t hw_revision;
	uint32_t driver_version;
	uint32_t reserved[31];
};

struct lmi_media_pad_desc {
	uint32_t entity;
	uint16_t index;
	uint32_t flags;
	uint32_t reserved[2];
};

struct lmi_media_entity_desc {
	uint32_t id;
	char name[32];
	uint32_t type;
	uint32_t revision;
	uint32_t flags;
	uint32_t group_id;
	uint16_t pads;
	uint16_t links;
	uint32_t reserved[4];
	struct {
		uint32_t major;
		uint32_t minor;
	} dev;
	uint8_t rest[176];
};

struct lmi_media_link_desc {
	struct lmi_media_pad_desc source;
	struct lmi_media_pad_desc sink;
	uint32_t flags;
	uint32_t reserved[2];
};

struct lmi_media_links_enum {
	uint32_t entity;
	struct lmi_media_pad_desc *pads;
	struct lmi_media_link_desc *links;
	uint32_t reserved[4];
};

#define MEDIA_IOC_DEVICE_INFO \
	LMI_IOC(LMI_IOC_READ | LMI_IOC_WRITE, '|', 0x00, sizeof(struct lmi_media_device_info))
#define MEDIA_IOC_ENUM_ENTITIES \
	LMI_IOC(LMI_IOC_READ | LMI_IOC_WRITE, '|', 0x01, sizeof(struct lmi_media_entity_desc))
#define MEDIA_IOC_ENUM_LINKS \
	LMI_IOC(LMI_IOC_READ | LMI_IOC_WRITE, '|', 0x02, sizeof(struct lmi_media_links_enum))
#define MEDIA_IOC_SETUP_LINK \
	LMI_IOC(LMI_IOC_READ | LMI_IOC_WRITE, '|', 0x03, sizeof(struct lmi_media_link_desc))

#define MEDIA_LNK_FL_ENABLED (1U << 0)
#define MEDIA_LNK_FL_IMMUTABLE (1U << 1)
#define MEDIA_PAD_FL_SINK (1U << 0)
#define MEDIA_PAD_FL_SOURCE (1U << 1)
#define MEDIA_ENTITY_TYPE_VIDEO_DEVICE 0x00010001
#define MEDIA_ENTITY_TYPE_SENSOR 0x00020001
#define MAX_LINKS 512

/* The format of a pad of a subdevice. */
struct lmi_subdev_format {
	uint32_t which;
	uint32_t pad;
	struct {
		uint32_t width;
		uint32_t height;
		uint32_t code;
		uint32_t field;
		uint32_t colorspace;
		uint16_t ycbcr_enc;
		uint16_t quantization;
		uint16_t xfer_func;
		uint16_t flags;
		uint16_t reserved[10];
	} format;
	uint32_t stream;
	uint32_t reserved[7];
};

#define VIDIOC_SUBDEV_G_FMT \
	LMI_IOC(LMI_IOC_READ | LMI_IOC_WRITE, 'V', 4, sizeof(struct lmi_subdev_format))
#define VIDIOC_SUBDEV_S_FMT \
	LMI_IOC(LMI_IOC_READ | LMI_IOC_WRITE, 'V', 5, sizeof(struct lmi_subdev_format))

#define V4L2_SUBDEV_FORMAT_ACTIVE 1

/* --------------------------------------------------------------------------- */

struct v4l2_map {
	void *start;
	size_t length;
};

struct chain {
	int sensor;
	int csiphy;
	int csid;
	int vfe;
	int video;
	struct lmi_media_link_desc csiphy_csid;
	struct lmi_media_link_desc csid_vfe;
	bool links_changed;
};

/* The formats that were active before the producer touched anything. */
struct saved_format {
	char path[64];
	struct lmi_subdev_format format;
	bool valid;
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
	int media_fd;
	struct chain chain;
	struct saved_format formats[8];
	unsigned format_count;
	struct v4l2_map maps[MAX_BUFFERS];
	unsigned map_count;
	unsigned char *frame;
	size_t frame_size;
	unsigned char *converted;
	uint32_t width;
	uint32_t height;
	uint32_t stride;
	uint32_t sizeimage;
	uint32_t bgrx_stride;
	enum lmi_bayer_phase phase;
	struct lmi_bayer_tuning tuning;
	bool tuning_ready;
	unsigned frames;
	unsigned drained;
	bool fresh;
	bool streaming;
};

static void log_line(const char *format, ...)
{
	va_list arguments;
	va_start(arguments, format);
	vfprintf(stderr, format, arguments);
	va_end(arguments);
	fputc('\n', stderr);
	fflush(stderr);
}

/* The foreground lease of the launcher. */
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

/* ---------------------------------------------------------------------------
 * The media controller.
 * ------------------------------------------------------------------------ */
/* The enumeration of the entities asks for the next one with this flag in
 * the identifier of the entity: the kernel answers with the entity and its
 * identifier, and an invalid argument means that there is no entity left. */
#define MEDIA_ENT_ID_FLAG_NEXT (1U << 31)

static int media_entities(int fd, struct lmi_media_entity_desc *entities,
			  unsigned capacity, unsigned *count)
{
	uint32_t ident = MEDIA_ENT_ID_FLAG_NEXT;
	unsigned index = 0;
	while (index < capacity) {
		struct lmi_media_entity_desc entity;
		memset(&entity, 0, sizeof(entity));
		entity.id = ident;
		if (ioctl(fd, MEDIA_IOC_ENUM_ENTITIES, &entity) < 0) {
			if (errno == EINVAL)
				break;
			return -1;
		}
		entities[index++] = entity;
		ident = entity.id | MEDIA_ENT_ID_FLAG_NEXT;
	}
	*count = index;
	return index ? 0 : -1;
}

/* The enumeration of the links of an entity.
 *
 * The kernel writes the pads and the links that start at the entity and
 * leaves the reserved fields of the request at zero: it does not report how
 * many of them there are. The numbers come from the description of the
 * entity, which counts every link that touches it. */
static int media_links(int fd, uint32_t entity, unsigned pads_expected,
		       unsigned links_expected, struct lmi_media_pad_desc *pads,
		       struct lmi_media_link_desc *links, unsigned *pad_count,
		       unsigned *link_count)
{
	if (pads_expected > 64 || links_expected > 64)
		return -1;
	struct lmi_media_links_enum request;
	memset(&request, 0, sizeof(request));
	request.entity = entity;
	request.pads = pads;
	request.links = links;
	if (ioctl(fd, MEDIA_IOC_ENUM_LINKS, &request) < 0)
		return -1;
	*pad_count = pads_expected;
	*link_count = links_expected;
	return 0;
}

static int set_link(int fd, const struct lmi_media_link_desc *link, bool enabled)
{
	struct lmi_media_link_desc request = *link;
	uint32_t flags = request.flags;
	flags &= ~MEDIA_LNK_FL_ENABLED;
	if (enabled)
		flags |= MEDIA_LNK_FL_ENABLED;
	request.flags = flags;
	return ioctl(fd, MEDIA_IOC_SETUP_LINK, &request);
}

/* The device node of a subdevice entity. */
static int subdev_path(uint32_t major, uint32_t minor, char *out, size_t size)
{
	glob_t paths;
	memset(&paths, 0, sizeof(paths));
	int found = -1;
	if (glob("/dev/v4l-subdev*", 0, NULL, &paths) == 0) {
		for (size_t i = 0; i < paths.gl_pathc; i++) {
			struct stat info;
			if (stat(paths.gl_pathv[i], &info) < 0)
				continue;
			if (!S_ISCHR(info.st_mode))
				continue;
			if (major(info.st_rdev) != major || minor(info.st_rdev) != minor)
				continue;
			if (found < 0) {
				snprintf(out, size, "%s", paths.gl_pathv[i]);
				found = 0;
			} else {
				found = -1;
				break;
			}
		}
	}
	globfree(&paths);
	return found;
}

/* The first pad of an entity that has the wanted direction. */
static int find_pad(const struct lmi_media_pad_desc *pads, unsigned count,
		    uint32_t flags)
{
	for (unsigned i = 0; i < count; i++)
		if (pads[i].flags & flags)
			return (int)pads[i].index;
	return -1;
}

/* Find the chain that leads from the rear sensor to a video node.
 *
 * The graph is walked from the sensor: the sensor feeds a CSIPHY, a CSIPHY
 * feeds a CSID, a CSID feeds a VFE RDI and a VFE RDI feeds the video node.
 * Only the two links in the middle are mutable; the link of the sensor and
 * the link of the video node are immutable and already enabled.
 */
/* Every link of the device, with the entity that owns it. The media
 * controller lists a link under the entity of its source pad, so the links
 * that end at an entity are not in the list of that entity: the chain has
 * to be built from all of them. */
struct link_index {
	struct lmi_media_link_desc link[MAX_LINKS];
	unsigned count;
};

static void collect_links(int media_fd, struct lmi_media_entity_desc *entities,
			   unsigned count, struct link_index *index)
{
	struct lmi_media_pad_desc pads[64];
	struct lmi_media_link_desc links[64];
	unsigned pad_count = 0, link_count = 0;
	index->count = 0;
	for (unsigned e = 0; e < count; e++) {
		if (media_links(media_fd, entities[e].id, entities[e].pads,
				entities[e].links, pads, links, &pad_count,
				&link_count) < 0)
			continue;
		for (unsigned l = 0; l < link_count && index->count < MAX_LINKS; l++)
			index->link[index->count++] = links[l];
	}
}

/* The entity that a link starts from, or -1. */
static int link_source(const struct link_index *index, uint32_t sink,
		       uint32_t exclude)
{
	for (unsigned i = 0; i < index->count; i++) {
		const struct lmi_media_link_desc *link = &index->link[i];
		if (link->sink.entity != sink)
			continue;
		if (link->source.entity == link->sink.entity)
			continue;
		if (link->source.entity == exclude)
			continue;
		return (int)link->source.entity;
	}
	return -1;
}

/* The entity that a link ends at, or -1. */
static int link_target(const struct link_index *index, uint32_t source)
{
	for (unsigned i = 0; i < index->count; i++) {
		const struct lmi_media_link_desc *link = &index->link[i];
		if (link->source.entity != source)
			continue;
		if (link->source.entity == link->sink.entity)
			continue;
		return (int)link->sink.entity;
	}
	return -1;
}

/* Find the chain that leads from the rear sensor to a video node.
 *
 * The graph is: the sensor feeds a CSIPHY, a CSIPHY feeds a CSID, a CSID
 * feeds a VFE RDI and a VFE RDI feeds the video node. Only the two links
 * in the middle are mutable; the link of the sensor and the link of the
 * video node are immutable and already enabled.
 */
/* The position of an entity in the array, from its identifier. The
 * identifiers of the entities are not their positions: one entity has the
 * identifier 1, the next 4, the next 7. */
static int entity_index(const struct lmi_media_entity_desc *entities,
			unsigned count, uint32_t id)
{
	for (unsigned i = 0; i < count; i++)
		if (entities[i].id == id)
			return (int)i;
	return -1;
}

/* Find the chain that leads from the rear sensor to a video node.
 *
 * The graph is: the sensor feeds a CSIPHY, a CSIPHY feeds a CSID, a CSID
 * feeds a VFE RDI and a VFE RDI feeds the video node. Only the two links
 * in the middle are mutable; the link of the sensor and the link of the
 * video node are immutable and already enabled.
 *
 * Every step of the walk is done with the identifiers of the entities.
 */
static int find_chain(int media_fd, const char *media_path,
		      struct lmi_media_entity_desc *entities, unsigned count,
		      struct chain *chain, char *device, size_t device_size)
{
	struct link_index index;
	collect_links(media_fd, entities, count, &index);

	/* The rear sensor: the entity of type sensor with a single pad. */
	int sensor = -1;
	for (unsigned i = 0; i < count; i++) {
		if (entities[i].type != MEDIA_ENTITY_TYPE_SENSOR)
			continue;
		if (entities[i].pads != 1)
			continue;
		sensor = (int)entities[i].id;
		break;
	}
	if (sensor < 0) {
		log_line("CHAIN_STEP no sensor entity");
		return -1;
	}
	log_line("CHAIN_STEP sensor=%s id=%d", entities[entity_index(entities, count, sensor)].name,
		 sensor);

	/* The CSIPHY of the sensor: the sensor is the source of the link. */
	int csiphy = link_target(&index, sensor);
	if (csiphy < 0) {
		log_line("CHAIN_STEP no csiphy for the sensor");
		return -1;
	}
	log_line("CHAIN_STEP csiphy=%s id=%d",
		 entities[entity_index(entities, count, csiphy)].name, csiphy);

	/* The video node: the entity of type video device whose node exists.
	 * The VFE RDI that feeds it is the source of the link that ends at
	 * the video entity. */
	int video = -1, vfe = -1;
	for (unsigned i = 0; i < count && video < 0; i++) {
		if (entities[i].type != MEDIA_ENTITY_TYPE_VIDEO_DEVICE)
			continue;
		char path[64];
		snprintf(path, sizeof(path), "/dev/video%u",
			 (unsigned)entities[i].dev.minor);
		if (access(path, F_OK) < 0)
			continue;
		int source = link_source(&index, entities[i].id, 0);
		if (source < 0)
			continue;
		video = (int)entities[i].id;
		vfe = source;
		snprintf(device, device_size, "%s", path);
	}
	if (video < 0 || vfe < 0) {
		log_line("CHAIN_STEP no video node (video=%d vfe=%d)", video, vfe);
		return -1;
	}
	log_line("CHAIN_STEP video=%s id=%d",
		 entities[entity_index(entities, count, video)].name, video);
	log_line("CHAIN_STEP vfe=%s id=%d",
		 entities[entity_index(entities, count, vfe)].name, vfe);

	/* The CSID that the VFE RDI takes its data from. */
	int csid = link_source(&index, vfe, 0);
	if (csid < 0) {
		log_line("CHAIN_STEP no csid for the vfe");
		return -1;
	}
	log_line("CHAIN_STEP csid=%s id=%d",
		 entities[entity_index(entities, count, csid)].name, csid);

	/* Every CSID of the device can be fed by every CSIPHY, so the CSIPHY
	 * of the sensor is not the only one that reaches the CSID: what
	 * matters is that the link between them exists, and that is checked
	 * with the two mutable links below. */
	if (link_source(&index, csid, 0) < 0) {
		log_line("CHAIN_STEP the csid has no incoming link");
		return -1;
	}

	/* The two mutable links. */
	bool have_csiphy_csid = false, have_csid_vfe = false;
	for (unsigned i = 0; i < index.count; i++) {
		const struct lmi_media_link_desc *link = &index.link[i];
		if (link->source.entity == (uint32_t)csiphy &&
		    link->sink.entity == (uint32_t)csid) {
			chain->csiphy_csid = *link;
			have_csiphy_csid = true;
		}
		if (link->source.entity == (uint32_t)csid &&
		    link->sink.entity == (uint32_t)vfe) {
			chain->csid_vfe = *link;
			have_csid_vfe = true;
		}
	}
	if (!have_csiphy_csid || !have_csid_vfe) {
		log_line("CHAIN_STEP missing links (csiphy-csid=%d csid-vfe=%d)",
			 have_csiphy_csid, have_csid_vfe);
		return -1;
	}

	chain->sensor = sensor;
	chain->csiphy = csiphy;
	chain->csid = csid;
	chain->vfe = vfe;
	chain->video = video;
	(void)media_path;
	return 0;
}

/* ---------------------------------------------------------------------------
 * The V4L2 side.
 * ------------------------------------------------------------------------ */
static int v4l2_open(const char *path, bool multiplane)
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
	uint32_t needed = multiplane ? V4L2_CAP_VIDEO_CAPTURE_MPLANE
				     : V4L2_CAP_VIDEO_CAPTURE;
	if (!(cap.capabilities & needed) || !(cap.capabilities & V4L2_CAP_STREAMING)) {
		close(fd);
		return -1;
	}
	return fd;
}

/* The formats that were active before the producer touched anything. */
static int save_formats(struct app *app,
			const struct lmi_media_entity_desc *entities, unsigned count)
{
	const uint32_t wanted[4] = {
		(uint32_t)app->chain.sensor, (uint32_t)app->chain.csiphy,
		(uint32_t)app->chain.csid, (uint32_t)app->chain.vfe
	};
	for (unsigned i = 0; i < 4; i++) {
		for (unsigned e = 0; e < count; e++) {
			if (entities[e].id != wanted[i])
				continue;
			char path[64];
			if (subdev_path(entities[e].dev.major, entities[e].dev.minor,
					path, sizeof(path)) < 0)
				break;
			int fd = open(path, O_RDWR | O_NONBLOCK);
			if (fd < 0)
				break;
			struct lmi_media_pad_desc pads[64];
			struct lmi_media_link_desc links[64];
			unsigned pad_count = 0, link_count = 0;
			if (media_links(app->media_fd, entities[e].id, entities[e].pads,
					entities[e].links, pads, links, &pad_count,
					&link_count) == 0) {
				for (unsigned p = 0; p < pad_count; p++) {
					struct lmi_subdev_format format;
					memset(&format, 0, sizeof(format));
					format.which = V4L2_SUBDEV_FORMAT_ACTIVE;
					format.pad = pads[p].index;
					if (ioctl(fd, VIDIOC_SUBDEV_G_FMT, &format) < 0)
						continue;
					if (app->format_count >= 8)
						break;
					struct saved_format *saved =
						&app->formats[app->format_count++];
					memset(saved, 0, sizeof(*saved));
					snprintf(saved->path, sizeof(saved->path), "%s",
						 path);
					saved->format = format;
					saved->valid = true;
				}
			}
			close(fd);
			break;
		}
	}
	return app->format_count ? 0 : -1;
}

/* Set the format of the sensor and of the three blocks of the chain. */
static int set_subdev_format(const char *path, int pad, uint32_t code,
			     uint32_t width, uint32_t height);

static void configure_chain(struct app *app,
			    const struct lmi_media_entity_desc *entities,
			    unsigned count)
{
	const uint32_t wanted[4] = {
		(uint32_t)app->chain.sensor, (uint32_t)app->chain.csiphy,
		(uint32_t)app->chain.csid, (uint32_t)app->chain.vfe
	};
	for (unsigned i = 0; i < 4; i++) {
		for (unsigned e = 0; e < count; e++) {
			if (entities[e].id != wanted[i])
				continue;
			char path[64];
			if (subdev_path(entities[e].dev.major, entities[e].dev.minor,
					path, sizeof(path)) < 0)
				break;
			struct lmi_media_pad_desc pads[64];
			struct lmi_media_link_desc links[64];
			unsigned pad_count = 0, link_count = 0;
			if (media_links(app->media_fd, entities[e].id, entities[e].pads,
					entities[e].links, pads, links, &pad_count,
					&link_count) < 0)
				break;
			/* The sensor is the provider of the chain, the other
			 * three blocks are the consumers of it. */
			int pad = -1;
			if (i == 0)
				pad = find_pad(pads, pad_count, MEDIA_PAD_FL_SOURCE);
			else
				pad = find_pad(pads, pad_count, MEDIA_PAD_FL_SINK);
			if (pad < 0)
				break;
			if (set_subdev_format(path, pad, LMI_BUS_FMT_SGRBG10_1X10,
					      app->width, app->height) < 0)
				log_line("SUBDEV_FORMAT_FAILED %s pad=%d", path, pad);
			else
				log_line("SUBDEV_FORMAT %s pad=%d %ux%u", path, pad,
					 app->width, app->height);
			break;
		}
	}
}

static int set_subdev_format(const char *path, int pad, uint32_t code,
			     uint32_t width, uint32_t height)
{
	int fd = open(path, O_RDWR);
	if (fd < 0)
		return -1;
	struct lmi_subdev_format format;
	memset(&format, 0, sizeof(format));
	format.which = V4L2_SUBDEV_FORMAT_ACTIVE;
	format.pad = (uint32_t)pad;
	format.format.code = code;
	format.format.width = width;
	format.format.height = height;
	int rc = ioctl(fd, VIDIOC_SUBDEV_S_FMT, &format);
	uint32_t got_code = format.format.code;
	uint32_t got_width = format.format.width;
	uint32_t got_height = format.format.height;
	close(fd);
	if (rc < 0)
		return -1;
	if (got_code != code || got_width != width || got_height != height)
		return -1;
	return 0;
}

static int restore_formats(struct app *app)
{
	int rc = 0;
	for (unsigned i = 0; i < app->format_count; i++) {
		if (!app->formats[i].valid)
			continue;
		int fd = open(app->formats[i].path, O_RDWR);
		if (fd < 0) {
			rc = -1;
			continue;
		}
		if (ioctl(fd, VIDIOC_SUBDEV_S_FMT, &app->formats[i].format) < 0)
			rc = -1;
		close(fd);
	}
	app->format_count = 0;
	return rc;
}

static int v4l2_configure(struct app *app, uint32_t width, uint32_t height)
{
	struct v4l2_format format;
	memset(&format, 0, sizeof(format));
	format.type = V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;
	format.fmt.pix_mp.width = width;
	format.fmt.pix_mp.height = height;
	format.fmt.pix_mp.pixelformat = LMI_PIX_FMT_SGRBG10P;
	format.fmt.pix_mp.field = V4L2_FIELD_NONE;
	format.fmt.pix_mp.num_planes = 1;
	if (ioctl(app->fd, VIDIOC_S_FMT, &format) < 0)
		return -1;
	if (format.fmt.pix_mp.pixelformat != LMI_PIX_FMT_SGRBG10P)
		return -1;
	if (format.fmt.pix_mp.num_planes != 1)
		return -1;
	app->width = format.fmt.pix_mp.width;
	app->height = format.fmt.pix_mp.height;
	app->stride = format.fmt.pix_mp.plane_fmt[0].bytesperline;
	app->sizeimage = format.fmt.pix_mp.plane_fmt[0].sizeimage;
	if (app->stride < (app->width * 10 + 7) / 8)
		return -1;
	if (app->sizeimage < app->stride * app->height)
		return -1;
	return 0;
}

static int v4l2_stream_on(struct app *app)
{
	struct v4l2_requestbuffers request;
	memset(&request, 0, sizeof(request));
	request.count = MAX_BUFFERS;
	request.type = V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;
	request.memory = V4L2_MEMORY_MMAP;
	if (ioctl(app->fd, VIDIOC_REQBUFS, &request) < 0)
		return -1;
	if (request.count < 1 || request.count > MAX_BUFFERS)
		return -1;
	app->map_count = request.count;
	for (unsigned i = 0; i < request.count; i++) {
		struct v4l2_plane planes[VIDEO_MAX_PLANES];
		memset(planes, 0, sizeof(planes));
		struct v4l2_buffer buffer;
		memset(&buffer, 0, sizeof(buffer));
		buffer.type = V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;
		buffer.memory = V4L2_MEMORY_MMAP;
		buffer.m.planes = planes;
		buffer.length = VIDEO_MAX_PLANES;
		buffer.index = i;
		if (ioctl(app->fd, VIDIOC_QUERYBUF, &buffer) < 0)
			return -1;
		void *start = mmap(NULL, planes[0].length, PROT_READ | PROT_WRITE,
				   MAP_SHARED, app->fd, planes[0].m.mem_offset);
		if (start == MAP_FAILED)
			return -1;
		app->maps[i].start = start;
		app->maps[i].length = planes[0].length;
	}
	for (unsigned i = 0; i < request.count; i++) {
		struct v4l2_plane planes[VIDEO_MAX_PLANES];
		memset(planes, 0, sizeof(planes));
		struct v4l2_buffer buffer;
		memset(&buffer, 0, sizeof(buffer));
		buffer.type = V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;
		buffer.memory = V4L2_MEMORY_MMAP;
		buffer.m.planes = planes;
		buffer.length = VIDEO_MAX_PLANES;
		buffer.index = i;
		if (ioctl(app->fd, VIDIOC_QBUF, &buffer) < 0)
			return -1;
	}
	int type = V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;
	if (ioctl(app->fd, VIDIOC_STREAMON, &type) < 0)
		return -1;
	app->streaming = true;
	return 0;
}

static void v4l2_stream_off(struct app *app)
{
	if (app->streaming) {
		int type = V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;
		ioctl(app->fd, VIDIOC_STREAMOFF, &type);
		app->streaming = false;
	}
	for (unsigned i = 0; i < app->map_count; i++)
		if (app->maps[i].start && app->maps[i].start != MAP_FAILED)
			munmap(app->maps[i].start, app->maps[i].length);
	app->map_count = 0;
}

/* Take one frame and convert it. */
static bool v4l2_take_frame(struct app *app)
{
	struct v4l2_plane planes[VIDEO_MAX_PLANES];
	memset(planes, 0, sizeof(planes));
	struct v4l2_buffer buffer;
	memset(&buffer, 0, sizeof(buffer));
	buffer.type = V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;
	buffer.memory = V4L2_MEMORY_MMAP;
	buffer.m.planes = planes;
	buffer.length = VIDEO_MAX_PLANES;
	if (ioctl(app->fd, VIDIOC_DQBUF, &buffer) < 0)
		return false;
	bool converted = false;
	if (buffer.index < app->map_count && app->maps[buffer.index].start) {
		size_t used = planes[0].bytesused;
		size_t offset = planes[0].data_offset;
		if (used > offset && used - offset >= app->stride * app->height) {
			if (used - offset > app->frame_size)
				used = app->frame_size + offset;
			memcpy(app->frame, (const uint8_t *)app->maps[buffer.index].start + offset,
			       used - offset);
			if (!app->tuning_ready) {
				if (lmi_bayer_analyse(app->frame, app->frame_size,
						      app->width, app->height, app->stride,
						      app->phase, &app->tuning) == 0) {
					app->tuning_ready = true;
					log_line("BAYER_TUNING black=%d/%d/%d span=%d/%d/%d gain=%.2f/%.2f/%.2f",
						 app->tuning.black[0], app->tuning.black[1],
						 app->tuning.black[2], app->tuning.span[0],
						 app->tuning.span[1], app->tuning.span[2],
						 app->tuning.gain[0], app->tuning.gain[1],
						 app->tuning.gain[2]);
				}
			}
			if (app->tuning_ready) {
				converted = lmi_bayer_convert(app->frame, app->frame_size,
							       app->width, app->height,
							       app->stride, app->phase,
							       &app->tuning, app->converted,
							       app->bgrx_stride) == 0;
			}
		}
	}
	ioctl(app->fd, VIDIOC_QBUF, &buffer);
	app->drained++;
	return converted;
}

/* ---------------------------------------------------------------------------
 * The PipeWire side.
 * ------------------------------------------------------------------------ */
static void quit(void *opaque, uint64_t expirations)
{
	(void)expirations;
	struct app *app = opaque;
	pw_main_loop_quit(app->loop);
}

static void interrupted(void *opaque, int sig)
{
	(void)sig;
	struct app *app = opaque;
	pw_main_loop_quit(app->loop);
}

static void state(void *opaque, enum pw_stream_state old, enum pw_stream_state now,
		  const char *error)
{
	(void)old;
	struct app *app = opaque;
	log_line("STATE %s %s", pw_stream_state_as_string(now), error ? error : "");
	if (now == PW_STREAM_STATE_ERROR) {
		pw_main_loop_quit(app->loop);
		return;
	}
	if (now == PW_STREAM_STATE_STREAMING) {
		struct timespec first = { 0, 1 };
		struct timespec period = { 0, TICK_NS };
		pw_loop_update_timer(pw_main_loop_get_loop(app->loop), app->tick, &first,
				     &period, false);
	} else {
		pw_loop_update_timer(pw_main_loop_get_loop(app->loop), app->tick, NULL, NULL,
				     false);
	}
}

static void format_changed(void *opaque, uint32_t id, const struct spa_pod *param)
{
	struct app *app = opaque;
	if (id != SPA_PARAM_Format || !param)
		return;
	struct spa_video_info_raw proposed;
	memset(&proposed, 0, sizeof(proposed));
	if (spa_format_video_raw_parse(param, &proposed) < 0 ||
	    proposed.format != SPA_VIDEO_FORMAT_BGRx ||
	    proposed.size.width != app->width || proposed.size.height != app->height) {
		pw_stream_set_error(app->stream, -EINVAL,
				    "Expected BGRx %ux%u from the camera",
				    app->width, app->height);
		return;
	}
	app->format = proposed;
	uint8_t storage[512];
	struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(storage, sizeof(storage));
	const struct spa_pod *params[2];
	params[0] = spa_pod_builder_add_object(&builder, SPA_TYPE_OBJECT_ParamBuffers,
					       SPA_PARAM_Buffers,
					       SPA_PARAM_BUFFERS_buffers,
					       SPA_POD_CHOICE_RANGE_Int(8, 2, 16),
					       SPA_PARAM_BUFFERS_blocks, SPA_POD_Int(1),
					       SPA_PARAM_BUFFERS_size,
					       SPA_POD_Int((int)app->bgrx_stride * app->height),
					       SPA_PARAM_BUFFERS_stride,
					       SPA_POD_Int((int)app->bgrx_stride));
	params[1] = spa_pod_builder_add_object(&builder, SPA_TYPE_OBJECT_ParamMeta,
					       SPA_PARAM_Meta, SPA_PARAM_META_type,
					       SPA_POD_Id(SPA_META_Header),
					       SPA_PARAM_META_size,
					       SPA_POD_Int(sizeof(struct spa_meta_header)));
	pw_stream_update_params(app->stream, params, 2);
}

static void process(void *opaque)
{
	struct app *app = opaque;
	if (!app->fresh)
		return;
	struct pw_buffer *buffer = pw_stream_dequeue_buffer(app->stream);
	if (!buffer)
		return;
	app->fresh = false;
	struct spa_buffer *data = buffer->buffer;
	size_t size = (size_t)app->bgrx_stride * app->height;
	if (!data->n_datas || !data->datas[0].data || !data->datas[0].chunk ||
	    data->datas[0].maxsize < size) {
		pw_stream_queue_buffer(app->stream, buffer);
		return;
	}
	memcpy(data->datas[0].data, app->converted, size);
	struct spa_meta_header *head =
		spa_buffer_find_meta_data(data, SPA_META_Header, sizeof(*head));
	if (head) {
		head->pts = -1;
		head->flags = 0;
		head->seq = app->frames;
		head->dts_offset = 0;
	}
	data->datas[0].chunk->offset = 0;
	data->datas[0].chunk->size = size;
	data->datas[0].chunk->stride = app->bgrx_stride;
	data->datas[0].chunk->flags = 0;
	buffer->size = 1;
	app->frames++;
	pw_stream_queue_buffer(app->stream, buffer);
}

static const struct pw_stream_events events = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = state,
	.param_changed = format_changed,
	.process = process,
};

static void tick(void *opaque, uint64_t expirations)
{
	(void)expirations;
	struct app *app = opaque;
	if (v4l2_take_frame(app)) {
		app->fresh = true;
		pw_stream_trigger_process(app->stream);
	}
}

/* The lease keeps the camera honest: the node is only streamed while the
 * camera application is in the foreground. */
static void lease_tick(void *opaque, uint64_t expirations)
{
	(void)expirations;
	struct app *app = opaque;
	pid_t lease_pid = 0;
	int state_value = lease_state(app->lease_path, &lease_pid);
	if (state_value < 0) {
		log_line("V4L2_LEASE_GONE");
		pw_main_loop_quit(app->loop);
		return;
	}
	if (state_value == 1 && lease_pid != getpid() && lease_pid != getppid()) {
		log_line("V4L2_LEASE_OTHER");
		pw_main_loop_quit(app->loop);
		return;
	}
	if (state_value == 1 && !app->streaming) {
		if (v4l2_stream_on(app) == 0)
			log_line("V4L2_RESUMED");
	} else if (state_value == 0 && app->streaming) {
		v4l2_stream_off(app);
		log_line("V4L2_PAUSED");
	}
}

static double now_seconds(void)
{
	struct timespec now;
	clock_gettime(CLOCK_MONOTONIC, &now);
	return now.tv_sec + now.tv_nsec / 1e9;
}

/* Put the chain back the way it was. */
static void restore_chain(struct app *app)
{
	if (app->chain.links_changed) {
		if (set_link(app->media_fd, &app->chain.csid_vfe, false) < 0)
			log_line("RESTORE_LINK_FAILED csid-vfe");
		if (set_link(app->media_fd, &app->chain.csiphy_csid, false) < 0)
			log_line("RESTORE_LINK_FAILED csiphy-csid");
		app->chain.links_changed = false;
	}
	restore_formats(app);
}

int main(int argc, char **argv)
{
	if (argc < 1 || argc > 4) {
		fprintf(stderr,
			"Usage: native-pipewire-v4l2-bayer-source [DEVICE|auto] [SECONDS:0..3600] [LEASE]\n"
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

	struct app app;
	memset(&app, 0, sizeof(app));
	app.lease_path = lease;
	app.phase = LMI_BAYER_GRBG;

	app.media_fd = open(DEFAULT_MEDIA, O_RDWR | O_NONBLOCK | O_CLOEXEC);
	if (app.media_fd < 0) {
		log_line("MEDIA_OPEN_FAILED %s", DEFAULT_MEDIA);
		return 1;
	}
	struct lmi_media_entity_desc entities[256];
	unsigned count = 0;
	if (media_entities(app.media_fd, entities, 256, &count) < 0) {
		log_line("MEDIA_ENUM_FAILED");
		close(app.media_fd);
		return 1;
	}
	log_line("MEDIA %s entities=%u", DEFAULT_MEDIA, count);
	if (find_chain(app.media_fd, DEFAULT_MEDIA, entities, count, &app.chain,
		       device, sizeof(device)) < 0) {
		log_line("CHAIN_NOT_FOUND");
		close(app.media_fd);
		return PROBE_EXIT;
	}
	log_line("CHAIN sensor=%s csiphy=%s csid=%s vfe=%s video=%s",
		 entities[entity_index(entities, count, app.chain.sensor)].name,
		 entities[entity_index(entities, count, app.chain.csiphy)].name,
		 entities[entity_index(entities, count, app.chain.csid)].name,
		 entities[entity_index(entities, count, app.chain.vfe)].name,
		 entities[entity_index(entities, count, app.chain.video)].name);

	app.fd = v4l2_open(device, true);
	if (app.fd < 0) {
		log_line("V4L2_OPEN_FAILED %s", device);
		close(app.media_fd);
		return 1;
	}
	if (save_formats(&app, entities, count) < 0)
		log_line("NO_FORMAT_SAVED");
	if (v4l2_configure(&app, DEFAULT_WIDTH, DEFAULT_HEIGHT) < 0) {
		log_line("V4L2_CONFIGURE_FAILED %s", device);
		close(app.fd);
		close(app.media_fd);
		return 1;
	}
	log_line("V4L2_FORMAT %ux%u stride=%u sizeimage=%u", app.width, app.height,
		 app.stride, app.sizeimage);

	app.frame_size = (size_t)app.stride * app.height;
	app.frame = malloc(app.frame_size);
	app.bgrx_stride = app.width * 4;
	app.converted = malloc((size_t)app.bgrx_stride * app.height);
	if (!app.frame || !app.converted) {
		log_line("OUT_OF_MEMORY");
		free(app.frame);
		free(app.converted);
		close(app.fd);
		close(app.media_fd);
		return 1;
	}

	/* The two links that the driver leaves disabled, and the formats of
	 * the chain. */
	if (set_link(app.media_fd, &app.chain.csiphy_csid, true) < 0 ||
	    set_link(app.media_fd, &app.chain.csid_vfe, true) < 0) {
		log_line("LINK_ENABLE_FAILED");
		free(app.frame);
		free(app.converted);
		close(app.fd);
		close(app.media_fd);
		return 1;
	}
	app.chain.links_changed = true;

	configure_chain(&app, entities, count);
	if (v4l2_stream_on(&app) < 0) {
		log_line("V4L2_STREAM_FAILED %s", device);
		restore_chain(&app);
		free(app.frame);
		free(app.converted);
		close(app.fd);
		close(app.media_fd);
		return 1;
	}
	double deadline = now_seconds() + PROBE_SECONDS;
	bool got = false;
	while (now_seconds() < deadline && !got) {
		got = v4l2_take_frame(&app);
		if (!got) {
			struct timespec pause = { 0, 20000000 };
			nanosleep(&pause, NULL);
		}
	}
	if (!got) {
		log_line("V4L2_NO_FRAME %s", device);
		v4l2_stream_off(&app);
		restore_chain(&app);
		free(app.frame);
		free(app.converted);
		close(app.fd);
		close(app.media_fd);
		return PROBE_EXIT;
	}
	printf("V4L2_SOURCE_READY %s %ux%u\n", device, app.width, app.height);
	fflush(stdout);

	pw_init(&argc, &argv);
	app.loop = pw_main_loop_new(NULL);
	if (!app.loop) {
		v4l2_stream_off(&app);
		restore_chain(&app);
		free(app.frame);
		free(app.converted);
		close(app.fd);
		close(app.media_fd);
		return 1;
	}
	struct pw_loop *loop = pw_main_loop_get_loop(app.loop);
	pw_loop_add_signal(loop, SIGINT, interrupted, &app);
	pw_loop_add_signal(loop, SIGTERM, interrupted, &app);
	app.context = pw_context_new(loop, NULL, 0);
	app.core = pw_context_connect(app.context, NULL, 0);
	if (!app.core) {
		log_line("No user PipeWire core");
		v4l2_stream_off(&app);
		restore_chain(&app);
		free(app.frame);
		free(app.converted);
		close(app.fd);
		close(app.media_fd);
		return 1;
	}
	app.tick = pw_loop_add_timer(loop, tick, &app);
	if (seconds > 0) {
		struct spa_source *expiry = pw_loop_add_timer(loop, quit, &app);
		struct timespec limit = { seconds, 0 };
		pw_loop_update_timer(loop, expiry, &limit, NULL, false);
	}

	char description[128];
	snprintf(description, sizeof(description), "LMI rear camera (V4L2 %s)", device);
	app.stream = pw_stream_new(app.core, "LMI V4L2 rear camera source",
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
	if (!app.stream) {
		log_line("Cannot create the PipeWire stream");
		v4l2_stream_off(&app);
		restore_chain(&app);
		free(app.frame);
		free(app.converted);
		close(app.fd);
		close(app.media_fd);
		return 1;
	}
	pw_stream_add_listener(app.stream, &app.listener, &events, &app);

	uint8_t storage[512];
	struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(storage, sizeof(storage));
	const struct spa_pod *param = spa_pod_builder_add_object(
		&builder, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat,
		SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
		SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
		SPA_FORMAT_VIDEO_format, SPA_POD_Id(SPA_VIDEO_FORMAT_BGRx),
		SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&SPA_RECTANGLE(app.width, app.height)),
		SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&SPA_FRACTION(30, 1)));
	int rc = pw_stream_connect(app.stream, PW_DIRECTION_OUTPUT, PW_ID_ANY,
				    PW_STREAM_FLAG_DRIVER | PW_STREAM_FLAG_MAP_BUFFERS,
				    &param, 1);
	if (rc < 0) {
		log_line("Cannot connect the PipeWire stream: %s", strerror(-rc));
		v4l2_stream_off(&app);
		restore_chain(&app);
		free(app.frame);
		free(app.converted);
		close(app.fd);
		close(app.media_fd);
		return 1;
	}

	struct spa_source *lease_timer = pw_loop_add_timer(loop, lease_tick, &app);
	struct timespec lease_period = { 0, 250000000 };
	pw_loop_update_timer(loop, lease_timer, NULL, &lease_period, false);
	pw_main_loop_run(app.loop);

	log_line("FRAMES %u DRAINED %u", app.frames, app.drained);
	v4l2_stream_off(&app);
	restore_chain(&app);
	pw_stream_destroy(app.stream);
	pw_core_disconnect(app.core);
	pw_context_destroy(app.context);
	pw_main_loop_destroy(app.loop);
	pw_deinit();
	free(app.frame);
	free(app.converted);
	close(app.fd);
	close(app.media_fd);
	return 0;
}
