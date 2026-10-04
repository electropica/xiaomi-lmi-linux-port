/* Private bounded diagnostics, NOT a production camera runtime.
 * Variadic ioctl forwarding assumes the tested pointer-argument callers.
 * Transaction pointer inspection trusts libhidl parcels; invalid pointers can
 * crash this diagnostic. Copies are capped at 64 KiB commands / 2 MiB data.
 * Some private variants expose camera devices for sensor probing; never use
 * this preload in the host session or as a general access-control policy.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdbool.h>
#include <sys/system_properties.h>
#include <stdarg.h>
#include <errno.h>
#include <unistd.h>
#define BIONIC_IOCTL_NO_SIGNEDNESS_OVERLOAD
#include <sys/ioctl.h>
#include <linux/android/binder.h>
#include <android/set_abort_message.h>
#include <android/log.h>
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

/* Symphony explicitly looks up the property getter on a libc handle.
 * Keep ordinary lookup semantics and only bridge that one private query. */
void *dlsym(void *handle, const char *name) {
    void *(*next)(void *, const char *) = dlvsym(RTLD_NEXT, "dlsym", "LIBC");
    if (!next) return NULL;
    const char *platform = getenv("LMI_PRIVATE_BOOT_PLATFORM");
    if (private_enabled() && platform && !strcmp(platform, "kona") &&
        handle != RTLD_NEXT && handle != RTLD_DEFAULT &&
        !strcmp(name, "__system_property_get")) {
        fputs("PRIVATE_EXPLICIT_LIBC_PROPERTY_GETTER_BRIDGE\n", stderr);
        return (void *)&__system_property_get;
    }
    return next(handle, name);
}

bool private_requesting_sid(void *self)
    __asm__("_ZN7android8hardware9BHwBinder15isRequestingSidEv");
bool private_requesting_sid(void *self) {
    bool (*next)(void *) = dlsym(RTLD_NEXT,
        "_ZN7android8hardware9BHwBinder15isRequestingSidEv");
    const char *gate = getenv("LMI_PRIVATE_BINDER_NO_SECCTX");
    if (private_enabled() && gate && !strcmp(gate, "1")) return false;
    return next ? next(self) : false;
}

/* Only the supervisor-selected lshal PID receives a diagnostic identity.
 * Unknown peers retain the original behavior; SELinux access checks remain. */
const char *private_calling_sid(const void *self)
    __asm__("_ZNK7android8hardware14IPCThreadState13getCallingSidEv");
const char *private_calling_sid(const void *self) {
    const char *(*next)(const void *) = dlsym(RTLD_NEXT,
        "_ZNK7android8hardware14IPCThreadState13getCallingSidEv");
    const char *original = next ? next(self) : NULL;
    const char *gate = getenv("LMI_PRIVATE_PEER_CHECK");
    if (original || !private_enabled() || !gate || strcmp(gate, "1")) return original;
    int (*pid_function)(const void *) = dlsym(RTLD_NEXT,
        "_ZNK7android8hardware14IPCThreadState13getCallingPidEv");
    if (!pid_function) return original;
    FILE *file = fopen("/checked-client.pid", "r");
    int allowed = -1;
    if (file) { if (fscanf(file, "%d", &allowed) != 1) allowed = -1; fclose(file); }
    if (allowed <= 1 || pid_function(self) != allowed) return original;
    fputs("PRIVATE_CALLER_IDENTITY_FOR_CHECKED_CLIENT_ONLY\n", stderr);
    return "u:r:shell:s0";
}

int selinux_check_access(const char *source, const char *target, const char *kind,
                         const char *permission, void *audit) {
    int (*next)(const char *, const char *, const char *, const char *, void *) =
        dlsym(RTLD_NEXT, "selinux_check_access");
    int result = next ? next(source, target, kind, permission, audit) : -1;
    if (private_enabled()) fprintf(stderr, "PRIVATE_ORIGINAL_ACCESS_CHECK %s %s result=%d\n",
                                    kind, permission, result);
    return result;
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

int getpidcon(pid_t pid, char **context) {
    const char *gate = getenv("LMI_PRIVATE_PEER_CHECK");
    if (private_enabled() && gate && !strcmp(gate, "1") && pid == getpid())
        return getcon(context);
    int (*next)(pid_t, char **) = dlsym(RTLD_NEXT, "getpidcon");
    return next ? next(pid, context) : -1;
}

static _Atomic int ready;
static char ready_token;
static const char ready_name[] = "hwservicemanager.ready";

int __system_property_get(const char *name, char *value) {
    const char *hardware = getenv("LMI_PRIVATE_BOOT_HARDWARE");
    if (private_enabled() && !strcmp(name, "ro.hardware") && hardware && !strcmp(hardware, "qcom")) {
        strcpy(value, hardware);
        fputs("PRIVATE_HARDWARE_FROM_CHECKED_BOOT_PARAMETER\n", stderr);
        return 4;
    }
    const char *platform = getenv("LMI_PRIVATE_BOOT_PLATFORM");
    if (private_enabled() && platform && !strcmp(platform, "kona") &&
        (!strcmp(name, "ro.board.platform") || !strcmp(name, "ro.product.board"))) {
        strcpy(value, platform);
        fputs("PRIVATE_PLATFORM_FROM_CHECKED_VENDOR_PROPERTY\n", stderr);
        return 4;
    }
    int (*next)(const char *, char *) = dlsym(RTLD_NEXT, "__system_property_get");
    return next ? next(name, value) : 0;
}

static void private_log_message(struct __android_log_message *message) {
    if (message->priority < ANDROID_LOG_WARN) return;
    fprintf(stderr, "PRIVATE_ANDROID_LOG %d %s: %.2048s\n", message->priority,
            message->tag ? message->tag : "", message->message ? message->message : "");
}

__attribute__((constructor)) static void checked_client_ready(void) {
    if (private_enabled()) {
        void (*set_logger)(void (*)(struct __android_log_message *)) =
            dlsym(RTLD_DEFAULT, "__android_log_set_logger");
        if (set_logger) set_logger(private_log_message);
    }
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
    if (private_enabled()) fprintf(stderr, "PRIVATE_PROPERTY_SET_DELEGATE %s\n",name);
    int result=next ? next(name, value) : -1;
    if (private_enabled()) fprintf(stderr, "PRIVATE_PROPERTY_SET_RESULT %s %d\n",name,result);
    return result;
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
    const char *gate = getenv("LMI_PRIVATE_BINDER_NO_SECCTX");
    if (private_enabled() && gate && !strcmp(gate, "1") &&
        (unsigned)request == BINDER_WRITE_READ && argument) {
        struct binder_write_read *original = argument;
        struct binder_write_read copy = *original;
        if (copy.write_size && copy.write_size <= 65536 && copy.write_buffer &&
            copy.write_consumed <= copy.write_size) {
            unsigned char *commands = malloc(copy.write_size);
            void *owned[64]; size_t owned_count=0, budget=0;
            if (!commands) { errno=ENOMEM; return -1; }
            memcpy(commands, (void *)(uintptr_t)copy.write_buffer, copy.write_size);
            size_t position=copy.write_consumed;
            while (position+sizeof(uint32_t) <= copy.write_size) {
                uint32_t command; memcpy(&command, commands+position, sizeof(command));
                position+=sizeof(command);
                size_t length=_IOC_SIZE(command);
                if (length > copy.write_size-position) break;
                if ((command==BC_TRANSACTION || command==BC_REPLY ||
                     command==BC_TRANSACTION_SG || command==BC_REPLY_SG) &&
                    length >= sizeof(struct binder_transaction_data)) {
                    struct binder_transaction_data transaction;
                    memcpy(&transaction,commands+position,sizeof(transaction));
                    if (transaction.data_size >= sizeof(struct flat_binder_object) &&
                        transaction.data_size <= 1048576 && transaction.data.ptr.buffer &&
                        transaction.offsets_size && transaction.offsets_size <= 4096 &&
                        transaction.offsets_size % sizeof(binder_size_t)==0 &&
                        transaction.data.ptr.offsets && owned_count<64 &&
                        budget+transaction.data_size<=2097152) {
                        unsigned char *data=malloc(transaction.data_size);
                        if (data) {
                            memcpy(data,(void *)(uintptr_t)transaction.data.ptr.buffer,transaction.data_size);
                            const binder_size_t *offsets=(void *)(uintptr_t)transaction.data.ptr.offsets;
                            for (size_t index=0; index<transaction.offsets_size/sizeof(binder_size_t); ++index) {
                                binder_size_t offset; memcpy(&offset,offsets+index,sizeof(offset));
                                if (offset<=transaction.data_size-sizeof(struct flat_binder_object)) {
                                    struct flat_binder_object object;
                                    memcpy(&object,data+offset,sizeof(object));
                                    if (object.hdr.type==BINDER_TYPE_BINDER &&
                                        (object.flags & FLAT_BINDER_FLAG_TXN_SECURITY_CTX)) {
                                        object.flags &= ~FLAT_BINDER_FLAG_TXN_SECURITY_CTX;
                                        memcpy(data+offset,&object,sizeof(object));
                                        fputs("PRIVATE_BINDER_OBJECT_WITHOUT_UNSUPPORTED_SECCTX\n",stderr);
                                    }
                                }
                            }
                            owned[owned_count++]=data; budget+=transaction.data_size;
                            transaction.data.ptr.buffer=(binder_uintptr_t)(uintptr_t)data;
                            memcpy(commands+position,&transaction,sizeof(transaction));
                        }
                    }
                }
                position+=length;
            }
            copy.write_buffer=(binder_uintptr_t)(uintptr_t)commands;
            int result=next(fd,request,&copy);
            int saved_errno=errno;
            original->write_consumed=copy.write_consumed;
            original->read_consumed=copy.read_consumed;
            for (size_t index=0; index<owned_count; ++index) free(owned[index]);
            free(commands); errno=saved_errno; return result;
        }
    }
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
