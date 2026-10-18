#!/usr/bin/env python3
"""Host regression test of actual grab predicates; not an end-to-end DnD test."""
from pathlib import Path
import subprocess,sys,tempfile
source=Path(sys.argv[1]).read_text()
def function(name):
 a=source.index('\n'+name+' (');a=source.rfind('\nstatic ',0,a);b=source.index('\n}\n',a)+3
 return source[a:b]
stubs="""
#include <stdbool.h>
#include <stddef.h>
struct wlr_surface { bool layer; };
struct wlr_layer_surface_v1 { int unused; };
struct wlr_seat { void *drag; bool grab; };
typedef struct { struct wlr_seat *seat; } PhocSeat;
static struct wlr_surface *wlr_surface_get_root_surface(struct wlr_surface *s) { return s; }
static struct wlr_layer_surface_v1 *wlr_layer_surface_v1_try_from_wlr_surface(struct wlr_surface *s) { static struct wlr_layer_surface_v1 l; return s->layer ? &l : NULL; }
static bool wlr_seat_touch_has_grab(struct wlr_seat *s) { return s->grab; }
static bool wlr_seat_pointer_has_grab(struct wlr_seat *s) { return s->grab; }
"""
main="""
int main(void) {
 struct wlr_seat w={0}; PhocSeat seat={&w}; struct wlr_surface surf={0};
 bool (*predicates[])(PhocSeat*,struct wlr_surface*)={should_ignore_touch_grab,should_ignore_pointer_grab};
 for (unsigned i=0;i<2;i++) {
  for (unsigned layer=0;layer<2;layer++) for(unsigned grab=0;grab<2;grab++) for(unsigned drag=0;drag<2;drag++) {
   surf.layer=layer;w.grab=grab;w.drag=drag ? &w : NULL;
   if(predicates[i](&seat,NULL)) return 1;
   if(predicates[i](&seat,&surf)!=(layer && grab && !drag)) return 2;
  }
 }
 return 0;
}
"""
with tempfile.TemporaryDirectory(prefix='phoc-grab-test-') as td:
 p=Path(td);c=p/'test.c';binary=p/'test'
 c.write_text(stubs+function('should_ignore_touch_grab')+function('should_ignore_pointer_grab')+main)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(c),'-o',str(binary)],check=True)
 result=subprocess.run([str(binary)])
 if result.returncode:sys.exit(result.returncode)
print('PASS: 16 routing combinations and 16 null-surface checks; touch and pointer')
