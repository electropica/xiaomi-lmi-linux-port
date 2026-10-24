"""Native test of the extracted production helper; not a GTK gesture simulation."""
from pathlib import Path
import re,subprocess,tempfile,importlib.util,json
task=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('recipe',task/'build-packages.py')
recipe=importlib.util.module_from_spec(spec);spec.loader.exec_module(recipe)
manifest=json.loads((task/'identity.json').read_text());recipe.verify(manifest)
def helper(text):
 m=re.search(r'static void\nlmi_update_activity_visibility \(PhoshOverview \*self\)\n\{.*?\n\}',text,re.S)
 assert m;return m.group()
prefix=r'''
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>
typedef struct Widget {int running,visible,changes; const char *page;} GtkWidget;
typedef GtkWidget HdyDeck;
typedef struct {GtkWidget *app_grid,*carousel_running_activities;int has_activities;} PhoshOverviewPrivate;
typedef struct {PhoshOverviewPrivate *priv;} PhoshOverview;
#define GTK_WIDGET(x) ((GtkWidget*)(x))
#define HDY_DECK(x) ((HdyDeck*)(x))
#define HDY_IS_DECK(x) ((x)!=NULL)
#define PHOSH_TYPE_APP_GRID 1
#define g_return_if_fail(x) assert(x)
static PhoshOverviewPrivate *phosh_overview_get_instance_private(PhoshOverview*s){return s->priv;}
static GtkWidget *gtk_widget_get_template_child(GtkWidget*w,int type,const char*name){(void)type;(void)name;return w;}
static int hdy_deck_get_transition_running(HdyDeck*d){return d->running;}
static const char *hdy_deck_get_visible_child_name(HdyDeck*d){return d->page;}
static int g_strcmp0(const char*a,const char*b){return !a ? (!b?0:-1) : (!b?1:strcmp(a,b));}
static void gtk_widget_set_visible(GtkWidget*w,int visible){w->visible=!!visible;w->changes++;}
'''
suffix=r'''
int main(void){
 int checks=0;
 for(int running=0;running<2;running++)for(int home=0;home<2;home++)
 for(int has=0;has<2;has++)for(int previous=0;previous<2;previous++){
  GtkWidget drawer={.running=running,.page=home?"home":"apps"};
  GtkWidget carousel={.visible=previous};
  PhoshOverviewPrivate priv={.app_grid=&drawer,.carousel_running_activities=&carousel,.has_activities=has};
  PhoshOverview self={.priv=&priv};
  lmi_update_activity_visibility(&self);
  if(running && (carousel.changes!=0 || carousel.visible!=previous))return 10;
  if(!running && carousel.visible!=(!home && has))return 11;
  drawer.running=0;lmi_update_activity_visibility(&self);
  if(carousel.visible!=(!home && has))return 12;
  checks++;
 }
 printf("PASS %d transition/home/activity/previous-state combinations\n",checks);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='lmi-drawer-visibility-') as td:
 stage=Path(td)/'replay';stage.mkdir();recipe.patched_sources(manifest,stage)
 new=(stage/'src/overview.c').read_text()
 subprocess.run(['patch','--batch','--fuzz=0','-R','-p1','-i',str(task/'drawer-interface.patch')],cwd=stage,check=True,capture_output=True)
 old=(stage/'src/overview.c').read_text()
 for label,body in [('new',helper(new)),('rejected',helper(old))]:
  path=Path(td)/(label+'.c');path.write_text(prefix+body+suffix)
  exe=Path(td)/label
  subprocess.run(['cc','-std=c11','-O0',str(path),'-o',str(exe)],check=True)
  r=subprocess.run([str(exe)],capture_output=True,text=True)
  if label=='new':assert r.returncode==0,r.stdout+r.stderr;print(r.stdout.strip())
  else:assert r.returncode==10,'Rejected helper must expose mutation during transition';print('REJECTED_VERSION_CONTROL: detected in-transition visibility mutation')
print('LIMIT: tests helper control flow with stub widgets, not real GTK touch routing')
