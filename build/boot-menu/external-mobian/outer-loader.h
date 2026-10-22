/* SPDX-License-Identifier: MIT
 * Included by aboot.c after the unchanged Android bundle loader.
 */
#include "KernelFdt.h"
#include "outer-range.h"
#include "outer-lock.h"
static int lmi_outer_reserved(const struct lmi_outer_range *r) {
    EFI_MEMORY_DESCRIPTOR *map=NULL,*d;
    UINTN size=0,key=0,stride=0;UINT32 version=0;EFI_STATUS st;int valid=0;
    st=gBS->GetMemoryMap(&size,NULL,&key,&stride,&version);
    if(st!=EFI_BUFFER_TOO_SMALL||!stride||size>1024*1024)return -1;
    size+=stride*8;
    map=AllocatePool(size);if(!map)return -1;
    st=gBS->GetMemoryMap(&size,map,&key,&stride,&version);
    if(!EFI_ERROR(st)&&stride>=sizeof(*d)) {
        UINTN i;
        for(i=0;i+stride<=size;i+=stride) {
            d=(EFI_MEMORY_DESCRIPTOR*)((unsigned char*)map+i);
            if(d->Type==EfiReservedMemoryType&&d->NumberOfPages<=UINT64_MAX/4096&&
               lmi_outer_within(r,d->PhysicalStart,d->NumberOfPages*4096)) {valid=1;break;}
        }
    }
    FreePool(map);return valid?0:-1;
}
static int lmi_outer_source(linux_load_from *from) {
    KERNEL_FDT_PROTOCOL *kfdt=NULL;EFI_STATUS st;struct lmi_outer_range r;
    int node,ns=0,ne=0;const void *a,*b;UINT32 crc=0;
    st=gBS->LocateProtocol(&gKernelFdtProtocolGuid,NULL,(VOID**)&kfdt);
    if(EFI_ERROR(st)||!kfdt||!kfdt->Fdt)return -1;
    node=fdt_path_offset(kfdt->Fdt,"/chosen");if(node<0)return -1;
    a=fdt_getprop(kfdt->Fdt,node,"linux,initrd-start",&ns);
    b=fdt_getprop(kfdt->Fdt,node,"linux,initrd-end",&ne);
    if(lmi_outer_decode(a,ns,b,ne,&r)||r.end-r.start!=LMI_OUTER_BYTES||
       lmi_outer_overlap(&r,0xCE000000ULL,0x02000000ULL)||lmi_outer_reserved(&r))return -1;
    /* Only dereference bytes after proving their range is still reserved. */
    if(EFI_ERROR(gBS->CalculateCrc32((VOID*)(UINTN)r.start,LMI_OUTER_BYTES,&crc))||
       crc!=LMI_OUTER_CRC32)return -1;
    ZeroMem(from,sizeof(*from));from->pointer=(VOID*)(UINTN)r.start;
    from->size=LMI_OUTER_BYTES;return 0;
}
int linux_boot_lmi_external(linux_boot *lb,const char *ident) {
    linux_load_from outer,initrd,cmd;linux_load_from *owned;linux_config *cfg;
    if(!lb||!lb->config||!ident)return -1;
    if(!strcmp(ident,"android"))return linux_boot_lmi_bundle(lb,ident);
    if(strcmp(ident,"mobian"))return -1;
    cfg=lb->config;
    if(lmi_outer_source(&outer)) {
        tlog_error("LMI Mobian input ramdisk absent, unreserved or CRC mismatch");return -1;
    }
    if(lmi_bundle_source(&cfg->kernel,outer.pointer,outer.size,"mobian/kernel")||
       lmi_bundle_source(&cfg->dtb,outer.pointer,outer.size,"mobian/dtb")||
       lmi_bundle_source(&initrd,outer.pointer,outer.size,"mobian/initrd")||
       lmi_bundle_source(&cmd,outer.pointer,outer.size,"mobian/cmdline"))return -1;
    if(cfg->kernel.size>64u*1024*1024||cfg->dtb.size>2u*1024*1024||
       initrd.size>32u*1024*1024||cmd.size<2||cmd.size>=sizeof(cfg->cmdline)-32||
       ((char*)cmd.pointer)[cmd.size-1]||memchr(cmd.pointer,0,cmd.size-1))return -1;
    owned=malloc(sizeof(*owned));if(!owned)return -1;
    CopyMem(owned,&initrd,sizeof(initrd));list_obj_add_new(&cfg->initrd,owned);
    if(!cfg->initrd)return -1;
    CopyMem(cfg->cmdline,cmd.pointer,cmd.size);
    strcat(cfg->cmdline," lmi_menu=outer-v1");
    cfg->use_uefi=false;cfg->arch=ARCH_ARM64;cfg->skip_dtb_after_kernel=true;
    cfg->use_kfdt_ramdisk_abootimg=false;cfg->use_kfdt_ramdisk_kernel=false;
    cfg->screen.update_splash=false;cfg->ignore_dtbo_error=false;
    cfg->skip_kfdt_cmdline=false;cfg->skip_kfdt_memory=false;
    tlog_notice("LMI verified external Mobian components; direct handoff requested");
    return 0;
}
