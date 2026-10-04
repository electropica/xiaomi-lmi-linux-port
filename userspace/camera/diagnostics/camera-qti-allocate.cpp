/*
 * Direct public QTI BufferManager allocation diagnostic. No camera requests.
 * Descriptor declarations derived from Qualcomm/LF public source:
 * https://android.googlesource.com/platform/hardware/qcom/sm7250/display/+/refs/heads/android12-s2-release/gralloc/gr_buf_descriptor.h
 * Copyright (c) 2016-2018, 2020, The Linux Foundation. All rights reserved.
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *  * Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *  * Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *  * Neither the name of The Linux Foundation nor the names of its
 *    contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
 * IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
 * GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
 * IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
 * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
 * IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * Use only with the inspected vendor library ABI and matching system libc++.so.
 * Binary accesses verified: name0,width24,height28,format32,layers36,usage40,
 * id48,reserved56. Do not replace the vendor handle with a fabricated handle.
 */
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <string>

struct native_handle;
struct private_handle_t;
using buffer_handle_t = const native_handle *;
namespace gralloc {
struct DescriptorAbiCheck;
class BufferDescriptor {
public:
    BufferDescriptor() {}
    explicit BufferDescriptor(uint64_t id) : id_(id) {}
    void SetUsage(uint64_t usage) { usage_ |= usage; }
    void SetDimensions(int w, int h) { width_ = w; height_ = h; }
    void SetColorFormat(int format) { format_ = format; }
    void SetLayerCount(uint32_t count) { layer_count_ = count; }
    void SetName(std::string name) { name_ = name; }
    void SetReservedSize(uint64_t size) { reserved_size_ = size; }
    uint64_t GetUsage() const { return usage_; }
    int GetWidth() const { return width_; }
    int GetHeight() const { return height_; }
    int GetFormat() const { return format_; }
    uint32_t GetLayerCount() const { return layer_count_; }
    uint64_t GetId() const { return id_; }
    uint64_t GetReservedSize() const { return reserved_size_; }
    std::string GetName() const { return name_; }
private:
    std::string name_ = "";
    int width_ = -1;
    int height_ = -1;
    int format_ = -1;
    uint32_t layer_count_ = 1;
    uint64_t usage_ = 0;
    const uint64_t id_ = 0;
    uint64_t reserved_size_ = 0;
    friend struct DescriptorAbiCheck;
};
struct DescriptorAbiCheck {
    static_assert(sizeof(std::string) == 24, "Inspected Android libc++ LP64 string");
    static_assert(sizeof(BufferDescriptor) == 64, "Inspected descriptor size");
    static_assert(offsetof(BufferDescriptor, name_) == 0, "name offset");
    static_assert(offsetof(BufferDescriptor, width_) == 24, "width offset");
    static_assert(offsetof(BufferDescriptor, height_) == 28, "height offset");
    static_assert(offsetof(BufferDescriptor, format_) == 32, "format offset");
    static_assert(offsetof(BufferDescriptor, layer_count_) == 36, "layers offset");
    static_assert(offsetof(BufferDescriptor, usage_) == 40, "usage offset");
    static_assert(offsetof(BufferDescriptor, id_) == 48, "id offset");
    static_assert(offsetof(BufferDescriptor, reserved_size_) == 56, "reserved offset");
};
class BufferManager; // Only vendor singleton pointer; never allocate this class.
}

template <typename T> static T symbol(void *library, const char *name) {
    dlerror();
    void *address = dlsym(library, name);
    const char *error = dlerror();
    if (error || !address) {
        std::fprintf(stderr, "symbol failed %s: %s\n", name, error ? error : "NULL");
        std::_Exit(4);
    }
    return reinterpret_cast<T>(address);
}

int main(int argc, char **argv) {
    const char *path = "/vendor/lib64/libgralloccore.so";
    if (argc == 2) path = argv[1];
    else if (argc != 1) { std::fprintf(stderr, "usage: %s [libgralloccore.so]\n", argv[0]); return 2; }
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    std::printf("stage=dlopen path=%s\n", path);
    void *library = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!library) { std::fprintf(stderr, "dlopen failed: %s\n", dlerror()); return 3; }
    using GetInstance = gralloc::BufferManager *(*)();
    using Allocate = int32_t (*)(gralloc::BufferManager *, const gralloc::BufferDescriptor &,
                                 buffer_handle_t *, unsigned int, bool);
    using Release = int32_t (*)(gralloc::BufferManager *, const private_handle_t *);
    auto instance = symbol<GetInstance>(library, "_ZN7gralloc13BufferManager11GetInstanceEv");
    auto allocate = symbol<Allocate>(library,
        "_ZN7gralloc13BufferManager14AllocateBufferERKNS_16BufferDescriptorEPPK13native_handlejb");
    auto release = symbol<Release>(library,
        "_ZN7gralloc13BufferManager13ReleaseBufferEPK16private_handle_t");
    std::printf("stage=GetInstance\n");
    gralloc::BufferManager *manager = instance();
    std::printf("manager_present=%d\n", manager != nullptr);
    if (!manager) std::_Exit(5);
    int failed = 0;
    {
        gralloc::BufferDescriptor descriptor;
        /* Keep the public std::string name empty, avoiding nonempty string ABI details. */
        descriptor.SetDimensions(32572808, 1);
        descriptor.SetColorFormat(0x21);
        descriptor.SetLayerCount(1);
        descriptor.SetUsage(UINT64_C(0x20003));
        descriptor.SetReservedSize(0);
        buffer_handle_t handle = nullptr;
        std::printf("stage=AllocateBuffer width=32572808 height=1 format=0x21 usage=0x20003 layers=1\n");
        int32_t result = allocate(manager, descriptor, &handle, 0, false);
        std::printf("allocate_result=%d handle_present=%d\n", result, handle != nullptr);
        if (result || !handle) failed = 6;
        else {
            /* Only pass the actual vendor-generated opaque handle back to its allocator. */
            std::printf("stage=ReleaseBuffer\n");
            result = release(manager, reinterpret_cast<const private_handle_t *>(handle));
            std::printf("release_result=%d\n", result);
            if (result) failed = 7;
        }
    }
    std::printf("stage=done result=%d\n", failed);
    /* Singleton and vendor globals remain vendor-owned; bypass process-global destructors. */
    std::_Exit(failed);
}
