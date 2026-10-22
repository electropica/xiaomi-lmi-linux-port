/* SPDX-License-Identifier: MIT
 * Reserve the complete ARM64 Image runtime extent, including its zeroed tail.
 * Included by aboot.c; called after decompression, before DT/initrd finalization.
 */
int linux_boot_lmi_kernel_extent(linux_boot *lb){
    linux_file_info *fi;UINT64 offset,extent;UINTN span,pages,bytes;
    unsigned char *base;
    if(!lb||lb->arch!=ARCH_ARM64)return -1;
    fi=&lb->kernel;
    if(!fi->address||fi->size<64||
       CompareMem((unsigned char*)fi->address+56,"ARM\x64",4))return -1;
    CopyMem(&offset,(unsigned char*)fi->address+8,sizeof(offset));
    CopyMem(&extent,(unsigned char*)fi->address+16,sizeof(extent));
    /* These pinned kernels are LE, non-legacy Images with a 512-KiB offset. */
    if(!extent||extent>MAX_KERNEL_SIZE||fi->size>MAX_KERNEL_SIZE||
       offset!=LINUX_ARM64_OFFSET||fi->offset!=offset||!fi->allocated||
       ((UINTN)fi->address-fi->offset)%MEM_ALIGN)return -1;
    span=(UINTN)extent>fi->size?(UINTN)extent:fi->size;
    if(fi->mem_size>=fi->offset&&fi->mem_size-fi->offset>=span)return 0;
    pages=EFI_SIZE_TO_PAGES(ALIGN_VALUE(span,MEM_ALIGN)+fi->offset);
    bytes=EFI_PAGES_TO_SIZE(pages);
    base=AllocateAlignedPages(pages,MEM_ALIGN);
    if(!base)return -1;
    ZeroMem(base,bytes);
    CopyMem(base+fi->offset,fi->address,fi->size);
    FreePages(fi->address-fi->offset,fi->mem_pages);
    fi->address=base+fi->offset;fi->mem_pages=pages;fi->mem_size=bytes;
    tlog_notice("LMI: reserved complete ARM64 Image extent: %llu bytes (file %zu)",
                (unsigned long long)extent,fi->size);
    return 0;
}
