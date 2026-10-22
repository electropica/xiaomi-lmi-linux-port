#!/usr/bin/env python3
"""Replay exact loader source checks: no payload read before reservation proof."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent;text=(here/'outer-loader.h').read_text()
def function(signature):
    start=text.index(signature);i=text.index('{',start)+1;depth=1
    while depth:depth+=(text[i]=='{')-(text[i]=='}');i+=1
    return text[start:i]
prefix=r'''
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "outer-range.h"
typedef void VOID;typedef size_t UINTN;typedef uint32_t UINT32;typedef unsigned EFI_STATUS;
#define EFI_BUFFER_TOO_SMALL 1
#define EFI_ERROR(s) ((s)!=0)
#define EfiReservedMemoryType 4
#define LMI_OUTER_BYTES 16u
#define LMI_OUTER_CRC32 0x12345678u
#define ZeroMem(p,n) memset(p,0,n)
typedef struct {unsigned Type;uint64_t PhysicalStart,NumberOfPages;} EFI_MEMORY_DESCRIPTOR;
typedef struct {void *Fdt;} KERNEL_FDT_PROTOCOL;
typedef struct {void *pointer;size_t size;} linux_load_from;
static unsigned char *payload,start[8],end[8];
static unsigned crc_calls;static int reserved=1,wrong_crc,wrong_size;
static KERNEL_FDT_PROTOCOL kfdt={(void*)1};static int gKernelFdtProtocolGuid;
static void *AllocatePool(size_t n){return malloc(n);}
static void FreePool(void *p){free(p);}
static EFI_STATUS getmap(UINTN *size,EFI_MEMORY_DESCRIPTOR *map,UINTN *key,UINTN *stride,UINT32 *version){
 (void)key;(void)version;*stride=sizeof(*map);
 if(!map){*size=sizeof(*map);return EFI_BUFFER_TOO_SMALL;}
 *size=sizeof(*map);map->Type=reserved?EfiReservedMemoryType:7;
 map->PhysicalStart=(uintptr_t)payload&~4095ULL;map->NumberOfPages=2;return 0;
}
static EFI_STATUS locate(void *guid,void *registration,void **result){
 (void)registration;assert(guid==&gKernelFdtProtocolGuid);*result=&kfdt;return 0;
}
static EFI_STATUS crc(void *p,UINTN n,UINT32 *out){
 assert(reserved&&p==payload&&n==LMI_OUTER_BYTES);++crc_calls;
 *out=wrong_crc?0:LMI_OUTER_CRC32;return 0;
}
static struct {EFI_STATUS (*GetMemoryMap)(UINTN*,EFI_MEMORY_DESCRIPTOR*,UINTN*,UINTN*,UINT32*);
 EFI_STATUS (*LocateProtocol)(void*,void*,void**);
 EFI_STATUS (*CalculateCrc32)(void*,UINTN,UINT32*);} services={getmap,locate,crc},*gBS=&services;
static int fdt_path_offset(void *f,const char *path){(void)f;(void)path;return 0;}
static const void *fdt_getprop(void *f,int node,const char *name,int *len){
 (void)f;(void)node;*len=wrong_size?3:8;return strstr(name,"start")?start:end;
}
static void be64(unsigned char *p,uint64_t n){for(unsigned i=0;i<8;i++)p[7-i]=(unsigned char)(n>>(8*i));}
'''
suffix=r'''
int main(void){
 linux_load_from from={0};payload=malloc(4096);assert(payload);
 be64(start,(uintptr_t)payload);be64(end,(uintptr_t)payload+LMI_OUTER_BYTES);
 assert(!lmi_outer_source(&from)&&from.pointer==payload&&from.size==LMI_OUTER_BYTES&&crc_calls==1);
 reserved=0;crc_calls=0;assert(lmi_outer_source(&from)&&crc_calls==0);
 reserved=1;wrong_size=1;assert(lmi_outer_source(&from)&&crc_calls==0);
 wrong_size=0;wrong_crc=1;assert(lmi_outer_source(&from)&&crc_calls==1);
 free(payload);puts("ACTUAL_OUTER_LOADER_RESERVATION_BEFORE_PAYLOAD_CRC_AND_REJECTION_PASS");
}
'''
with tempfile.TemporaryDirectory(prefix='lmi-outer-loader-') as tmp:
    p=Path(tmp);(p/'test.c').write_text(prefix+function('static int lmi_outer_reserved(')+function('static int lmi_outer_source(')+suffix)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I',str(here),str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
