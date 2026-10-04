/*
 * Source-only inspection of a legacy gralloc module; no buffer allocation.
 * ABI declarations derived from AOSP (Apache License 2.0):
 * Copyright (C) 2008, 2015 The Android Open Source Project.
 * https://www.apache.org/licenses/LICENSE-2.0
 * https://android.googlesource.com/platform/hardware/libhardware/+/android16-release/include_all/hardware/hardware.h
 * https://android.googlesource.com/platform/hardware/libhardware/+/android16-release/include_all/hardware/gralloc1.h
 * https://android.googlesource.com/platform/hardware/libhardware/+/android16-release/include_all/hardware/gralloc.h
 * Run in the existing isolated bionic/vendor runtime under an external timeout.
 * Usage: camera-gralloc-inspect [module.so] [--open]
 * --open uses "gralloc" for gralloc1 and "gpu0" for gralloc0. Only gralloc1
 * function availability is queried; no returned function is invoked.
 */
#include <dlfcn.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
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
    int (*open)(const struct hw_module_t *module, const char *id,
                struct hw_device_t **device);
} hw_module_methods_t;
typedef struct hw_device_t {
    uint32_t tag;
    uint32_t version;
    struct hw_module_t *module;
#ifdef __LP64__
    uint64_t reserved[12];
#else
    uint32_t reserved[12];
#endif
    int (*close)(struct hw_device_t *device);
} hw_device_t;
typedef void (*gralloc1_function_pointer_t)();
typedef struct gralloc1_device {
    struct hw_device_t common;
    void (*getCapabilities)(struct gralloc1_device *device, uint32_t *outCount,
                            int32_t *outCapabilities);
    gralloc1_function_pointer_t (*getFunction)(struct gralloc1_device *device,
                                              int32_t descriptor);
} gralloc1_device_t;
#ifdef __LP64__
_Static_assert(sizeof(hw_module_t) == 248, "AOSP hw_module_t LP64 ABI");
_Static_assert(sizeof(hw_device_t) == 120, "AOSP hw_device_t LP64 ABI");
_Static_assert(offsetof(gralloc1_device_t, getFunction) == 128,
               "AOSP gralloc1 LP64 ABI");
#else
_Static_assert(sizeof(hw_module_t) == 128, "AOSP hw_module_t ILP32 ABI");
_Static_assert(sizeof(hw_device_t) == 64, "AOSP hw_device_t ILP32 ABI");
_Static_assert(offsetof(gralloc1_device_t, getFunction) == 68,
               "AOSP gralloc1 ILP32 ABI");
#endif

int main(int argc, char **argv) {
    const char *path = "/vendor/lib64/hw/gralloc.default.so";
    int do_open = 0;
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--open") == 0) do_open = 1;
        else if (i == 1) path = argv[i];
        else { fprintf(stderr, "usage: %s [module.so] [--open]\n", argv[0]); return 2; }
    }
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("stage=dlopen path=%s\n", path);
    void *handle = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!handle) { fprintf(stderr, "dlopen failed: %s\n", dlerror()); return 3; }
    dlerror();
    hw_module_t *module = (hw_module_t *)dlsym(handle, "HMI");
    const char *error = dlerror();
    if (error || !module) { fprintf(stderr, "HMI failed: %s\n", error ? error : "NULL"); return 4; }
    printf("stage=HMI tag=0x%08x module_api=0x%04x hal_api=0x%04x\n",
           module->tag, module->module_api_version, module->hal_api_version);
    if (module->tag != UINT32_C(0x48574d54) || !module->id || strcmp(module->id, "gralloc")) {
        fprintf(stderr, "expected HWMT/gralloc\n"); return 5;
    }
    printf("module_id=gralloc\n");
    if (!do_open) return 0;
    if (!module->methods || !module->methods->open) return 6;
    /* Match libhardware's successful load(): module->dso = dlopen handle. */
    module->dso = handle;
    const char *open_id = module->module_api_version >= 0x0100 ? "gralloc" : "gpu0";
    printf("stage=open open_id=%s\n", open_id);
    hw_device_t *device = NULL;
    int result = module->methods->open(module, open_id, &device);
    printf("open_result=%d device_present=%d\n", result, device != NULL);
    if (result || !device) return 7;
    printf("device_tag=0x%08x device_version=0x%08x\n", device->tag, device->version);
    if (device->tag != UINT32_C(0x48574454)) return 8;
    if (module->module_api_version >= 0x0100 && device->version >= 0x0100) {
        gralloc1_device_t *g = (gralloc1_device_t *)device;
        if (!g->getFunction) return 9;
        static const struct { int32_t id; const char *name; } functions[] = {
            {2, "CREATE_DESCRIPTOR"}, {3, "DESTROY_DESCRIPTOR"},
            {4, "SET_CONSUMER_USAGE"}, {5, "SET_DIMENSIONS"},
            {6, "SET_FORMAT"}, {7, "SET_PRODUCER_USAGE"},
            {13, "GET_STRIDE"}, {14, "ALLOCATE"}, {15, "RETAIN"},
            {16, "RELEASE"}, {18, "LOCK"}, {20, "UNLOCK"}
        };
        for (size_t i = 0; i < sizeof(functions)/sizeof(functions[0]); ++i) {
            printf("stage=getFunction descriptor=%d name=%s\n", functions[i].id, functions[i].name);
            gralloc1_function_pointer_t p = g->getFunction(g, functions[i].id);
            printf("function=%s present=%d\n", functions[i].name, p != NULL);
        }
    } else printf("gralloc0_device=1 gralloc1_query_skipped=1\n");
    if (device->close) { printf("stage=close\n"); printf("close_result=%d\n", device->close(device)); }
    /* No dlclose: process exit owns vendor-module lifetime. */
    return 0;
}
