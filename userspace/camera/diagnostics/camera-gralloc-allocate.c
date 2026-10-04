/*
 * Isolated gralloc0 allocation diagnostic; no camera requests or image data.
 * ABI declarations derived from AOSP (Apache License 2.0):
 * Copyright (C) 2008 The Android Open Source Project.
 * https://www.apache.org/licenses/LICENSE-2.0
 * https://android.googlesource.com/platform/hardware/libhardware/+/c16e56d/include/hardware/gralloc.h
 * Hardware LP64 layout follows current hardware.h, as in gralloc-inspect.
 * Run under the existing private vendor runtime and an external timeout.
 */
#include <dlfcn.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct hw_module_methods_t;
struct hw_device_t;
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
typedef struct hw_module_methods_t {
    int (*open)(const hw_module_t *, const char *, struct hw_device_t **);
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
    int (*close)(struct hw_device_t *);
} hw_device_t;

/* Opaque native_handle_t: do not inspect vendor-private payload or fd layout. */
struct native_handle;
typedef const struct native_handle *buffer_handle_t;
typedef struct gralloc_module_t {
    hw_module_t common;
    int (*registerBuffer)(const struct gralloc_module_t *, buffer_handle_t);
    int (*unregisterBuffer)(const struct gralloc_module_t *, buffer_handle_t);
    int (*lock)(const struct gralloc_module_t *, buffer_handle_t, int,
                int, int, int, int, void **);
    int (*unlock)(const struct gralloc_module_t *, buffer_handle_t);
    int (*perform)(const struct gralloc_module_t *, int, ...);
    void *reserved_proc[7]; /* Exact gralloc module 0.1 tail. */
} gralloc_module_t;
typedef struct alloc_device_t {
    hw_device_t common;
    int (*alloc)(struct alloc_device_t *, int, int, int, int,
                 buffer_handle_t *, int *);
    int (*free)(struct alloc_device_t *, buffer_handle_t);
    void (*dump)(struct alloc_device_t *, char *, int);
    void *reserved_proc[7];
} alloc_device_t;

enum {
    GRALLOC_USAGE_SW_READ_OFTEN = 0x00000003,
    GRALLOC_USAGE_HW_CAMERA_WRITE = 0x00020000,
    HAL_PIXEL_FORMAT_BLOB = 0x21,
    BLOB_BYTES = 16 * 1024 * 1024
};
#ifdef __LP64__
_Static_assert(sizeof(hw_module_t) == 248, "LP64 module ABI");
_Static_assert(sizeof(hw_device_t) == 120, "LP64 device ABI");
_Static_assert(offsetof(gralloc_module_t, lock) == 264, "LP64 lock ABI");
_Static_assert(offsetof(gralloc_module_t, unlock) == 272, "LP64 unlock ABI");
_Static_assert(offsetof(alloc_device_t, alloc) == 120, "LP64 alloc ABI");
_Static_assert(offsetof(alloc_device_t, free) == 128, "LP64 free ABI");
#endif

int main(int argc, char **argv) {
    const char *path = "/vendor/lib64/hw/gralloc.default.so";
    int do_lock = 0;
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--lock") == 0) do_lock = 1;
        else if (i == 1) path = argv[i];
        else { fprintf(stderr, "usage: %s [module.so] [--lock]\n", argv[0]); return 2; }
    }
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("stage=dlopen path=%s\n", path);
    void *dso = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!dso) { fprintf(stderr, "dlopen failed: %s\n", dlerror()); return 3; }
    dlerror();
    gralloc_module_t *module = (gralloc_module_t *)dlsym(dso, "HMI");
    const char *error = dlerror();
    if (error || !module) { fprintf(stderr, "HMI failed: %s\n", error ? error : "NULL"); return 4; }
    printf("stage=HMI tag=0x%08x module_api=0x%04x hal_api=0x%04x\n",
           module->common.tag, module->common.module_api_version,
           module->common.hal_api_version);
    if (module->common.tag != UINT32_C(0x48574d54) || !module->common.id ||
        strcmp(module->common.id, "gralloc") || module->common.module_api_version != 0x0001 ||
        !module->common.methods || !module->common.methods->open) return 5;
    module->common.dso = dso;
    hw_device_t *common_device = NULL;
    printf("stage=open open_id=gpu0\n");
    int result = module->common.methods->open(&module->common, "gpu0", &common_device);
    printf("open_result=%d device_present=%d\n", result, common_device != NULL);
    if (result || !common_device) return 6;
    alloc_device_t *device = (alloc_device_t *)common_device;
    printf("device_tag=0x%08x device_version=0x%08x\n", device->common.tag, device->common.version);
    if (device->common.tag != UINT32_C(0x48574454) || device->common.version != 0 ||
        !device->alloc || !device->free || !device->common.close) return 7;
    buffer_handle_t handle = NULL;
    int stride = 0;
    int failed = 0;
    int usage = GRALLOC_USAGE_SW_READ_OFTEN | GRALLOC_USAGE_HW_CAMERA_WRITE;
    printf("stage=alloc width=%d height=1 format=0x%x usage=0x%x\n",
           BLOB_BYTES, HAL_PIXEL_FORMAT_BLOB, usage);
    result = device->alloc(device, BLOB_BYTES, 1, HAL_PIXEL_FORMAT_BLOB, usage, &handle, &stride);
    printf("alloc_result=%d handle_present=%d stride=%d\n", result, handle != NULL, stride);
    if (result || !handle) failed = 8;
    else {
        if (do_lock) {
            if (!module->lock || !module->unlock) failed = 9;
            else {
                void *address = NULL;
                printf("stage=lock usage=0x%x\n", GRALLOC_USAGE_SW_READ_OFTEN);
                result = module->lock(module, handle, GRALLOC_USAGE_SW_READ_OFTEN,
                                      0, 0, BLOB_BYTES, 1, &address);
                printf("lock_result=%d address_present=%d\n", result, address != NULL);
                if (result) failed = 10;
                else {
                    if (!address) failed = 10;
                    /* Do not read or write uninitialized buffer content. */
                    printf("stage=unlock\n");
                    result = module->unlock(module, handle);
                    printf("unlock_result=%d\n", result);
                    if (result) {
                        /* A failed unlock leaves ownership uncertain: no free/close. */
                        printf("stage=exit_after_unlock_failure\n");
                        _Exit(11);
                    }
                }
            }
        }
        printf("stage=free\n");
        result = device->free(device, handle);
        printf("free_result=%d\n", result);
        if (result) failed = 12;
        handle = NULL;
    }
    printf("stage=close\n");
    result = device->common.close(&device->common);
    printf("close_result=%d\n", result);
    if (result) failed = 13;
    /* Avoid unrelated vendor global destructors; no dlclose. */
    printf("stage=done result=%d\n", failed);
    _Exit(failed);
}
