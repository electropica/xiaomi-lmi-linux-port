"""Exercise the exact firmware extent helper with host memory-service stubs."""
from pathlib import Path
import json
import subprocess
import tempfile

recipe = Path(__file__).resolve().parent
prefix = r'''
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef uint64_t UINT64; typedef size_t UINTN;
typedef struct {void *address;size_t size,offset,mem_size,mem_pages;int allocated;} linux_file_info;
typedef struct {int arch;linux_file_info kernel;} linux_boot;
#define ARCH_ARM64 1
#define MEM_ALIGN 0x200000u
#define LINUX_ARM64_OFFSET 0x80000u
#define MAX_KERNEL_SIZE 0x4000000u
#define ALIGN_VALUE(n,a) (((n)+(a)-1)&~((a)-1))
#define EFI_SIZE_TO_PAGES(n) (((n)+4095)/4096)
#define EFI_PAGES_TO_SIZE(n) ((n)*4096)
#define CompareMem memcmp
#define CopyMem memcpy
#define ZeroMem(p,n) memset(p,0,n)
#define tlog_notice(...) ((void)0)
static int fail_alloc,calls,frees;
static void *AllocateAlignedPages(size_t pages,size_t align){
 ++calls;if(fail_alloc)return NULL;return aligned_alloc(align,ALIGN_VALUE(pages*4096,align));
}
static void FreePages(void *p,size_t pages){(void)pages;++frees;free(p);}
'''
suffix = r'''
static void check(size_t file,size_t extent){
 linux_boot lb={0};lb.arch=ARCH_ARM64;
 linux_file_info *f=&lb.kernel;
 size_t offset=LINUX_ARM64_OFFSET;
 f->size=file;f->offset=offset;f->allocated=1;
 f->mem_size=ALIGN_VALUE(file,MEM_ALIGN)+offset;f->mem_pages=f->mem_size/4096;
 unsigned char *base=AllocateAlignedPages(f->mem_pages,MEM_ALIGN);assert(base);
 memset(base,0x5a,f->mem_size);f->address=base+offset;
 memcpy((char*)f->address+8,&offset,8);memcpy((char*)f->address+16,&extent,8);
 memcpy((char*)f->address+56,"ARM\x64",4);
 size_t old_pages=f->mem_pages;void *old=f->address;
 fail_alloc=1;assert(linux_boot_lmi_kernel_extent(&lb)==-1);
 assert(f->address==old&&f->mem_pages==old_pages);fail_alloc=0;
 int free_before=frees;assert(linux_boot_lmi_kernel_extent(&lb)==0);
 assert(frees==free_before+1);assert(f->mem_size-f->offset>=extent);
 assert(((char*)f->address)[100]==0x5a);
 for(size_t i=file;i<extent;i++)assert(((unsigned char*)f->address)[i]==0);
 int before=calls;assert(linux_boot_lmi_kernel_extent(&lb)==0&&calls==before);
 ((char*)f->address)[56]=0;assert(linux_boot_lmi_kernel_extent(&lb)==-1);
 FreePages((char*)f->address-f->offset,f->mem_pages);
}
int main(void){
 check(45359128,56758272);check(53456920,64811008);
 puts("BOTH_PINNED_KERNEL_EXTENTS_COPY_ZERO_TAIL_IDEMPOTENCE_AND_ALLOCATION_FAILURE_PASS");
}
'''
with tempfile.TemporaryDirectory(prefix='lmi-dual-extent-') as temp:
    temp = Path(temp)
    source = temp/'test.c'
    source.write_text(prefix+(recipe/'lmi-kernel-extent.h').read_text()+suffix)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(source),'-o',str(temp/'test')],check=True)
    subprocess.run([str(temp/'test')],check=True)
print(json.dumps({'firmware_build':False,'phone_contact':False,'scope':'exact helper, host EFI allocation stubs; not handset validation'}))
