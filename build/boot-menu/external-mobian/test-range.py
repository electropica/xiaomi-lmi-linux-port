#!/usr/bin/env python3
"""Exercise the exact PEI/loader span parser, not a Python reimplementation."""
from pathlib import Path
import subprocess,tempfile
header=Path(__file__).with_name('outer-range.h')
c=r'''
#include <assert.h>
#include <stdio.h>
#include "outer-range.h"
int main(void) {
 struct lmi_outer_range r;
 unsigned char a[]={0,0,0,0,0xb8,0,0,1}, b[]={0,0,0,0,0xbb,0,0,2};
 assert(!lmi_outer_decode(a,8,b,8,&r));
 assert(r.start==0xb8000001ULL&&r.end==0xbb000002ULL);
 assert(r.page_start==0xb8000000ULL&&r.page_end==0xbb001000ULL);
 assert(!lmi_outer_decode(a+4,4,b+4,4,&r));
 assert(lmi_outer_within(&r,0xb0190000,0x0fe70000));
 assert(!lmi_outer_within(&r,0xb8001000,0x10000000));
 assert(!lmi_outer_overlap(&r,0xce000000,0x02000000));
 assert(lmi_outer_overlap(&r,0xb9000000,0x1000));
 assert(lmi_outer_overlap(&r,UINT64_MAX-4,8));
 assert(lmi_outer_decode(b,8,a,8,&r));
 assert(lmi_outer_decode(a,8,a,8,&r));
 assert(lmi_outer_decode(a,3,b,8,&r));
 assert(lmi_outer_decode(NULL,8,b,8,&r));
 unsigned char huge[]={0,0,0,0,0xff,0,0,0};
 assert(lmi_outer_decode(a,8,huge,8,&r));
 unsigned char wrap[]={0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff};
 assert(lmi_outer_decode(a,8,wrap,8,&r));
 puts("ACTUAL_OUTER_RANGE_ENDIAN_WIDTH_ALIGNMENT_CONTAINMENT_OVERFLOW_PASS");
}
'''
with tempfile.TemporaryDirectory(prefix='lmi-outer-range-') as tmp:
    p=Path(tmp);(p/'test.c').write_text(c)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I',str(header.parent),str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
