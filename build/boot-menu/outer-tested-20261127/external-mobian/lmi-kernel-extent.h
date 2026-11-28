/* SPDX-License-Identifier: MIT
 * Reserve the complete ARM64 Image runtime extent, including its zeroed tail.
 * Included by aboot.c; called after decompression, before DT/initrd finalization.
 *
 * ISOLATED PROPOSAL (not applied to the shared tree).
 * Change: accept a modern mainline Image whose header declares text_offset 0,
 * in addition to the pinned legacy layout (text_offset 0x80000).
 *
 * Why more than the test has to change:
 *   src/linux-boot/aboot.c:30-31 and src/linux-boot/loader.c:307-308 set
 *   lb->kernel.offset from the ARCHITECTURE, not from the Image header:
 *       case ARCH_ARM64: lb->kernel.offset=LINUX_ARM64_OFFSET; break;
 *   The Image is therefore loaded at base+0x80000 while a modern header says
 *   text_offset 0. Upstream requires the Image to be placed text_offset bytes
 *   from a 2 MiB aligned base (Documentation/arch/arm64/booting.rst:138-146);
 *   with text_offset 0 the Image must finally sit ON a 2 MiB aligned address.
 *   Accepting the header offset alone would therefore leave the Image at a
 *   512-KiB-misaligned address while claiming offset 0.
 *
 * Legacy behaviour (text_offset 0x80000) is preserved bit for bit: same
 * refusals, same re-allocation trigger, same placement at base+0x80000.
 */
int linux_boot_lmi_kernel_extent(linux_boot *lb){
    linux_file_info *fi;UINT64 offset,extent;UINTN span,pages,bytes;
    unsigned char *base;bool legacy,rebase;
    if(!lb||lb->arch!=ARCH_ARM64)return -1;
    fi=&lb->kernel;
    if(!fi->address||fi->size<64||
       CompareMem((unsigned char*)fi->address+56,"ARM\x64",4))return -1;
    CopyMem(&offset,(unsigned char*)fi->address+8,sizeof(offset));
    CopyMem(&extent,(unsigned char*)fi->address+16,sizeof(extent));
    /* Legacy: "These pinned kernels are LE, non-legacy Images with a 512-KiB
       offset." Modern: upstream v7.3 head.S writes .quad 0 for the load offset. */
    legacy=(offset==LINUX_ARM64_OFFSET);
    if(!legacy&&offset!=0)return -1;
    if(!extent||extent>MAX_KERNEL_SIZE||fi->size>MAX_KERNEL_SIZE||!fi->allocated)return -1;
    if(legacy&&(fi->offset!=offset||((UINTN)fi->address-fi->offset)%MEM_ALIGN))return -1;
    span=(UINTN)extent>fi->size?(UINTN)extent:fi->size;
    rebase=false;
    if(!legacy){
        /* Modern Image: the loader placed it at base+LINUX_ARM64_OFFSET. It has
           to end on a 2 MiB aligned base with text_offset 0. */
        if(fi->offset!=0||((UINTN)fi->address)%MEM_ALIGN)rebase=true;
    }
    if(fi->mem_size<fi->offset||fi->mem_size-fi->offset<span)rebase=true;
    if(!rebase)return 0;
    pages=EFI_SIZE_TO_PAGES(ALIGN_VALUE(span,MEM_ALIGN)+offset);
    bytes=EFI_PAGES_TO_SIZE(pages);
    base=AllocateAlignedPages(pages,MEM_ALIGN);
    if(!base)return -1;
    ZeroMem(base,bytes);
    CopyMem(base+offset,fi->address,fi->size);
    FreePages(fi->address-fi->offset,fi->mem_pages);
    fi->address=base+offset;fi->offset=offset;fi->mem_pages=pages;fi->mem_size=bytes;
    tlog_notice("LMI: reserved complete ARM64 Image extent: %llu bytes (file %zu, offset %llu)",
                (unsigned long long)extent,fi->size,(unsigned long long)offset);
    return 0;
}
