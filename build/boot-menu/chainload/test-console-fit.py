#!/usr/bin/env python3
"""Compile the actual console formatter against a bounded UEFI mock."""
from pathlib import Path
import subprocess,tempfile
def main():
 here=Path(__file__).resolve().parent
 c=r'''
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
typedef uintptr_t UINTN;typedef int32_t INT32;typedef uint16_t CHAR16;typedef int BOOLEAN;
#define FALSE 0
#define TRUE 1
#define EFI_ERROR(s) ((s)!=0)
typedef struct Console Console;
typedef struct {INT32 MaxMode,Mode;} Mode;
struct Console {Mode*Mode;int(*QueryMode)(Console*,UINTN,UINTN*,UINTN*);int(*SetMode)(Console*,UINTN);int(*EnableCursor)(Console*,BOOLEAN);int(*OutputString)(Console*,CHAR16*);};
typedef struct {Console*ConOut;} System;
static System*gST;
static unsigned chars,lines,failed,sets;
static int query(Console*c,UINTN m,UINTN*w,UINTN*h){(void)c;if(m>1)return 1;*w=m?40:80;*h=m?100:25;return 0;}
static int set(Console*c,UINTN m){c->Mode->Mode=(INT32)m;sets++;return 0;}
static int cursor(Console*c,BOOLEAN b){(void)c;(void)b;return 0;}
static int output(Console*c,CHAR16*s){UINTN n=0,w,h;query(c,c->Mode->Mode,&w,&h);while(n<258&&s[n])n++;if(n>=258||n>w||n<3||s[0]!=' '||s[n-2]!='\r'||s[n-1]!='\n'){failed++;return 1;}chars+=(unsigned)n-3;lines++;return 0;}
#define LMI_CONSOLE_ZOOM_H
static UINTN lmi_zoom_columns;
static BOOLEAN lmi_zoom_init(void){return FALSE;}
static BOOLEAN lmi_zoom_line(CHAR16*line){(void)line;return FALSE;}
'''
 # The included formatter remains byte-identical to the firmware source.
 c+='\n#include "lmi-console-fit.h"\n'+r'''
int main(void){
 Mode m={2,0};Console con={&m,query,set,cursor,output};System sys={&con};char text[16001];
 memset(text,'A',16000);text[16000]=0;gST=&sys;
 lmi_fit_console_line(text);
 if(failed||chars!=16000||sets!=1||m.Mode!=1||lines<400)return 1;
 chars=lines=0;lmi_fit_console_line("one\ntwo\tthree");
 if(failed||chars!=12||sets!=1)return 2;
 gST=NULL;lmi_fit_console_line("ignored");
 puts("CONSOLE_MODE_WIDTH_MARGINS_AND_LONG_LINE_BOUNDS_PASS");return 0;
}
'''
 with tempfile.TemporaryDirectory(prefix='lmi-console-fit-') as tmp:
  root=Path(tmp);(root/'Library').mkdir();(root/'Library/UefiBootServicesTableLib.h').write_text('/* Mock: declarations supplied by harness. */\n')
  source=root/'test.c';exe=root/'test';source.write_text(c)
  subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(root),'-I'+str(here),str(source),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
if __name__=='__main__':main()
