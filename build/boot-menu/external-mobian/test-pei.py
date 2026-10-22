#!/usr/bin/env python3
"""Replay actual reservation code with mocked HOB and FDT services."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
program=r'''
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#define STATIC static
#define VOID void
typedef uint64_t UINT64;
typedef void fdt;
enum {AddMem=1,EFI_RESOURCE_SYSTEM_MEMORY=2,EfiConventionalMemory=3,EfiReservedMemoryType=4};
typedef struct {uint64_t Address,Length;int HobOption,ResourceType,MemoryType;} ARM_MEMORY_REGION_DESCRIPTOR_EX,*PARM_MEMORY_REGION_DESCRIPTOR_EX;
static ARM_MEMORY_REGION_DESCRIPTOR_EX descriptors[]={
 {0xb0190000,0x0fe70000,AddMem,EFI_RESOURCE_SYSTEM_MEMORY,EfiConventionalMemory},{0,0,0,0,0}};
static ARM_MEMORY_REGION_DESCRIPTOR_EX emitted[8];static unsigned count;
static unsigned char start[]={0,0,0,0,0xb8,0,0,1},end[]={0,0,0,0,0xbb,0,0,2};
static int malformed;
static PARM_MEMORY_REGION_DESCRIPTOR_EX GetPlatformMemoryMap(void){return descriptors;}
static void AddHob(PARM_MEMORY_REGION_DESCRIPTOR_EX p){assert(count<8);emitted[count++]=*p;}
static void CpuDeadLoop(void){abort();}
static int fdt_path_offset(fdt *f,const char *p){(void)f;(void)p;return 0;}
static const void *fdt_getprop(fdt *f,int n,const char *p,int *len){
 (void)f;(void)n;*len=malformed?3:8;
 return strstr(p,"start")?start:end;
}
#include "outer-pei.h"
int main(void){
 LmiFindOuter(NULL,0x9ff00000,0x100000);
 assert(LmiOuter.start==0xb8000001ULL);
 LmiAddProtectedHob(descriptors);
 assert(count==3);
 assert(emitted[0].Address==descriptors[0].Address);
 assert(emitted[0].Address+emitted[0].Length==emitted[1].Address);
 assert(emitted[1].MemoryType==EfiReservedMemoryType);
 assert(emitted[1].Address==0xb8000000&&emitted[1].Length==0x03001000);
 assert(emitted[1].Address+emitted[1].Length==emitted[2].Address);
 assert(emitted[2].Address+emitted[2].Length==descriptors[0].Address+descriptors[0].Length);
 count=0;LmiFindOuter(NULL,0xb8000000,0x4000000);assert(!LmiOuter.start);
 LmiAddProtectedHob(descriptors);assert(count==1&&emitted[0].Length==descriptors[0].Length);
 malformed=1;LmiFindOuter(NULL,0x9ff00000,0x100000);assert(!LmiOuter.start);
 malformed=0;descriptors[0].MemoryType=EfiReservedMemoryType;
 LmiFindOuter(NULL,0x9ff00000,0x100000);assert(!LmiOuter.start);
 puts("ACTUAL_PEI_HOB_SPLIT_NONOVERLAP_RESERVED_TYPE_AND_REJECTION_PASS");
}
'''
with tempfile.TemporaryDirectory(prefix='lmi-outer-pei-') as tmp:
    p=Path(tmp);(p/'test.c').write_text(program)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I',str(here),str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
