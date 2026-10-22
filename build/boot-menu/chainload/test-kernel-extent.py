#!/usr/bin/env python3
"""Exercise actual runtime-reservation C against both pinned Image headers."""
from pathlib import Path
import struct,subprocess,tempfile,json
here=Path(__file__).resolve().parent
inputs=Path('/home/linuxagent/lmi-boot-menu-build/inputs')
cases=[]
for name in ['mobian','android']:
    raw=(inputs/(name+'.img')).read_bytes()
    size=struct.unpack_from('<I',raw,8)[0];page=struct.unpack_from('<I',raw,36)[0]
    head=raw[page:page+64]
    assert head[56:60]==b'ARM\x64'
    off,extent=struct.unpack_from('<QQ',head,8)
    oldbytes=((size+2097151)//2097152)*2097152+off
    assert oldbytes-off<extent
    cases.append({'os':name,'file_bytes':size,'image_size':extent,'old_allocation':oldbytes,'old_usable':oldbytes-off,'shortfall':extent-(oldbytes-off)})
c=r'''
#define _POSIX_C_SOURCE 200112L
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
typedef uint64_t UINT64;typedef size_t UINTN;
#define MEM_ALIGN 0x200000u
#define MAX_KERNEL_SIZE 0x4000000u
#define LINUX_ARM64_OFFSET 0x80000u
#define ARCH_ARM64 3
#define ALIGN_VALUE(x,a) (((x)+(a)-1)&~((size_t)(a)-1))
#define EFI_SIZE_TO_PAGES(x) (((x)+4095)/4096)
#define EFI_PAGES_TO_SIZE(x) ((x)*4096)
#define CopyMem memcpy
#define CompareMem memcmp
#define ZeroMem(p,n) memset(p,0,n)
#define tlog_notice(...) ((void)0)
typedef struct {void *address;size_t size,offset,mem_pages,mem_size;int allocated;} linux_file_info;
typedef struct {int arch;linux_file_info kernel;} linux_boot;
static int allocation_fail,free_count;
static void *AllocateAlignedPages(size_t pages,size_t align){
 void *p=NULL;if(allocation_fail)return NULL;
 if(posix_memalign(&p,align,pages*4096))return NULL;return p;
}
static void FreePages(void *p,size_t pages){(void)pages;free_count++;free(p);}
'''+(here/'lmi-kernel-extent.h').read_text()+r'''
static void one(size_t file,size_t extent){
 linux_boot b={0};b.arch=ARCH_ARM64;
 linux_file_info *f=&b.kernel;f->size=file;f->offset=LINUX_ARM64_OFFSET;
 f->mem_pages=EFI_SIZE_TO_PAGES(ALIGN_VALUE(file,MEM_ALIGN)+f->offset);
 f->mem_size=EFI_PAGES_TO_SIZE(f->mem_pages);f->allocated=1;
 unsigned char *old=AllocateAlignedPages(f->mem_pages,MEM_ALIGN);assert(old);
 memset(old,0xa5,f->mem_size);f->address=old+f->offset;
 UINT64 offset=f->offset,ext=extent;
 memcpy((char*)f->address+8,&offset,8);memcpy((char*)f->address+16,&ext,8);
 memcpy((char*)f->address+56,"ARM\x64",4);
 allocation_fail=1;assert(linux_boot_lmi_kernel_extent(&b)==-1);
 assert(f->address==old+f->offset&&free_count==0);allocation_fail=0;
 assert(linux_boot_lmi_kernel_extent(&b)==0&&free_count==1);
 assert(f->mem_size-f->offset>=extent);
 unsigned char *p=f->address;
 for(size_t i=64;i<file;i++)assert(p[i]==0xa5);
 for(size_t i=file;i<extent;i++)assert(p[i]==0);
 assert(linux_boot_lmi_kernel_extent(&b)==0&&free_count==1);
 UINT64 invalid=MAX_KERNEL_SIZE+1ULL;
 memcpy(p+16,&invalid,8);assert(linux_boot_lmi_kernel_extent(&b)==-1);
 memcpy(p+16,&ext,8);p[56]=0;assert(linux_boot_lmi_kernel_extent(&b)==-1);
 free(p-f->offset);free_count=0;
}
int main(void){
'''
for case in cases:c+=f"one({case['file_bytes']}u,{case['image_size']}u);\n"
c+='puts("ACTUAL_ARM64_EXTENT_RESERVATION_PAYLOAD_ZERO_TAIL_FAILURE_AND_REUSE_PASS");return 0;}\n'
with tempfile.TemporaryDirectory(prefix='lmi-extent-') as tmp:
    p=Path(tmp);(p/'test.c').write_text(c)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
print(json.dumps(cases,indent=2))
