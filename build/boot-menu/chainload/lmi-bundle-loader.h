/* SPDX-License-Identifier: MIT
 * Included by the pinned src/linux-boot/aboot.c, which already consumes
 * list helpers and EFI boot services. Assets live in a protected FV section.
 */
#include "bundle-format.h"
#include <Pi/PiFirmwareFile.h>
#include <Library/DxeServicesLib.h>
static EFI_GUID lmi_bundle_guid={0x4f9fd886,0x1b54,0x4e6c,{0x9d,0xf8,0x2c,0x64,0x66,0x52,0x12,0x27}};
static void*lmi_bundle_buffer=NULL;
static UINTN lmi_bundle_bytes=0;
static int lmi_bundle_source(linux_load_from*from,const void*b,size_t len,const char*name){
    const void*data=NULL;size_t size=0;uint32_t expected=0;UINT32 actual=0;
    if(lmi_bundle_find(b,len,name,&data,&size,&expected)){
        tlog_error("LMI bundle component absent/invalid: %s",name);return -1;
    }
    if(EFI_ERROR(gBS->CalculateCrc32((VOID*)data,size,&actual))||actual!=expected){
        tlog_error("LMI bundle CRC rejected: %s",name);return -1;
    }
    ZeroMem(from,sizeof(*from));from->enabled=true;from->type=FROM_POINTER;
    from->pointer=(void*)data;from->size=size;return 0;
}
int linux_boot_lmi_bundle(linux_boot*lb,const char*ident){
    EFI_STATUS st;void*b=NULL;size_t len=0;
    linux_load_from initrd,dtbo,cmd;linux_config*cfg;
    linux_load_from*initrd_owned=NULL,*dtbo_owned=NULL;
    if(!lb||!lb->config||strcmp(ident,"android"))return -1;
    cfg=lb->config;
    if(!lmi_bundle_buffer){
        st=GetSectionFromAnyFv(&lmi_bundle_guid,EFI_SECTION_RAW,0,&lmi_bundle_buffer,&lmi_bundle_bytes);
        if(EFI_ERROR(st)||!lmi_bundle_buffer){
            tlog_error("LMI FV asset lookup failed: %s",efi_status_to_string(st));return -1;
        }
    }
    b=lmi_bundle_buffer;len=lmi_bundle_bytes;
    if(lmi_bundle_source(&cfg->kernel,b,len,"android/kernel")||
       lmi_bundle_source(&cfg->dtb,b,len,"android/dtb")||
       lmi_bundle_source(&initrd,b,len,"android/initrd")||
       lmi_bundle_source(&dtbo,b,len,"android/dtbo")||
       lmi_bundle_source(&cmd,b,len,"android/cmdline"))return -1;
    if(cfg->kernel.size>64u*1024u*1024u||cfg->dtb.size>2u*1024u*1024u||
       initrd.size>32u*1024u*1024u||dtbo.size>24u*1024u*1024u||
       cmd.size>sizeof(cfg->cmdline)||cmd.size<2||
       ((char*)cmd.pointer)[cmd.size-1]!=0||memchr(cmd.pointer,0,cmd.size-1))return -1;
    initrd_owned=malloc(sizeof(*initrd_owned));dtbo_owned=malloc(sizeof(*dtbo_owned));
    if(!initrd_owned||!dtbo_owned){free(initrd_owned);free(dtbo_owned);return -1;}
    CopyMem(initrd_owned,&initrd,sizeof(initrd));CopyMem(dtbo_owned,&dtbo,sizeof(dtbo));
    list_obj_add_new(&cfg->initrd,initrd_owned);list_obj_add_new(&cfg->dtbo,dtbo_owned);
    if(!cfg->initrd||!cfg->dtbo)return -1;
    CopyMem(cfg->cmdline,cmd.pointer,cmd.size);
    cfg->use_uefi=false;cfg->arch=ARCH_ARM64;cfg->skip_dtb_after_kernel=true;
    cfg->use_kfdt_ramdisk_abootimg=false;cfg->use_kfdt_ramdisk_kernel=false;
    cfg->screen.update_splash=false;cfg->ignore_dtbo_error=false;
    /* Keep ABL's dynamic boot arguments and memory information. The exact
     * pinned image command line is additionally supplied through cfg->cmdline.
     * Qualcomm DTB/DTBO matching uses the upstream hardware-info protocols. */
    cfg->skip_kfdt_cmdline=false;cfg->skip_kfdt_memory=false;
    tlog_notice("LMI bundle verified; attempting experimental LineageOS handoff");
    return 0;
}
