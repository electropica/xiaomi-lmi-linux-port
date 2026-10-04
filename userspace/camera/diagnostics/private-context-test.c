/* Diagnostic only: bounded, isolated HIDL manager/lshal tests.
 * The ioctl forwarding assumes pointer arguments used by these binaries;
 * it is not a generic preload library or a production security solution.
 * No physical camera nodes are exposed by the private test supervisor. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <stdatomic.h>
#include <stdint.h>
#include <sys/system_properties.h>
#include <stdarg.h>
#include <errno.h>
#define BIONIC_IOCTL_NO_SIGNEDNESS_OVERLOAD
#include <sys/ioctl.h>
#include <linux/android/binder.h>
#include <android/set_abort_message.h>
static int private_enabled(void);

/* Observe the original abort reason; never suppress the abort. */
void android_set_abort_message(const char *message) {
    if (private_enabled()) fprintf(stderr, "PRIVATE_ORIGINAL_ABORT: %s\n", message ? message : "(null)");
    void (*next)(const char *) = dlsym(RTLD_NEXT, "android_set_abort_message");
    if (next) next(message);
}

static int private_enabled(void) {
    const char *value = getenv("LMI_PRIVATE_CONTEXT_ACTIVE");
    return value && !strcmp(value, "1");
}

/* Private no-camera HIDL startup diagnostic only. This is not a production
 * access-control policy and must never be injected into the host session. */
int getcon(char **context) {
    if (!private_enabled()) {
        int (*next)(char **) = dlsym(RTLD_NEXT, "getcon");
        return next ? next(context) : -1;
    }
    fputs("PRIVATE_HIDL_TEST_SYNTHETIC_CONTEXT_NO_CAMERA_ACCESS\n", stderr);
    *context = strdup("u:r:hwservicemanager:s0");
    return *context ? 0 : -1;
}

static _Atomic int ready;
static char ready_token;
static const char ready_name[] = "hwservicemanager.ready";

__attribute__((constructor)) static void checked_client_ready(void) {
    const char *checked = getenv("LMI_PRIVATE_HIDL_READY_CHECKED");
    if (private_enabled() && checked && !strcmp(checked, "1")) {
        atomic_store(&ready, 1);
        fputs("PRIVATE_CLIENT_READY_AFTER_BINDER_CONTEXT_CHECK\n", stderr);
    }
}

int __system_property_set(const char *name, const char *value) {
    if (private_enabled() && !strcmp(name, ready_name)) {
        atomic_store(&ready, !strcmp(value, "true"));
        fputs("PRIVATE_HIDL_READY_PROPERTY_UPDATED\n", stderr);
        return 0;
    }
    int (*next)(const char *, const char *) = dlsym(RTLD_NEXT, "__system_property_set");
    return next ? next(name, value) : -1;
}

const prop_info *__system_property_find(const char *name) {
    if (private_enabled() && !strcmp(name, ready_name))
        return atomic_load(&ready) ? (const prop_info *)&ready_token : NULL;
    const prop_info *(*next)(const char *) = dlsym(RTLD_NEXT, "__system_property_find");
    return next ? next(name) : NULL;
}

int ioctl(int fd, int request, ...) {
    va_list arguments;
    va_start(arguments, request);
    void *argument = va_arg(arguments, void *);
    va_end(arguments);
    int (*next)(int, int, ...) = dlsym(RTLD_NEXT, "ioctl");
    if (!next) { errno = ENOSYS; return -1; }
    if (private_enabled() && (unsigned)request == BINDER_SET_CONTEXT_MGR_EXT && argument) {
        struct flat_binder_object object = *(struct flat_binder_object *)argument;
        object.flags &= ~FLAT_BINDER_FLAG_TXN_SECURITY_CTX;
        fputs("PRIVATE_BINDER_CONTEXT_WITHOUT_UNSUPPORTED_SECCTX\n", stderr);
        return next(fd, request, &object);
    }
    return next(fd, request, argument);
}

void __system_property_read_callback(const prop_info *info,
        void (*callback)(void *, const char *, const char *, uint32_t), void *cookie) {
    if (info == (const prop_info *)&ready_token) {
        callback(cookie, ready_name, atomic_load(&ready) ? "true" : "false", 1);
        return;
    }
    void (*next)(const prop_info *, void (*)(void *, const char *, const char *, uint32_t), void *) =
        dlsym(RTLD_NEXT, "__system_property_read_callback");
    if (next) next(info, callback, cookie);
}
