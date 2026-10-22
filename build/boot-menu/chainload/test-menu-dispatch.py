#!/usr/bin/env python3
"""Replay actual menu handoff callbacks; test checked choice versus default."""
from pathlib import Path
import subprocess,tempfile
source=Path('/home/linuxagent/lmi-boot-menu-build/source/edk2-msm/GPLDrivers/Library/SimpleInit/src/gui/interface/core/bootmenu.c').read_text()
def function(signature):
    start=source.index(signature);begin=source.index('{',start);depth=1;i=begin+1
    while depth:
        depth+=(source[i]=='{')-(source[i]=='}');i+=1
    return source[start:i]
c=r'''
#include <string.h>
#include <stdbool.h>
#include <assert.h>
#include <stdio.h>
#define ENABLE_UEFI
#define PATH_MAX 4096
#define BOOT_SIMPLE_INIT 11
#define tlog_debug(...) ((void)0)
typedef struct {int mode;char ident[64];} boot_config;
struct bootmenu_item {boot_config cfg;};
struct bootmenu {struct bootmenu_item *selected;};
static char target_boot_name[PATH_MAX],current[64],executed[64];
static bool no_autoboot,gui_run;
static int (*queued)(void*);
static int boot_name(const char *name){strcpy(executed,name);return 0;}
static void gui_set_run_exit(void *p){(void)p;}
static int gui_screen_init(void){return 0;}
static int bootmenu_draw(void){return 0;}
static int gui_main(void){return 0;}
static bool bootmenu_chdir(struct bootmenu_item *bi){(void)bi;return false;}
static void enter_simple_init(void *p){(void)p;}
static void lv_async_call(void(*fn)(void*),void *p){fn(p);}
static void confd_set_string(const char *key,const char *name){assert(!strcmp(key,"boot.current"));strcpy(current,name);}
static void confd_set_save(const char *key,bool b){(void)key;(void)b;}
static void gui_run_and_exit(int (*fn)(void*)){queued=fn;}
'''+function('static int after_exit(')+'\n'+function('static void bootmenu_boot(')+r'''
int main(void){
 struct bootmenu_item mobian={{8,"mobian"}},android={{8,"android"}};
 struct bootmenu bm={&mobian};strcpy(current,"mobian");
 bootmenu_boot(&bm);assert(queued&&!strcmp(target_boot_name,"mobian"));
 queued(NULL);assert(!strcmp(executed,"mobian")&&no_autoboot&&gui_run);
 /* Simulate an explicitly checked Android choice while default remains Mobian. */
 bm.selected=&android;strcpy(current,"mobian");queued=NULL;
 bootmenu_boot(&bm);assert(queued&&!strcmp(target_boot_name,"android"));
 assert(!strcmp(current,"android"));
 /* Dispatch must use the copied choice even if the GUI selection changes. */
 bm.selected=&mobian;queued(NULL);assert(!strcmp(executed,"android"));
 assert(!target_boot_name[0]);
 puts("ACTUAL_MENU_CHECKED_ANDROID_DISPATCH_AND_MOBIAN_DEFAULT_PASS");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='lmi-dispatch-') as tmp:
 p=Path(tmp);(p/'test.c').write_text(c)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
