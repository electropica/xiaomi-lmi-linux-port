/*
 * Source-only HAL3 preparation diagnostic. Opens one camera and inspects its
 * operation table, initializes callbacks, and requests STILL_CAPTURE defaults.
 * Reports public JPEG metadata; --configure configures one advertised BLOB
 * output stream. Does not allocate buffers or submit capture requests.
 * Reuses the verified AOSP module ABI and stable callback tables in the enum
 * source. Camera3 ABI provenance (Apache License 2.0, AOSP):
 * https://android.googlesource.com/platform/hardware/libhardware/+/android16-release/include_all/hardware/camera3.h
 * https://source.android.com/reference/hal/structcamera3__device__ops
 * Run in the private bionic runtime, with the same property/runtime setup as
 * enumeration and an external timeout. Never run alongside the OEM provider.
 * Usage: camera-module-prepare CAMERA_ID [camera.qcom.so path] [--configure]
 */
#define main enumeration_diagnostic_main
#include "camera-module-enumerate.c"
#undef main
#include <camera/NdkCameraMetadataTags.h>
#include <android/data_space.h>

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
static camera3_stream_t probe_blob_stream;
static camera3_stream_t *probe_streams[] = { &probe_blob_stream };
static camera3_stream_configuration_t probe_configuration;
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
static void prepare_result_callback(const camera3_callback_ops_t *cb,
                                     const camera3_capture_result_t *result) {
    (void)cb;
    if (result) printf("callback=capture_result frame=%u output_buffers=%u partial=%u\n",
                       result->frame_number, result->num_output_buffers, result->partial_result);
}
static void prepare_notify_callback(const camera3_callback_ops_t *cb,
                                     const camera3_notify_msg_t *msg) {
    (void)cb;
    if (!msg) return;
    printf("callback=notify type=%d\n", msg->type);
    if (msg->type == 1) printf("notify_error frame=%u code=%d\n",
                               msg->message.error.frame_number, msg->message.error.error_code);
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
#else
_Static_assert(sizeof(hw_device_t) == 64, "AOSP ILP32 device ABI");
_Static_assert(offsetof(camera3_device_t, ops) == 64, "AOSP ILP32 camera ops ABI");
#endif

int main(int argc, char **argv) {
    if (argc < 2 || argc > 4) {
        fprintf(stderr, "usage: %s CAMERA_ID [camera HAL .so] [--configure]\n", argv[0]);
        diagnostic_exit(2);
    }
    char *end = NULL;
    long camera_id = strtol(argv[1], &end, 10);
    if (!end || *end || camera_id < 0 || camera_id > 15) diagnostic_exit(2);
    const char *path = "/vendor/lib64/hw/camera.qcom.so";
    int do_configure = 0;
    for (int i = 2; i < argc; ++i) {
        if (!strcmp(argv[i], "--configure")) do_configure = 1;
        else if (i == 2) path = argv[i];
        else diagnostic_exit(2);
    }
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
    if (!find_entry || !info.static_camera_characteristics) diagnostic_exit(22);
    camera_metadata_ro_entry_t entry = {0};
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
        if (configuration[0] != 0x21 || configuration[3] != 0 || configuration[1] <= 0 || configuration[2] <= 0)
            continue;
        if (blob_count < 32) printf("blob_output width=%d height=%d\n", configuration[1], configuration[2]);
        ++blob_count;
        uint64_t area = (uint64_t)(uint32_t)configuration[1] * (uint32_t)configuration[2];
        if (area < chosen_area) { chosen_area = area; chosen_width = configuration[1]; chosen_height = configuration[2]; }
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
    printf("stage=construct_default_request_settings template=STILL_CAPTURE\n");
    /* CAMERA3_TEMPLATE_STILL_CAPTURE == 2; HAL owns immutable metadata. */
    const struct camera_metadata *still_settings =
        camera->ops->construct_default_request_settings(camera, 2);
    printf("still_capture_defaults_present=%d\n", still_settings != NULL);
    int settings_status = still_settings != NULL ? 0 : 20;
    if (do_configure) {
        if (!chosen_width || !chosen_height || jpeg_max_size <= 0 || !camera->ops->configure_streams)
            diagnostic_exit(24);
        probe_blob_stream = (camera3_stream_t){
            .stream_type = 0, .width = chosen_width, .height = chosen_height,
            .format = 0x21, .usage = 3, /* gralloc0 SW_READ_OFTEN consumer usage */
            .data_space = ADATASPACE_JFIF, .rotation = 0, .physical_camera_id = ""
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
    if (device->close) {
        printf("stage=device_close\n"); int close_result = device->close(device);
        printf("device_close_result=%d\n", close_result);
        if (close_result) diagnostic_exit(16);
    }
    diagnostic_exit(settings_status);
}
