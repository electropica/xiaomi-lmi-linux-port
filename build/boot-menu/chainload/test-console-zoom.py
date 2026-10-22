#!/usr/bin/env python3
"""Replay the actual 2x pixel-copy function with buffer canaries."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
s=(here/'lmi-console-zoom.h').read_text()
function=s[s.index('static void lmi_pixels_double('):s.index('static BOOLEAN lmi_zoom_init(')]
c='''#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
typedef size_t UINTN;
typedef struct {uint32_t value;} EFI_GRAPHICS_OUTPUT_BLT_PIXEL;
'''+function+'''
int main(void){
 EFI_GRAPHICS_OUTPUT_BLT_PIXEL input[4]={{1},{2},{3},{4}};
 struct {uint32_t before;EFI_GRAPHICS_OUTPUT_BLT_PIXEL out[16];uint32_t after;} b={0};
 const uint32_t expected[16]={1,1,2,2,1,1,2,2,3,3,4,4,3,3,4,4};
 b.before=0x12345678;b.after=0x76543210;
 lmi_pixels_double(input,b.out,2,2);
 for(unsigned i=0;i<16;i++)if(b.out[i].value!=expected[i])return 1;
 if(b.before!=0x12345678||b.after!=0x76543210)return 2;
 puts("ACTUAL_2X_PIXELS_AND_BUFFER_CANARIES_PASS");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='lmi-console-zoom-') as tmp:
 p=Path(tmp);(p/'test.c').write_text(c)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
