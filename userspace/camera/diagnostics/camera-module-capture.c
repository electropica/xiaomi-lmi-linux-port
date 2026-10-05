/*
 * Bounded HAL3 JPEG / rear YUV diagnostic using actual OEM QTI buffers.
 * Earlier frames condition 3A; only the last frame is saved.
 * Output /data/vendor/camera/test.jpg must resolve inside the private runtime.
 * Requires an external process timeout: vendor configure/flush/close calls can
 * block despite this client's bounded result and release-fence waits.
 * Reuses the verified AOSP module ABI and stable callback tables in the enum
 * source. Camera3 ABI provenance (Apache License 2.0, AOSP):
 * https://android.googlesource.com/platform/hardware/libhardware/+/android16-release/include_all/hardware/camera3.h
 * https://source.android.com/reference/hal/structcamera3__device__ops
 * Run in the private bionic runtime, with the same property/runtime setup as
 * enumeration and an external timeout. Never run alongside the OEM provider.
 * Usage: camera-module-capture CAMERA_ID [camera.qcom.so path] [--configure] [--manual-exposure | --ae-precapture | --preview | --preview-sequence | --preview-live | --preview-pipeline]
 */
#define main enumeration_diagnostic_main
#include "camera-module-enumerate.c"
#undef main
#include <camera/NdkCameraMetadataTags.h>
#include <android/data_space.h>
#include <pthread.h>
#include <time.h>
#include <poll.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>

extern int lmi_qti_allocate(uint32_t bytes, uint64_t usage, const void **handle);
extern int lmi_qti_allocate_yuv(uint32_t,uint32_t,uint64_t,const void **);
extern int lmi_qti_save_ppm(const void *,uint32_t,uint32_t,const char *);
extern int lmi_qti_release(const void *handle);
extern int lmi_qti_lock_cpu(const void *handle, void **address);
extern int lmi_qti_unlock(const void *handle);
static const void *capture_handle;
static struct camera_metadata *manual_settings;
static void (*free_metadata)(struct camera_metadata *);

/* Public metadata ABI and tags:
 * https://android.googlesource.com/platform/system/media/+/refs/heads/main/camera/include/system/camera_metadata.h
 * https://android.googlesource.com/platform/system/media/+/refs/heads/master/camera/include/system/camera_metadata_tags.h
 * ANDROID_JPEG_MAX_SIZE is a system tag omitted from public NDK enums. Its
 * stable position is JPEG section (7) + offset8, verified in AOSP tag header. */
#define PROBE_ANDROID_JPEG_MAX_SIZE ((uint32_t)ACAMERA_JPEG_START + 8)
_Static_assert(PROBE_ANDROID_JPEG_MAX_SIZE == 0x00070008, "AOSP JPEG maxSize tag");
_Static_assert(ACAMERA_SCALER_AVAILABLE_STREAM_CONFIGURATIONS == 0x000d000a,
               "AOSP stream configurations tag");
typedef struct camera_metadata_rational { int32_t numerator; int32_t denominator; } camera_metadata_rational_t;
typedef struct camera_metadata_ro_entry {
    size_t index;
    uint32_t tag;
    uint8_t type;
    size_t count;
    union {
        const uint8_t *u8; const int32_t *i32; const float *f;
        const int64_t *i64; const double *d; const camera_metadata_rational_t *r;
    } data;
} camera_metadata_ro_entry_t;
typedef int (*find_metadata_fn)(const struct camera_metadata *, uint32_t,
                                camera_metadata_ro_entry_t *);

typedef struct hw_module_methods_t {
    int (*open)(const hw_module_t *module, const char *id,
                struct hw_device_t **device);
} hw_module_methods_t;
typedef struct hw_device_t {
    uint32_t tag;
    uint32_t version;
    hw_module_t *module;
#ifdef __LP64__
    uint64_t reserved[12];
#else
    uint32_t reserved[12];
#endif
    int (*close)(struct hw_device_t *device);
} hw_device_t;
struct camera3_device;
struct camera3_callback_ops;
struct camera3_stream_configuration;
struct camera3_stream_buffer_set;
struct camera3_stream;
struct camera3_stream_buffer;
struct camera3_buffer_request;
struct camera3_stream_buffer_ret;
/* Native HAL3.5 stream has no buffer_size member: JPEG capacity belongs to
 * allocation. HIDL stream.bufferSize must not be appended to this C ABI. */
typedef struct camera3_stream {
    int stream_type;
    uint32_t width;
    uint32_t height;
    int format;
    uint32_t usage;
    uint32_t max_buffers;
    void *priv;
    int data_space;
    int rotation;
    const char *physical_camera_id;
    void *reserved[6];
} camera3_stream_t;
typedef struct camera3_stream_configuration {
    uint32_t num_streams;
    camera3_stream_t **streams;
    uint32_t operation_mode;
    const struct camera_metadata *session_parameters;
} camera3_stream_configuration_t;
static int preview_mode;
static camera3_stream_t probe_blob_stream;
static camera3_stream_t *probe_streams[] = { &probe_blob_stream };
static camera3_stream_configuration_t probe_configuration;
/* Exact HAL3.5 stream-buffer/request layouts. Handles remain opaque; the
 * pointer-to-handle storage and request are stable for the full session. */
typedef struct camera3_stream_buffer {
    camera3_stream_t *stream;
    const void **buffer;
    int status;
    int acquire_fence;
    int release_fence;
} camera3_stream_buffer_t;
typedef struct camera3_capture_request {
    uint32_t frame_number;
    const struct camera_metadata *settings;
    camera3_stream_buffer_t *input_buffer;
    uint32_t num_output_buffers;
    const camera3_stream_buffer_t *output_buffers;
    uint32_t num_physcam_settings;
    const char **physcam_id;
    const struct camera_metadata **physcam_settings;
} camera3_capture_request_t;
enum { PIPELINE_SLOTS=3 };
static int preview_pipeline, preview_foreground;
struct pipeline_slot {
    const void *handle;
    camera3_stream_buffer_t output;
    camera3_capture_request_t request;
    uint32_t frame;
    int received,error,status,fence;
};
static struct pipeline_slot pipeline[PIPELINE_SLOTS];
static camera3_stream_buffer_t capture_output;
static camera3_capture_request_t capture_request;
static pthread_mutex_t capture_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t capture_cond = PTHREAD_COND_INITIALIZER;
static int capture_received, capture_error, capture_status, capture_release_fence = -1;
static uint32_t capture_expected_frame;
typedef struct camera3_capture_result {
    uint32_t frame_number;
    const struct camera_metadata *result;
    uint32_t num_output_buffers;
    const struct camera3_stream_buffer *output_buffers;
    const struct camera3_stream_buffer *input_buffer;
    uint32_t partial_result;
    uint32_t num_physcam_metadata;
    const char **physcam_ids;
    const struct camera_metadata **physcam_metadata;
} camera3_capture_result_t;
typedef struct camera3_error_msg {
    uint32_t frame_number;
    struct camera3_stream *error_stream;
    int error_code;
} camera3_error_msg_t;
typedef struct camera3_shutter_msg {
    uint32_t frame_number;
    uint64_t timestamp;
} camera3_shutter_msg_t;
typedef struct camera3_notify_msg {
    int type;
    union {
        camera3_error_msg_t error;
        camera3_shutter_msg_t shutter;
        uint8_t generic[32];
    } message;
} camera3_notify_msg_t;
typedef enum camera3_buffer_request_status {
    CAMERA3_BUF_REQ_OK = 0,
    CAMERA3_BUF_REQ_FAILED_PARTIAL = 1,
    CAMERA3_BUF_REQ_FAILED_CONFIGURING = 2,
    CAMERA3_BUF_REQ_FAILED_ILLEGAL_ARGUMENTS = 3,
    CAMERA3_BUF_REQ_FAILED_UNKNOWN = 4,
    CAMERA3_BUF_REQ_NUM_STATUS
} camera3_buffer_request_status_t;
typedef struct camera3_callback_ops {
    void (*process_capture_result)(const struct camera3_callback_ops *,
                                   const camera3_capture_result_t *);
    void (*notify)(const struct camera3_callback_ops *, const camera3_notify_msg_t *);
    camera3_buffer_request_status_t (*request_stream_buffers)(
        const struct camera3_callback_ops *, uint32_t,
        const struct camera3_buffer_request *, uint32_t *,
        struct camera3_stream_buffer_ret *);
    void (*return_stream_buffers)(const struct camera3_callback_ops *, uint32_t,
                                  const struct camera3_stream_buffer *const *);
} camera3_callback_ops_t;
static find_metadata_fn result_find_entry;
static void prepare_result_callback(const camera3_callback_ops_t *cb,
                                     const camera3_capture_result_t *result) {
    (void)cb;
    if (result && result->result && result_find_entry) {
        camera_metadata_ro_entry_t e = {0};
        if (!result_find_entry(result->result, ACAMERA_CONTROL_AE_STATE, &e) && e.type == 0 && e.count == 1)
            printf("ae_state frame=%u value=%u\n", result->frame_number, e.data.u8[0]);
        if (!result_find_entry(result->result, ACAMERA_SENSOR_EXPOSURE_TIME, &e) && e.type == 3 && e.count == 1)
            printf("exposure_ns frame=%u value=%lld\n", result->frame_number, (long long)e.data.i64[0]);
        if (!result_find_entry(result->result, ACAMERA_SENSOR_SENSITIVITY, &e) && e.type == 1 && e.count == 1)
            printf("sensitivity_iso frame=%u value=%d\n", result->frame_number, e.data.i32[0]);
    }
    if (result) printf("callback=capture_result frame=%u output_buffers=%u partial=%u\n",
                       result->frame_number, result->num_output_buffers, result->partial_result);
    if (!result || !result->output_buffers || result->num_output_buffers > 16)
        return;
    pthread_mutex_lock(&capture_mutex);
    if (preview_pipeline) {
        for (unsigned slot=0;slot<PIPELINE_SLOTS;slot++) {
            struct pipeline_slot *p=&pipeline[slot];
            if (p->frame!=result->frame_number)continue;
            for (uint32_t i=0;i<result->num_output_buffers;i++) {
                const camera3_stream_buffer_t *buffer=result->output_buffers+i;
                if (buffer->stream!=&probe_blob_stream)continue;
                if (!p->received) {
                    p->received=1;p->status=buffer->status;p->fence=buffer->release_fence;
                    if (!buffer->buffer || *buffer->buffer!=p->handle)p->error=1;
                }
            }
        }
        pthread_cond_broadcast(&capture_cond);
        pthread_mutex_unlock(&capture_mutex);
        return;
    }
    if (result->frame_number != capture_expected_frame) {
        pthread_mutex_unlock(&capture_mutex);
        return;
    }
    for (uint32_t i = 0; i < result->num_output_buffers; ++i) {
        const camera3_stream_buffer_t *buffer = result->output_buffers + i;
        if (buffer->stream != &probe_blob_stream) continue;
        if (!capture_received) {
            capture_received = 1;
            capture_status = buffer->status;
            capture_release_fence = buffer->release_fence;
        }
    }
    pthread_cond_broadcast(&capture_cond);
    pthread_mutex_unlock(&capture_mutex);
}
static void prepare_notify_callback(const camera3_callback_ops_t *cb,
                                     const camera3_notify_msg_t *msg) {
    (void)cb;
    if (!msg) return;
    printf("callback=notify type=%d\n", msg->type);
    if (msg->type == 1) printf("notify_error frame=%u code=%d\n",
                               msg->message.error.frame_number, msg->message.error.error_code);
    if (msg->type == 1) {
        pthread_mutex_lock(&capture_mutex);
        if (preview_pipeline) {
            for (unsigned slot=0;slot<PIPELINE_SLOTS;slot++)
                if (pipeline[slot].frame==msg->message.error.frame_number || msg->message.error.error_code==1)
                    pipeline[slot].error=1;
            pthread_cond_broadcast(&capture_cond);
        }
        if (msg->message.error.frame_number == capture_expected_frame || msg->message.error.error_code == 1) {
            capture_error = 1;
            pthread_cond_broadcast(&capture_cond);
        }
        pthread_mutex_unlock(&capture_mutex);
    }
}
/* Exact modern table, with trailing optional callbacks NULL as required for
 * CAMERA_DEVICE_API_VERSION <= 3.5. No captures/streams means no buffer callback. */
static const camera3_callback_ops_t prepare_callbacks = {
    .process_capture_result = prepare_result_callback,
    .notify = prepare_notify_callback,
    .request_stream_buffers = NULL,
    .return_stream_buffers = NULL
};
typedef struct camera3_device_ops_prefix {
    int (*initialize)(const struct camera3_device *,
                      const struct camera3_callback_ops *);
    int (*configure_streams)(const struct camera3_device *,
                             struct camera3_stream_configuration *);
    int (*register_stream_buffers)(const struct camera3_device *,
                                   const struct camera3_stream_buffer_set *);
    const struct camera_metadata *(*construct_default_request_settings)(
        const struct camera3_device *, int type);
    int (*process_capture_request)(const struct camera3_device *, camera3_capture_request_t *);
    void (*get_metadata_vendor_tag_ops)(const struct camera3_device *, void *);
    void (*dump)(const struct camera3_device *, int);
    int (*flush)(const struct camera3_device *);
} camera3_device_ops_prefix_t;
typedef struct camera3_device {
    hw_device_t common;
    camera3_device_ops_prefix_t *ops;
    void *priv;
} camera3_device_t;
#ifdef __LP64__
_Static_assert(sizeof(hw_device_t) == 120, "AOSP LP64 device ABI");
_Static_assert(offsetof(camera3_device_t, ops) == 120, "AOSP LP64 camera ops ABI");
_Static_assert(offsetof(camera3_device_ops_prefix_t, construct_default_request_settings) == 24,
               "AOSP LP64 default settings ABI");
_Static_assert(sizeof(camera3_capture_result_t) == 64, "AOSP LP64 capture result ABI");
_Static_assert(sizeof(camera3_notify_msg_t) == 40, "AOSP LP64 notify ABI");
_Static_assert(sizeof(camera3_callback_ops_t) == 32, "AOSP LP64 callbacks ABI");
_Static_assert(sizeof(camera_metadata_ro_entry_t) == 32, "AOSP LP64 metadata entry ABI");
_Static_assert(sizeof(camera3_stream_t) == 96, "AOSP LP64 HAL3.5 stream ABI");
_Static_assert(offsetof(camera3_stream_t, physical_camera_id) == 40, "AOSP LP64 physical camera id ABI");
_Static_assert(sizeof(camera3_stream_configuration_t) == 32, "AOSP LP64 stream configuration ABI");
_Static_assert(sizeof(camera3_stream_buffer_t) == 32, "AOSP LP64 stream buffer ABI");
_Static_assert(sizeof(camera3_capture_request_t) == 64, "AOSP LP64 request ABI");
_Static_assert(offsetof(camera3_device_ops_prefix_t, process_capture_request) == 32, "AOSP request operation ABI");
_Static_assert(offsetof(camera3_device_ops_prefix_t, flush) == 56, "AOSP flush operation ABI");
#else
_Static_assert(sizeof(hw_device_t) == 64, "AOSP ILP32 device ABI");
_Static_assert(offsetof(camera3_device_t, ops) == 64, "AOSP ILP32 camera ops ABI");
#endif


/* Mutable copy only; the HAL owns immutable default request metadata.
 * AOSP camera_metadata.h allocation/append/update ABI. */
struct camera_metadata_entry;
static int prepare_manual_settings(void *library, const struct camera_metadata *defaults,
                                   const struct camera_metadata *characteristics) {
    struct camera_metadata *(*allocate)(size_t,size_t) = dlsym(library,"allocate_camera_metadata");
    size_t (*entries)(const struct camera_metadata *) = dlsym(library,"get_camera_metadata_entry_count");
    size_t (*bytes)(const struct camera_metadata *) = dlsym(library,"get_camera_metadata_data_count");
    int (*append)(struct camera_metadata *,const struct camera_metadata *) = dlsym(library,"append_camera_metadata");
    int (*add)(struct camera_metadata *,uint32_t,const void *,size_t) = dlsym(library,"add_camera_metadata_entry");
    int (*update)(struct camera_metadata *,size_t,const void *,size_t,struct camera_metadata_entry *) = dlsym(library,"update_camera_metadata_entry");
    int (*validate)(const struct camera_metadata *,const size_t *) = dlsym(library,"validate_camera_metadata_structure");
    free_metadata = dlsym(library,"free_camera_metadata");
    if (!allocate || !entries || !bytes || !append || !add || !update || !validate || !free_metadata || !defaults)
        return 42;
    camera_metadata_ro_entry_t e = {0};
    if (result_find_entry(characteristics,ACAMERA_REQUEST_AVAILABLE_CAPABILITIES,&e) || e.type!=0 || e.count>256) return 43;
    bool supported=false;
    for (size_t i=0;i<e.count;i++) if(e.data.u8[i]==ACAMERA_REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR) supported=true;
    if (!supported) return 43;
    const int64_t exposure=50000000, duration=66666667;
    const int32_t sensitivity=800;
    if(result_find_entry(characteristics,ACAMERA_SENSOR_INFO_EXPOSURE_TIME_RANGE,&e) || e.type!=3 || e.count!=2 || exposure<e.data.i64[0] || exposure>e.data.i64[1])return 43;
    if(result_find_entry(characteristics,ACAMERA_SENSOR_INFO_SENSITIVITY_RANGE,&e) || e.type!=1 || e.count!=2 || sensitivity<e.data.i32[0] || sensitivity>e.data.i32[1])return 43;
    if(result_find_entry(characteristics,ACAMERA_SENSOR_INFO_MAX_FRAME_DURATION,&e) || e.type!=3 || e.count!=1 || duration>e.data.i64[0])return 43;
    const uint8_t ae=ACAMERA_CONTROL_AE_MODE_OFF;
    const uint32_t tags[]={ACAMERA_CONTROL_AE_MODE,ACAMERA_SENSOR_EXPOSURE_TIME,ACAMERA_SENSOR_SENSITIVITY,ACAMERA_SENSOR_FRAME_DURATION};
    const void *values[]={&ae,&exposure,&sensitivity,&duration};
    if(result_find_entry(characteristics,ACAMERA_REQUEST_AVAILABLE_REQUEST_KEYS,&e) || e.type!=1 || e.count>16384)return 43;
    for(size_t j=0;j<4;j++) {
        bool present=false;
        for(size_t i=0;i<e.count;i++)if((uint32_t)e.data.i32[i]==tags[j])present=true;
        if(!present)return 43;
    }
    if(validate(defaults,NULL))return 44;
    size_t count=entries(defaults), data=bytes(defaults);
    if(count>16384 || data>1048576)return 44;
    manual_settings=allocate(count+4,data+256);
    if(!manual_settings || append(manual_settings,defaults))return 44;
    for(size_t i=0;i<4;i++) {
        int found=result_find_entry(manual_settings,tags[i],&e);
        int status=found ? add(manual_settings,tags[i],values[i],1) : update(manual_settings,e.index,values[i],1,NULL);
        if(status)return 44;
    }
    if(validate(manual_settings,NULL))return 44;
    printf("requested_manual ae_mode=OFF exposure_ns=%lld sensitivity=%d frame_duration_ns=%lld\n",(long long)exposure,sensitivity,(long long)duration);
    return 0;
}

static int (*ae_update)(struct camera_metadata *,size_t,const void *,size_t,struct camera_metadata_entry *);
static int prepare_auto_settings(void *library,const struct camera_metadata *defaults) {
    struct camera_metadata *(*allocate)(size_t,size_t)=dlsym(library,"allocate_camera_metadata");
    size_t (*entries)(const struct camera_metadata *)=dlsym(library,"get_camera_metadata_entry_count");
    size_t (*bytes)(const struct camera_metadata *)=dlsym(library,"get_camera_metadata_data_count");
    int (*append)(struct camera_metadata *,const struct camera_metadata *)=dlsym(library,"append_camera_metadata");
    int (*add)(struct camera_metadata *,uint32_t,const void *,size_t)=dlsym(library,"add_camera_metadata_entry");
    ae_update=dlsym(library,"update_camera_metadata_entry");
    free_metadata=dlsym(library,"free_camera_metadata");
    if(!allocate||!entries||!bytes||!append||!add||!ae_update||!free_metadata||!defaults)return 45;
    size_t count=entries(defaults), data=bytes(defaults);
    if(count>16384||data>1048576)return 45;
    const uint32_t tags[]={ACAMERA_CONTROL_MODE,ACAMERA_CONTROL_AE_MODE,ACAMERA_CONTROL_AE_LOCK,ACAMERA_CONTROL_AE_PRECAPTURE_TRIGGER};
    const uint8_t values[]={ACAMERA_CONTROL_MODE_AUTO,ACAMERA_CONTROL_AE_MODE_ON,0,ACAMERA_CONTROL_AE_PRECAPTURE_TRIGGER_START};
    camera_metadata_ro_entry_t e={0};
    for(size_t i=0;i<4;i++)if(!result_find_entry(defaults,tags[i],&e)&&e.type==0&&e.count==1)
        printf("default_ae tag=0x%x value=%u\n",tags[i],e.data.u8[0]);
    manual_settings=allocate(count+4,data+256);
    if(!manual_settings||append(manual_settings,defaults))return 45;
    for(size_t i=0;i<4;i++) {
        int found=result_find_entry(manual_settings,tags[i],&e);
        int r=found?add(manual_settings,tags[i],&values[i],1):ae_update(manual_settings,e.index,&values[i],1,NULL);
        if(r)return 45;
    }
    return 0;
}

static double monotonic_seconds(void) {
    struct timespec now; clock_gettime(CLOCK_MONOTONIC,&now);
    return now.tv_sec+now.tv_nsec/1e9;
}
static int capture_one(camera3_device_t *camera, uint32_t capacity,
                       uint32_t frame_number, bool save_image) {
    if (!camera->ops->process_capture_request || capacity < 12) return 30;
    int r;
    double frame_begin=monotonic_seconds();
    if (ae_update && manual_settings && frame_number > 1) {
        camera_metadata_ro_entry_t e={0};
        uint8_t idle=ACAMERA_CONTROL_AE_PRECAPTURE_TRIGGER_IDLE;
        if(result_find_entry(manual_settings,ACAMERA_CONTROL_AE_PRECAPTURE_TRIGGER,&e) ||
           ae_update(manual_settings,e.index,&idle,1,NULL)) return 45;
    }
    if (!capture_handle) {
        printf("stage=qti_allocate capacity=%u usage=0x%x\n", capacity, probe_blob_stream.usage);
        r = preview_mode ? lmi_qti_allocate_yuv(probe_blob_stream.width,probe_blob_stream.height,probe_blob_stream.usage,&capture_handle) : lmi_qti_allocate(capacity, probe_blob_stream.usage, &capture_handle);
        printf("qti_allocate_result=%d handle_present=%d\n", r, capture_handle != NULL);
        if (r || !capture_handle) return 31;
    }
    const struct camera_metadata *settings = manual_settings ? manual_settings :
        camera->ops->construct_default_request_settings(camera, preview_mode ? 1 : 2);
    if (!settings) return 32;
    capture_output = (camera3_stream_buffer_t){ .stream = &probe_blob_stream,
        .buffer = &capture_handle, .status = 0, .acquire_fence = -1, .release_fence = -1 };
    capture_request = (camera3_capture_request_t){ .frame_number = frame_number, .settings = settings,
        .num_output_buffers = 1, .output_buffers = &capture_output };
    pthread_mutex_lock(&capture_mutex);
    capture_expected_frame = frame_number;
    capture_received = capture_error = capture_status = 0;
    capture_release_fence = -1;
    pthread_mutex_unlock(&capture_mutex);
    printf("stage=process_capture_request frame=%u save_image=%d\n", frame_number, save_image);
    r = camera->ops->process_capture_request(camera, &capture_request);
    printf("process_capture_request_result=%d\n", r);
    if (r) return 33;
    struct timespec deadline;
    clock_gettime(CLOCK_REALTIME, &deadline); deadline.tv_sec += 5;
    pthread_mutex_lock(&capture_mutex);
    while (!capture_received && !capture_error) {
        int wait_result = pthread_cond_timedwait(&capture_cond, &capture_mutex, &deadline);
        if (wait_result == ETIMEDOUT) break;
        if (wait_result) { capture_error = 1; break; }
    }
    int received = capture_received, error = capture_error, status = capture_status;
    int fence = capture_release_fence;
    pthread_mutex_unlock(&capture_mutex);
    printf("capture_received=%d error=%d buffer_status=%d release_fence_present=%d\n",
           received, error, status, fence >= 0);
    if (!received || error || status != 0) {
        if (camera->ops->flush) { printf("stage=flush\n"); printf("flush_result=%d\n", camera->ops->flush(camera)); }
        return 34;
    }
    if (fence >= 0) {
        struct pollfd poll_fence = { .fd = fence, .events = POLLIN };
        r = poll(&poll_fence, 1, 1000);
        if (r <= 0 || !(poll_fence.revents & POLLIN) || (poll_fence.revents & (POLLERR | POLLNVAL))) return 35;
        close(fence); capture_release_fence = -1;
    }
    double result_ready=monotonic_seconds();
    void *address = NULL;
    r = lmi_qti_lock_cpu(capture_handle, &address);
    printf("qti_lock_cpu_result=%d address_present=%d\n", r, address != NULL);
    if (r || !address) return 36;
    double lock_ready=monotonic_seconds();
    int output_status=0;
    if (preview_mode) {
        if(save_image) {
            output_status=lmi_qti_save_ppm(capture_handle,probe_blob_stream.width,probe_blob_stream.height,"/data/vendor/camera/preview-next.ppm");
            if (!output_status && rename("/data/vendor/camera/preview-next.ppm","/data/vendor/camera/preview.ppm")) output_status=39;
            printf("preview_image_result=%d\n",output_status);
        } else printf("warmup_frame_discarded=%u\n",frame_number);
    } else {
        struct jpeg_footer { uint16_t id; uint32_t size; } footer;
        _Static_assert(sizeof(struct jpeg_footer) == 8, "camera3 JPEG footer ABI");
        const uint8_t *bytes = address;
        memcpy(&footer, bytes + capacity - sizeof(footer), sizeof(footer));
        printf("image_signature=%02x%02x%02x%02x\n", bytes[0], bytes[1], bytes[2], bytes[3]);
        printf("jpeg_footer_id=0x%x jpeg_size=%u\n", footer.id, footer.size);
        uint32_t footer_offset = capacity - (uint32_t)sizeof(footer);
        int expected_footer_valid = footer.id == 0xff && footer.size >= 4 &&
            footer.size <= footer_offset && bytes[0] == 0xff && bytes[1] == 0xd8 &&
            bytes[footer.size - 2] == 0xff && bytes[footer.size - 1] == 0xd9;
        if (!expected_footer_valid) {
            /* HAL may place its footer at a smaller negotiated JPEG buffer end.
             * Search only the capacity of the real allocated/locked buffer. Require
             * a unique aligned footer with a plausible size, JPEG SOI, and EOI.
             * Never infer extra mapped bytes from vendor-private handle fields. */
            uint32_t candidates = 0;
            struct jpeg_footer candidate;
            if (bytes[0] == 0xff && bytes[1] == 0xd8) {
                for (uint32_t offset = 0; offset <= capacity - sizeof(candidate); offset += 4) {
                    memcpy(&candidate, bytes + offset, sizeof(candidate));
                    if (candidate.id != 0xff || candidate.size < 4 || candidate.size > offset)
                        continue;
                    if (bytes[candidate.size - 2] != 0xff || bytes[candidate.size - 1] != 0xd9)
                        continue;
                    ++candidates;
                    if (candidates > 1) break;
                    footer = candidate;
                    footer_offset = offset;
                }
            }
            printf("jpeg_footer_search_candidates=%u\n", candidates);
            if (candidates != 1) output_status = 37;
        }
        if (!output_status) printf("accepted_jpeg_footer_offset=%u jpeg_size=%u\n", footer_offset, footer.size);
        if (!output_status && save_image) {
            int fd = open("/data/vendor/camera/test.jpg", O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
            if (fd < 0) output_status = 38;
            else {
                size_t written = 0;
                while (written < footer.size) {
                    ssize_t n = write(fd, bytes + written, footer.size - written);
                    if (n < 0 && errno == EINTR) continue;
                    if (n <= 0) { output_status = 39; break; }
                    written += (size_t)n;
                }
                if (close(fd) && !output_status) output_status = 39;
                if (!output_status) printf("jpeg_written=/data/vendor/camera/test.jpg bytes=%u\n", footer.size);
            }
        }
        if (!output_status && !save_image) printf("warmup_frame_discarded=%u\n", frame_number);
    }
    double render_ready=monotonic_seconds();
    r = lmi_qti_unlock(capture_handle); printf("qti_unlock_result=%d\n", r);
    if (preview_mode) printf("frame_timing frame=%u save=%d request_wait_ms=%.3f lock_ms=%.3f render_ms=%.3f unlock_ms=%.3f\n",
       frame_number,save_image,1000*(result_ready-frame_begin),1000*(lock_ready-result_ready),
       1000*(render_ready-lock_ready),1000*(monotonic_seconds()-render_ready));
    return output_status ? output_status : (r ? 40 : 0);
}

static int pipeline_submit(camera3_device_t *camera, struct pipeline_slot *slot,
                           uint32_t frame,const struct camera_metadata *settings) {
    pthread_mutex_lock(&capture_mutex);
    slot->frame=frame;slot->received=slot->error=slot->status=0;slot->fence=-1;
    pthread_mutex_unlock(&capture_mutex);
    slot->output=(camera3_stream_buffer_t){.stream=&probe_blob_stream,.buffer=&slot->handle,
       .status=0,.acquire_fence=-1,.release_fence=-1};
    slot->request=(camera3_capture_request_t){.frame_number=frame,.settings=settings,
       .num_output_buffers=1,.output_buffers=&slot->output};
    return camera->ops->process_capture_request(camera,&slot->request) ? 33 : 0;
}
static int capture_pipeline(camera3_device_t *camera,uint32_t count) {
    if (probe_blob_stream.max_buffers<PIPELINE_SLOTS)return 46;
    const struct camera_metadata *settings=camera->ops->construct_default_request_settings(camera,1);
    if (!settings)return 32;
    for (unsigned i=0;i<PIPELINE_SLOTS;i++)pipeline[i].fence=-1;
    for (unsigned i=0;i<PIPELINE_SLOTS;i++) {
        int r=lmi_qti_allocate_yuv(probe_blob_stream.width,probe_blob_stream.height,probe_blob_stream.usage,&pipeline[i].handle);
        if (r || !pipeline[i].handle)return 31;
    }
    for (unsigned i=0;i<PIPELINE_SLOTS;i++) {
        int r=pipeline_submit(camera,&pipeline[i],i+1,settings);if(r)return r;
    }
    double begin=monotonic_seconds();
    uint32_t last=count;
    for (uint32_t frame=1;frame<=last;frame++) {
        struct pipeline_slot *slot=&pipeline[(frame-1)%PIPELINE_SLOTS];
        struct timespec deadline;clock_gettime(CLOCK_REALTIME,&deadline);deadline.tv_sec+=5;
        pthread_mutex_lock(&capture_mutex);
        while (!slot->received && !slot->error) {
            int r=pthread_cond_timedwait(&capture_cond,&capture_mutex,&deadline);
            if(r)break;
        }
        int received=slot->received,error=slot->error,status=slot->status,fence=slot->fence;
        if(slot->frame!=frame)error=1;
        pthread_mutex_unlock(&capture_mutex);
        if(!received || error || status)return 34;
        if(fence>=0) {
            struct pollfd fd={.fd=fence,.events=POLLIN};
            int r=poll(&fd,1,1000);
            if(r<=0 || !(fd.revents&POLLIN) || (fd.revents&(POLLERR|POLLNVAL)))return 35;
            close(fence);slot->fence=-1;
        }
        if(frame>=15) {
            void *address=NULL;
            int r=lmi_qti_lock_cpu(slot->handle,&address);if(r || !address)return 36;
            r=lmi_qti_save_ppm(slot->handle,probe_blob_stream.width,probe_blob_stream.height,"/data/vendor/camera/preview-next.ppm");
            if(!r && rename("/data/vendor/camera/preview-next.ppm","/data/vendor/camera/preview.ppm"))r=39;
            int unlock=lmi_qti_unlock(slot->handle);
            if(r || unlock)return r ? r : 40;
            printf("pipeline_frame=%u elapsed_seconds=%.3f\n",frame,monotonic_seconds()-begin);
        }
        // Stop queueing after 25 seconds, then drain the two already queued
        // requests. A hard frame cap and outer service timeout remain in place.
        if(!preview_foreground && last==count && monotonic_seconds()-begin>=25.0) {
            uint32_t drain=frame+PIPELINE_SLOTS-1;
            if(drain<last)last=drain;
        }
        if(frame+PIPELINE_SLOTS<=last) {
            int r=pipeline_submit(camera,slot,frame+PIPELINE_SLOTS,settings);if(r)return r;
        }
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2 || argc > 5) {
        fprintf(stderr, "usage: %s CAMERA_ID [camera HAL .so] [--configure] [--manual-exposure | --ae-precapture | --preview | --preview-sequence | --preview-live | --preview-pipeline]\n", argv[0]);
        diagnostic_exit(2);
    }
    char *end = NULL;
    long camera_id = strtol(argv[1], &end, 10);
    if (!end || *end || camera_id < 0 || camera_id > 15) diagnostic_exit(2);
    const char *path = "/vendor/lib64/hw/camera.qcom.so";
    int do_configure = 1, manual_exposure = 0, ae_precapture = 0, preview_sequence = 0, preview_live = 0;
    for (int i = 2; i < argc; ++i) {
        if (!strcmp(argv[i], "--configure")) do_configure = 1;
        else if (!strcmp(argv[i], "--manual-exposure")) manual_exposure = 1;
        else if (!strcmp(argv[i], "--ae-precapture")) ae_precapture=1;
        else if (!strcmp(argv[i], "--preview")) preview_mode=1;
        else if (!strcmp(argv[i], "--preview-sequence")) { preview_mode=1; preview_sequence=1; }
        else if (!strcmp(argv[i], "--preview-live")) { preview_mode=1; preview_sequence=1; preview_live=1; preview_pipeline=1; }
        else if (!strcmp(argv[i], "--preview-foreground")) { preview_mode=1; preview_live=1; preview_pipeline=1; preview_foreground=1; }
        else if (!strcmp(argv[i], "--preview-pipeline")) { preview_mode=1; preview_sequence=1; preview_live=1; preview_pipeline=1; }
        else if (i == 2) path = argv[i];
        else diagnostic_exit(2);
    }
    if ((manual_exposure + ae_precapture + preview_mode > 1) || ((manual_exposure || ae_precapture || preview_mode) && camera_id != 0)) diagnostic_exit(2);
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("stage=dlopen path=%s\n", path);
    void *handle = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!handle) { fprintf(stderr, "dlopen: %s\n", dlerror()); diagnostic_exit(3); }
    camera_module_prefix_t *module = (camera_module_prefix_t *)dlsym(handle, "HMI");
    if (!module || module->common.tag != UINT32_C(0x48574d54) ||
        !module->common.id || strcmp(module->common.id, "camera")) diagnostic_exit(4);
    module->common.dso = handle;
    if (module->common.module_api_version >= 0x0204 && module->init) {
        printf("stage=module_init\n");
        int r = module->init(); printf("module_init_result=%d\n", r);
        if (r) diagnostic_exit(9);
    }
    if (module->common.module_api_version >= 0x0202 && module->get_vendor_tag_ops) {
        printf("stage=get_vendor_tag_ops\n"); module->get_vendor_tag_ops(&vendor_ops);
    }
    if (module->common.module_api_version >= 0x0201 && module->set_callbacks) {
        printf("stage=set_callbacks\n");
        int r = module->set_callbacks(&module_callbacks);
        printf("set_callbacks_result=%d\n", r); if (r) diagnostic_exit(10);
    }
    if (!module->get_number_of_cameras) diagnostic_exit(6);
    printf("stage=get_number_of_cameras\n");
    int count = module->get_number_of_cameras(); printf("camera_count=%d\n", count);
    if (count < 1 || count > 16 || camera_id >= count) diagnostic_exit(7);
    camera_info_t info = {0};
    if (!module->get_camera_info || module->get_camera_info((int)camera_id, &info)) diagnostic_exit(11);
    printf("camera_id=%ld device_version=0x%08x\n", camera_id, info.device_version);
    printf("stage=metadata_reader\n");
    void *metadata_handle = dlopen("/system/lib64/libcamera_metadata.so", RTLD_NOW | RTLD_LOCAL);
    if (!metadata_handle) { fprintf(stderr, "metadata dlopen: %s\n", dlerror()); diagnostic_exit(21); }
    find_metadata_fn find_entry = (find_metadata_fn)dlsym(metadata_handle, "find_camera_metadata_ro_entry");
    result_find_entry = find_entry;
    if (!find_entry || !info.static_camera_characteristics) diagnostic_exit(22);
    camera_metadata_ro_entry_t entry = {0};
    int orientation_status=find_entry(info.static_camera_characteristics,ACAMERA_SENSOR_ORIENTATION,&entry);
    if (!orientation_status && entry.type==1 && entry.count==1 && entry.data.i32)
        { printf("sensor_orientation_degrees=%d\n",entry.data.i32[0]);
          if (preview_live) {
              FILE *orientation=fopen("/data/vendor/camera/sensor-orientation","w");
              if (!orientation) diagnostic_exit(39);
              fprintf(orientation,"%d\n",entry.data.i32[0]);
              if (fclose(orientation)) diagnostic_exit(39);
          }
        }
    memset(&entry,0,sizeof(entry));
    int metadata_result = find_entry(info.static_camera_characteristics, PROBE_ANDROID_JPEG_MAX_SIZE, &entry);
    int32_t jpeg_max_size = 0;
    printf("jpeg_max_size_lookup=%d\n", metadata_result);
    if (!metadata_result && entry.type == 1 && entry.count == 1 && entry.data.i32) {
        jpeg_max_size = entry.data.i32[0]; printf("jpeg_max_size=%d\n", jpeg_max_size);
    }
    memset(&entry, 0, sizeof(entry));
    metadata_result = find_entry(info.static_camera_characteristics,
                                 ACAMERA_SCALER_AVAILABLE_STREAM_CONFIGURATIONS, &entry);
    printf("stream_configurations_lookup=%d\n", metadata_result);
    if (metadata_result || entry.type != 1 || !entry.data.i32 || entry.count % 4 || entry.count > 16384)
        diagnostic_exit(23);
    uint32_t chosen_width = 0, chosen_height = 0;
    uint64_t chosen_area = UINT64_MAX;
    size_t blob_count = 0;
    for (size_t i = 0; i < entry.count; i += 4) {
        const int32_t *configuration = entry.data.i32 + i;
        if (configuration[0] != (preview_mode ? 0x23 : 0x21) || configuration[3] != 0 || configuration[1] <= 0 || configuration[2] <= 0)
            continue;
        if (blob_count < 32) printf("blob_output width=%d height=%d\n", configuration[1], configuration[2]);
        ++blob_count;
        uint64_t area = (uint64_t)(uint32_t)configuration[1] * (uint32_t)configuration[2];
        if ((!preview_mode || (configuration[1]==1280 && configuration[2]==720)) && area < chosen_area) { chosen_area = area; chosen_width = configuration[1]; chosen_height = configuration[2]; }
    }
    printf("blob_output_count=%zu blob_output_reported=%zu\n", blob_count, blob_count < 32 ? blob_count : 32);
    printf("selected_blob width=%u height=%u\n", chosen_width, chosen_height);
    if (info.device_version < 0x0300 || info.device_version >= 0x0400) diagnostic_exit(12);
    if (!module->common.methods || !module->common.methods->open) diagnostic_exit(13);
    char id_string[8]; snprintf(id_string, sizeof(id_string), "%ld", camera_id);
    hw_device_t *device = NULL;
    printf("stage=device_open camera_id=%ld\n", camera_id);
    int r = module->common.methods->open(&module->common, id_string, &device);
    printf("device_open_result=%d device_present=%d\n", r, device != NULL);
    if (r || !device) diagnostic_exit(14);
    if (device->tag != UINT32_C(0x48574454) || device->version < 0x0300 || device->version >= 0x0400)
        diagnostic_exit(15);
    camera3_device_t *camera = (camera3_device_t *)device;
    printf("device_version=0x%08x ops_present=%d\n", device->version, camera->ops != NULL);
    if (camera->ops) printf("initialize_present=%d configure_streams_present=%d default_settings_present=%d\n",
                           camera->ops->initialize != NULL, camera->ops->configure_streams != NULL,
                           camera->ops->construct_default_request_settings != NULL);
    if (!camera->ops || !camera->ops->initialize || !camera->ops->construct_default_request_settings)
        diagnostic_exit(17);
    /* This initial preparation target is the observed legacy HAL3.5 ABI. */
    if (device->version > 0x0305) diagnostic_exit(18);
    printf("stage=device_initialize\n");
    int initialize_result = camera->ops->initialize(camera, &prepare_callbacks);
    printf("device_initialize_result=%d\n", initialize_result);
    if (initialize_result != 0) {
        if (device->close) device->close(device);
        diagnostic_exit(19);
    }
    printf("stage=construct_default_request_settings (STILL_CAPTURE or explicit PREVIEW)\n");
    /* CAMERA3_TEMPLATE_STILL_CAPTURE == 2; HAL owns immutable metadata. */
    const struct camera_metadata *still_settings =
        camera->ops->construct_default_request_settings(camera, preview_mode ? 1 : 2);
    printf("still_capture_defaults_present=%d\n", still_settings != NULL);
    int settings_status = still_settings ? 0 : 20;
    if (manual_exposure) {
        settings_status = prepare_manual_settings(metadata_handle, still_settings, info.static_camera_characteristics);
        printf("manual_settings_result=%d\n", settings_status);
    }
    if (ae_precapture) {
        settings_status=prepare_auto_settings(metadata_handle,still_settings);
        printf("ae_precapture_settings_result=%d\n",settings_status);
    }
    if (do_configure) {
        if (!chosen_width || !chosen_height || jpeg_max_size <= 0 || !camera->ops->configure_streams)
            diagnostic_exit(24);
        probe_blob_stream = (camera3_stream_t){
            .stream_type = 0, .width = chosen_width, .height = chosen_height,
            .format = preview_mode ? 0x23 : 0x21, .usage = 3, /* gralloc0 SW_READ_OFTEN consumer usage */
            .data_space = preview_mode ? ADATASPACE_UNKNOWN : ADATASPACE_JFIF, .rotation = 0, .physical_camera_id = ""
        };
        probe_configuration = (camera3_stream_configuration_t){
            .num_streams = 1, .streams = probe_streams, .operation_mode = 0,
            .session_parameters = NULL
        };
        printf("stage=configure_blob width=%u height=%u dataspace=0x%x\n",
               chosen_width, chosen_height, probe_blob_stream.data_space);
        int configuration_result = camera->ops->configure_streams(camera, &probe_configuration);
        printf("configure_blob_result=%d returned_format=0x%x returned_usage=0x%x max_buffers=%u\n",
               configuration_result, probe_blob_stream.format, probe_blob_stream.usage, probe_blob_stream.max_buffers);
        if (configuration_result) settings_status = 25;
    }
    /* Actual sensor frames condition exposure; an idle pause does not run 3A.
     * Reuse one genuine buffer only after previous result/fence/unlock completed.
     * Save only the last frame, with no intermediate image files. */
    uint32_t frame_count=preview_foreground ? UINT32_MAX-PIPELINE_SLOTS : (preview_pipeline ? 900 : (preview_live ? 120 : (preview_sequence ? 45 : (preview_mode ? 15 : 5))));
    struct timespec sequence_start;
    clock_gettime(CLOCK_MONOTONIC,&sequence_start);
    if (preview_pipeline && !settings_status)settings_status=capture_pipeline(camera,frame_count);
    for (uint32_t frame_number = 1; !preview_pipeline && frame_number <= frame_count && !settings_status; ++frame_number) {
        bool save=preview_live ? frame_number>=15 : (preview_sequence ? (frame_number>=15 && frame_number%3==0) : frame_number==frame_count);
        settings_status = capture_one(camera, (uint32_t)jpeg_max_size, frame_number, save);
        if (save && !settings_status) {
            struct timespec now; clock_gettime(CLOCK_MONOTONIC,&now);
            double elapsed=(now.tv_sec-sequence_start.tv_sec)+(now.tv_nsec-sequence_start.tv_nsec)/1e9;
            printf("preview_sequence_frame=%u elapsed_seconds=%.3f\n",frame_number,elapsed);
        }
    }
    if (device->close) {
        printf("stage=device_close\n"); int close_result = device->close(device);
        printf("device_close_result=%d\n", close_result);
        if (close_result) diagnostic_exit(16);
    }
    if (capture_release_fence >= 0) { close(capture_release_fence); capture_release_fence = -1; }
    if (capture_handle) {
        int release_result = lmi_qti_release(capture_handle);
        printf("qti_release_result=%d\n", release_result);
        if (release_result && !settings_status) settings_status = 41;
    }
    if(preview_pipeline)for (unsigned i=0;i<PIPELINE_SLOTS;i++) {
        if(pipeline[i].fence>=0)close(pipeline[i].fence);
        if(pipeline[i].handle) {
            int r=lmi_qti_release(pipeline[i].handle);
            printf("pipeline_release slot=%u result=%d\n",i,r);
            if(r && !settings_status)settings_status=41;
        }
    }
    if (manual_settings && free_metadata) free_metadata(manual_settings);
    diagnostic_exit(settings_status);
}
