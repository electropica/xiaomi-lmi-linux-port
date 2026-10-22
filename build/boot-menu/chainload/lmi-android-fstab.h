/* SPDX-License-Identifier: MIT
 * Included by aboot.c. Modify only the RAM DT passed to pinned Android.
 */
#include "variant-args.h"
int linux_boot_lmi_variant(linux_boot *lb){
    int chosen,len;const char *original;char args[4096];
    if(!lb||!lb->config||!lb->dtb.address)return -1;
    if(strcmp(lb->config->tag,"android")&&strcmp(lb->config->tag,"mobian"))return -1;
    chosen=fdt_path_offset(lb->dtb.address,"/chosen");if(chosen<0)return -1;
    if(fdt_setprop_string(lb->dtb.address,chosen,"lmi,menu-os",lb->config->tag))return -1;
    original=fdt_getprop(lb->dtb.address,chosen,"bootargs",&len);
    if(!original||len<=0||(size_t)len>sizeof(args)||original[len-1]!=0)return -1;
    memcpy(args,original,(size_t)len);
    if(lmi_variant_args(args,(size_t)len))return -1;
    if(!strcmp(args,original))return 0;
    return fdt_setprop_string(lb->dtb.address,chosen,"bootargs",args);
}
int linux_boot_lmi_android_fstab(linux_boot *lb){
    int node,vendor,len,r;
    const char *compatible,*dev;
    static const char legacy_vendor[]="/dev/block/platform/soc/1d84000.ufshc/by-name/vendor";
    if(!lb||!lb->config||!lb->dtb.address)return -1;
    /* Mobian uses its exact pinned DT and initramfs, never Android surgery. */
    if(!strcmp(lb->config->tag,"mobian"))return 0;
    if(strcmp(lb->config->tag,"android"))return -1;
    if(fdt_check_header(lb->dtb.address))return -1;
    node=fdt_path_offset(lb->dtb.address,"/firmware/android/fstab");
    if(node==-FDT_ERR_NOTFOUND)return 0;
    if(node<0)return -1;
    compatible=fdt_getprop(lb->dtb.address,node,"compatible",&len);
    if(!compatible||len!=sizeof("android,fstab")||memcmp(compatible,"android,fstab",sizeof("android,fstab"))){
        tlog_error("LMI: unexpected DT fstab compatibility; refusing removal");return -1;
    }
    vendor=fdt_subnode_offset(lb->dtb.address,node,"vendor");
    if(vendor<0)return -1;
    dev=fdt_getprop(lb->dtb.address,vendor,"dev",&len);
    if(!dev||len!=sizeof(legacy_vendor)||memcmp(dev,legacy_vendor,sizeof(legacy_vendor))){
        tlog_error("LMI: unexpected DT vendor path; refusing removal");return -1;
    }
    /* AOSP dynamic partitions require the ramdisk's logical fstab. The
     * legacy DT table takes precedence and incorrectly waits for physical
     * system/vendor partitions. Leave AVB policy, ramdisk and GPT intact. */
    r=fdt_del_node(lb->dtb.address,node);
    if(r){tlog_error("LMI: remove legacy DT fstab failed: %s",fdt_strerror(r));return -1;}
    if(fdt_path_offset(lb->dtb.address,"/firmware/android/fstab")!=-FDT_ERR_NOTFOUND)return -1;
    lb->dtb.size=fdt_totalsize(lb->dtb.address);
    tlog_notice("LMI: legacy DT fstab removed in RAM; use pinned Android logical ramdisk fstab");
    return 0;
}
