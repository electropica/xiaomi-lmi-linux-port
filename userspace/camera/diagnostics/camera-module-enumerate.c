/*
 * Source-only diagnostic: enumerate the legacy camera HAL module directly.
 * No device open, stream setup, camera capture, or service registration.
 *
 * ABI definitions below reproduce only the necessary AOSP public prefix:
 * https://android.googlesource.com/platform/hardware/libhardware/+/android16-release/include_all/hardware/hardware.h
 * https://android.googlesource.com/platform/hardware/libhardware/+/android16-release/include_all/hardware/camera_common.h
 * https://android.googlesource.com/platform/system/media/+/android16-release/camera/include/system/vendor_tags.h
 * AOSP verifies camera_module_t.get_number_of_cameras at offset 128 (32 bit)
 * or 248 (64 bit), see:
 * https://android.googlesource.com/platform/hardware/libhardware/+/refs/tags/android-cts-6.0_r15/tests/hardware/struct-offset.cpp
 *
 * Derived ABI declarations: Copyright (C) 2008 The Android Open Source Project.
 * Licensed under the Apache License, Version 2.0:
 * https://www.apache.org/licenses/LICENSE-2.0
 *
 * Run only in the existing private Android/bionic runtime with its configured
 * vendor linker dependencies and property bridge. This is not a glibc client.
 * Calls optional camera_module_t.init() for module API >= 2.4 before counting.
 * A successful count is not
 * proof that initialization, camera opening, or capture works.
 */
#include <dlfcn.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct hw_module_methods_t;
struct hw_device_t;
struct camera_info;
struct camera_metadata;
typedef struct camera_info {
    int facing;
    int orientation;
    uint32_t device_version;
    const struct camera_metadata *static_camera_characteristics;
    int resource_cost;
    char **conflicting_devices;
    size_t conflicting_devices_length;
} camera_info_t;
struct camera_module_callbacks;
struct vendor_tag_ops;
typedef struct vendor_tag_ops {
    int (*get_tag_count)(const struct vendor_tag_ops *v);
    void (*get_all_tags)(const struct vendor_tag_ops *v, uint32_t *tag_array);
    const char *(*get_section_name)(const struct vendor_tag_ops *v, uint32_t tag);
    const char *(*get_tag_name)(const struct vendor_tag_ops *v, uint32_t tag);
    int (*get_tag_type)(const struct vendor_tag_ops *v, uint32_t tag);
    void *reserved[8];
} vendor_tag_ops_t;
typedef struct camera_module_callbacks {
    void (*camera_device_status_change)(const struct camera_module_callbacks *,
                                       int camera_id, int new_status);
    void (*torch_mode_status_change)(const struct camera_module_callbacks *,
                                    const char *camera_id, int new_status);
} camera_module_callbacks_t;

/* HAL may retain both tables: keep their addresses stable until process exit. */
static vendor_tag_ops_t vendor_ops;
static void camera_status_changed(const camera_module_callbacks_t *callbacks,
                                  int camera_id, int new_status) {
    (void)callbacks;
    printf("callback=camera_device_status camera_id=%d status=%d\n", camera_id, new_status);
}
static void torch_status_changed(const camera_module_callbacks_t *callbacks,
                                 const char *camera_id, int new_status) {
    (void)callbacks;
    printf("callback=torch_mode_status camera_id=%.64s status=%d\n",
           camera_id ? camera_id : "(null)", new_status);
}
static const camera_module_callbacks_t module_callbacks = {
    .camera_device_status_change = camera_status_changed,
    .torch_mode_status_change = torch_status_changed
};
typedef struct hw_module_t {
    uint32_t tag;
    uint16_t module_api_version;
    uint16_t hal_api_version;
    const char *id;
    const char *name;
    const char *author;
    struct hw_module_methods_t *methods;
    void *dso;
#ifdef __LP64__
    uint64_t reserved[32 - 7];
#else
    uint32_t reserved[32 - 7];
#endif
} hw_module_t;

/* A prefix, not a full camera_module_t: never use sizeof to copy a real HAL. */
typedef struct camera_module_prefix_t {
    hw_module_t common;
    int (*get_number_of_cameras)(void);
    int (*get_camera_info)(int camera_id, struct camera_info *info);
    int (*set_callbacks)(const struct camera_module_callbacks *callbacks);
    void (*get_vendor_tag_ops)(struct vendor_tag_ops *ops);
    int (*open_legacy)(const struct hw_module_t *module, const char *id,
                       uint32_t hal_version, struct hw_device_t **device);
    int (*set_torch_mode)(const char *camera_id, bool enabled);
    int (*init)(void);
} camera_module_prefix_t;

#ifdef __LP64__
_Static_assert(sizeof(hw_module_t) == 248, "AOSP LP64 hw_module_t ABI");
_Static_assert(offsetof(camera_module_prefix_t, get_number_of_cameras) == 248,
               "AOSP LP64 camera count ABI");
_Static_assert(offsetof(camera_module_prefix_t, init) == 296,
               "AOSP LP64 camera init ABI");
_Static_assert(sizeof(vendor_tag_ops_t) == 104, "AOSP LP64 vendor ops ABI");
_Static_assert(sizeof(camera_module_callbacks_t) == 16, "AOSP LP64 callbacks ABI");
_Static_assert(sizeof(camera_info_t) == 48, "AOSP LP64 camera info ABI");
_Static_assert(offsetof(camera_info_t, static_camera_characteristics) == 16,
               "AOSP LP64 camera metadata pointer ABI");
#else
_Static_assert(sizeof(hw_module_t) == 128, "AOSP ILP32 hw_module_t ABI");
_Static_assert(offsetof(camera_module_prefix_t, get_number_of_cameras) == 128,
               "AOSP ILP32 camera count ABI");
_Static_assert(offsetof(camera_module_prefix_t, init) == 152,
               "AOSP ILP32 camera init ABI");
_Static_assert(sizeof(vendor_tag_ops_t) == 52, "AOSP ILP32 vendor ops ABI");
_Static_assert(sizeof(camera_module_callbacks_t) == 8, "AOSP ILP32 callbacks ABI");
_Static_assert(sizeof(camera_info_t) == 28, "AOSP ILP32 camera info ABI");
_Static_assert(offsetof(camera_info_t, static_camera_characteristics) == 12,
               "AOSP ILP32 camera metadata pointer ABI");
#endif

/* Diagnostic lifetime only: flush evidence and terminate without executing
 * proprietary atexit/static destructors. The kernel reclaims process resources.
 * This does not establish that normal provider teardown is safe. */
static _Noreturn void diagnostic_exit(int status) {
    fflush(stdout);
    fflush(stderr);
    _Exit(status);
}

int main(int argc, char **argv) {
    const char *path = "/vendor/lib64/hw/camera.qcom.so";
    const uint32_t expected_tag = ((uint32_t)'H' << 24) |
        ((uint32_t)'W' << 16) | ((uint32_t)'M' << 8) | (uint32_t)'T';
    if (argc > 2) {
        fprintf(stderr, "usage: %s [camera HAL .so path]\n", argv[0]);
        diagnostic_exit(2);
    }
    if (argc == 2) path = argv[1];
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("stage=dlopen path=%s\n", path);
    void *handle = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!handle) {
        fprintf(stderr, "dlopen failed: %s\n", dlerror());
        diagnostic_exit(3);
    }
    dlerror();
    camera_module_prefix_t *module =
        (camera_module_prefix_t *)dlsym(handle, "HMI");
    const char *error = dlerror();
    if (error || !module) {
        fprintf(stderr, "HMI lookup failed: %s\n", error ? error : "NULL symbol");
        diagnostic_exit(4);
    }
    printf("stage=HMI tag=0x%08x module_api=0x%04x hal_api=0x%04x\n",
           module->common.tag, module->common.module_api_version,
           module->common.hal_api_version);
    if (module->common.tag != expected_tag || !module->common.id ||
        strcmp(module->common.id, "camera") != 0) {
        fprintf(stderr, "unexpected module tag or id (expected HWMT/camera)\n");
        diagnostic_exit(5);
    }
    printf("module_id=camera\n");
    module->common.dso = handle; /* Match AOSP hw_get_module's load contract. */
    if (module->common.module_api_version >= 0x0204 && module->init) {
        printf("stage=module_init\n");
        int init_result = module->init();
        printf("module_init_result=%d\n", init_result);
        if (init_result != 0) {
            fprintf(stderr, "camera module initialization failed\n");
            diagnostic_exit(9);
        }
    }
    if (module->common.module_api_version >= 0x0202 && module->get_vendor_tag_ops) {
        printf("stage=get_vendor_tag_ops\n");
        module->get_vendor_tag_ops(&vendor_ops);
        printf("vendor_tag_ops_returned=1 tag_count_function_present=%d\n",
               vendor_ops.get_tag_count != NULL);
        /* The OEM getter registers its ops with libcamera_metadata itself;
         * this probe does not repeat set_camera_metadata_vendor_ops(). */
    }
    if (module->common.module_api_version >= 0x0201 && module->set_callbacks) {
        printf("stage=set_callbacks\n");
        int callbacks_result = module->set_callbacks(&module_callbacks);
        printf("set_callbacks_result=%d\n", callbacks_result);
        if (callbacks_result != 0) diagnostic_exit(10);
    }
    if (!module->get_number_of_cameras) {
        fprintf(stderr, "get_number_of_cameras is NULL\n");
        diagnostic_exit(6);
    }
    printf("stage=get_number_of_cameras\n");
    int count = module->get_number_of_cameras();
    printf("camera_count=%d\n", count);
    if (count < 0 || count > 16) {
        fprintf(stderr, "camera count outside diagnostic bound 0..16\n");
        diagnostic_exit(7);
    }
    int info_failures = 0;
    for (int id = 0; id < count; ++id) {
        printf("camera_id=%d\n", id);
        if (!module->get_camera_info) { ++info_failures; continue; }
        camera_info_t info = {0};
        printf("stage=get_camera_info camera_id=%d\n", id);
        int info_result = module->get_camera_info(id, &info);
        printf("camera_info_result=%d camera_id=%d\n", info_result, id);
        if (info_result != 0) { ++info_failures; continue; }
        printf("camera_info camera_id=%d facing=%d orientation=%d device_version=0x%08x metadata_present=%d\n",
               id, info.facing, info.orientation, info.device_version,
               info.static_camera_characteristics != NULL);
    }
    /* Do not dlclose a vendor module with potentially running worker threads.
     * Process exit owns cleanup; use a bounded external timeout for the probe. */
    diagnostic_exit(count == 0 ? 8 : (info_failures ? 11 : 0));
}
