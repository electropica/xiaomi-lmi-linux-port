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

#include <cerrno>
#include <climits>
#include <pthread.h>

/* Private handle stays opaque. Public packed4 prefix proves base offset84:
 * native_handle header12, fds8, magic/flags8, width/height/uw/uh/format/type/layers28,
 * id/usage16,size/offset/metaoffset12 => base84. Vendor LockBuffer@0xab6c and
 * @0xabc8 read/map that exact field; AllocateBuffer allocates112,header12/2/23.
 * Public source: platform/hardware/qcom/sdm845/display/gralloc/gr_priv_handle.h.
 * Read via memcpy only for handles created and tracked by this bridge.
 */
namespace {
using GetInstance = gralloc::BufferManager *(*)();
using Allocate = int32_t (*)(gralloc::BufferManager *, const gralloc::BufferDescriptor &,
                             buffer_handle_t *, unsigned int, bool);
using Release = int32_t (*)(gralloc::BufferManager *, const private_handle_t *);
using Lock = int32_t (*)(gralloc::BufferManager *, const private_handle_t *, uint64_t);
using Unlock = int32_t (*)(gralloc::BufferManager *, const private_handle_t *);
struct Entry { const void *handle; bool locked; };
Entry entries[64] = {};
pthread_mutex_t bridge_mutex = PTHREAD_MUTEX_INITIALIZER;
void *core_library;
gralloc::BufferManager *manager;
Allocate allocate_buffer;
Release release_buffer;
Lock lock_buffer;
Unlock unlock_buffer;

int initialize() {
    if (manager) return 0;
    if (!core_library) core_library = dlopen("/vendor/lib64/libgralloccore.so", RTLD_NOW | RTLD_LOCAL);
    if (!core_library) return -ENOENT;
    auto get = reinterpret_cast<GetInstance>(dlsym(core_library,
        "_ZN7gralloc13BufferManager11GetInstanceEv"));
    allocate_buffer = reinterpret_cast<Allocate>(dlsym(core_library,
        "_ZN7gralloc13BufferManager14AllocateBufferERKNS_16BufferDescriptorEPPK13native_handlejb"));
    release_buffer = reinterpret_cast<Release>(dlsym(core_library,
        "_ZN7gralloc13BufferManager13ReleaseBufferEPK16private_handle_t"));
    lock_buffer = reinterpret_cast<Lock>(dlsym(core_library,
        "_ZN7gralloc13BufferManager10LockBufferEPK16private_handle_tm"));
    unlock_buffer = reinterpret_cast<Unlock>(dlsym(core_library,
        "_ZN7gralloc13BufferManager12UnlockBufferEPK16private_handle_t"));
    if (!get || !allocate_buffer || !release_buffer || !lock_buffer || !unlock_buffer) return -ENOSYS;
    manager = get();
    return manager ? 0 : -ENODEV;
}
Entry *find_entry(const void *handle) {
    if (!handle) return nullptr;
    for (auto &entry : entries) if (entry.handle == handle) return &entry;
    return nullptr;
}
bool valid_handle_header(const void *handle) {
    int32_t header[3];
    uint32_t magic;
    std::memcpy(header, handle, sizeof(header));
    std::memcpy(&magic, static_cast<const unsigned char *>(handle) + 20, sizeof(magic));
    return header[0] == 12 && header[1] == 2 && header[2] == 23 &&
           magic == UINT32_C(0x676d736d);
}
struct Guard {
    Guard() { pthread_mutex_lock(&bridge_mutex); }
    ~Guard() { pthread_mutex_unlock(&bridge_mutex); }
};
}

static int allocate_format(uint32_t width,uint32_t height,int format,uint64_t usage,const void **handle) {
    if (!handle) return -EINVAL;
    *handle = nullptr;
    if (!width || !height || width>INT_MAX || height>INT_MAX) return -EINVAL;
    Guard guard;
    Entry *free_entry = nullptr;
    for (auto &entry : entries) if (!entry.handle) { free_entry = &entry; break; }
    if (!free_entry) return -ENOSPC;
    int result = initialize();
    if (result) return result;
    gralloc::BufferDescriptor descriptor;
    descriptor.SetDimensions(static_cast<int>(width),static_cast<int>(height));
    descriptor.SetColorFormat(format);
    descriptor.SetLayerCount(1);
    descriptor.SetUsage(usage);
    descriptor.SetReservedSize(0);
    buffer_handle_t vendor_handle = nullptr;
    result = allocate_buffer(manager, descriptor, &vendor_handle, 0, false);
    if (result) return result;
    if (!vendor_handle) return -EIO;
    free_entry->handle = vendor_handle;
    free_entry->locked = false;
    *handle = vendor_handle;
    return 0;
}

extern "C" int lmi_qti_allocate(uint32_t bytes,uint64_t usage,const void **handle) {
    return allocate_format(bytes,1,0x21,usage,handle);
}
extern "C" int lmi_qti_allocate_yuv(uint32_t width,uint32_t height,uint64_t usage,const void **handle) {
    if(width>4096 || height>4096)return -EINVAL;
    return allocate_format(width,height,0x23,usage,handle);
}

extern "C" int lmi_qti_release(const void *handle) {
    Guard guard;
    Entry *entry = find_entry(handle);
    if (!entry) return -EINVAL;
    if (entry->locked) return -EBUSY;
    int result = release_buffer(manager, static_cast<const private_handle_t *>(handle));
    if (!result) *entry = {};
    return result;
}

extern "C" int lmi_qti_lock(const void *handle, void **address) {
    if (!address) return -EINVAL;
    *address = nullptr;
    Guard guard;
    Entry *entry = find_entry(handle);
    if (!entry) return -EINVAL;
    if (entry->locked) return -EBUSY;
    // Guard ABI before reading the vendor's mapped base; native_handle header is public.
    if (!valid_handle_header(handle)) return -EPROTO;
    int result = lock_buffer(manager, static_cast<const private_handle_t *>(handle), UINT64_C(3));
    if (result) return result;
    entry->locked = true;
    uint64_t base = 0;
    std::memcpy(&base, static_cast<const unsigned char *>(handle) + 84, sizeof(base));
    if (!base) {
        result = unlock_buffer(manager, static_cast<const private_handle_t *>(handle));
        if (!result) entry->locked = false;
        return result ? result : -EIO;
    }
    *address = reinterpret_cast<void *>(static_cast<uintptr_t>(base));
    return 0;
}
extern "C" int lmi_qti_lock_cpu(const void *handle, void **address) {
    return lmi_qti_lock(handle, address);
}
extern "C" int lmi_qti_unlock(const void *handle) {
    Guard guard;
    Entry *entry = find_entry(handle);
    if (!entry || !entry->locked) return -EINVAL;
    int result = unlock_buffer(manager, static_cast<const private_handle_t *>(handle));
    if (!result) entry->locked = false;
    return result;
}

extern "C" int lmi_qti_get_capacity(const void *handle, uint32_t *capacity) {
    if (!capacity) return -EINVAL;
    *capacity = 0;
    Guard guard;
    if (!find_entry(handle)) return -EINVAL;
    if (!valid_handle_header(handle)) return -EPROTO;
    /* Public packed4 size/offset fields; actual vendor LockBuffer loads these
     * at0xab84 and passes size/offset to MapBuffer at0xabd4. AllocateBuffer
     * stores size at0xb3c4 and zeroes offset at0xb3d0. No guessed capacity.
     */
    uint32_t size = 0, offset = 0;
    std::memcpy(&size, static_cast<const unsigned char *>(handle) + 72, sizeof(size));
    std::memcpy(&offset, static_cast<const unsigned char *>(handle) + 76, sizeof(offset));
    if (offset || !size || size > 128U * 1024U * 1024U) return -EPROTO;
    *capacity = size;
    return 0;
}

// Public Android LP64 android_ycbcr ABI; inspected OEM grallocutils symbol.
struct android_ycbcr {
    void *y, *cb, *cr;
    size_t ystride, cstride, chroma_step;
    uint32_t reserved[8];
};
static_assert(sizeof(android_ycbcr)==80, "Android LP64 YCbCr ABI");
extern "C" int lmi_qti_save_ppm(const void *handle,uint32_t width,uint32_t height,const char *path) {
    if (!path || !width || !height || width>4096 || height>4096 || width%2 || height%2) return -EINVAL;
    Guard guard;
    Entry *entry=find_entry(handle);
    if (!entry || !entry->locked || !valid_handle_header(handle)) return -EINVAL;
    using Layout=int (*)(const private_handle_t *,android_ycbcr *);
    auto layout=reinterpret_cast<Layout>(dlsym(core_library,"_ZN7gralloc15GetYUVPlaneInfoEPK16private_handle_tP13android_ycbcr"));
    if (!layout) return -ENOSYS;
    android_ycbcr planes[2]={};
    int result=layout(static_cast<const private_handle_t *>(handle),planes);
    if(result)return result;
    uint32_t capacity=0; uint64_t base=0;
    std::memcpy(&capacity,static_cast<const unsigned char *>(handle)+72,4);
    std::memcpy(&base,static_cast<const unsigned char *>(handle)+84,8);
    auto &p=planes[0];
    if(!capacity || capacity>128U*1024U*1024U || !base || p.ystride<width ||
       p.cstride<(width/2-1)*p.chroma_step+1 || (p.chroma_step!=1 && p.chroma_step!=2))return -EPROTO;
    auto span=[&](void *pointer,size_t stride,uint32_t rows,uint64_t columns){
        uint64_t start=reinterpret_cast<uintptr_t>(pointer);
        return start>=base && start-base<capacity && stride<=capacity &&
               (uint64_t)(rows-1)*stride+columns<=capacity-(start-base);
    };
    uint64_t columns=(uint64_t)(width/2-1)*p.chroma_step+1;
    if(!span(p.y,p.ystride,height,width)||!span(p.cb,p.cstride,height/2,columns)||!span(p.cr,p.cstride,height/2,columns))return -EPROTO;
    printf("yuv_layout width=%u height=%u ystride=%zu cstride=%zu step=%zu yoffset=%llu cboffset=%llu croffset=%llu\n",width,height,p.ystride,p.cstride,p.chroma_step,
       (unsigned long long)(reinterpret_cast<uintptr_t>(p.y)-base),(unsigned long long)(reinterpret_cast<uintptr_t>(p.cb)-base),(unsigned long long)(reinterpret_cast<uintptr_t>(p.cr)-base));
    FILE *file=fopen(path,"wb"); if(!file)return -errno;
    fprintf(file,"P6\n%u %u\n255\n",width,height);
    auto clamp=[](int x){return (unsigned char)(x<0?0:(x>255?255:x));};
    auto *row=static_cast<unsigned char *>(std::malloc((size_t)width*3));
    if(!row){fclose(file);return -ENOMEM;}
    // Diagnostic BT.601 limited-range rendering; colorimetry is not calibrated.
    for(uint32_t y=0;y<height && !result;y++){
        for(uint32_t x=0;x<width;x++){
            int l=static_cast<unsigned char *>(p.y)[y*p.ystride+x]-16;
            int u=static_cast<unsigned char *>(p.cb)[(y/2)*p.cstride+(x/2)*p.chroma_step]-128;
            int v=static_cast<unsigned char *>(p.cr)[(y/2)*p.cstride+(x/2)*p.chroma_step]-128;
            row[3*x]=clamp((298*l+409*v+128)>>8);
            row[3*x+1]=clamp((298*l-100*u-208*v+128)>>8);
            row[3*x+2]=clamp((298*l+516*u+128)>>8);
        }
        if(fwrite(row,3,width,file)!=width)result=-EIO;
    }
    std::free(row); if(fclose(file) && !result)result=-EIO;
    return result;
}
