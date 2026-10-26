from pathlib import Path
import importlib.util, json, subprocess, tempfile

repo = Path(__file__).resolve().parents[3]
task = repo / 'userspace/phosh/drawer-search-close-candidate'
spec = importlib.util.spec_from_file_location('candidate', task / 'build-packages.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
manifest = json.loads((task / 'identity.json').read_text())
with tempfile.TemporaryDirectory(prefix='lmi-close-callback-check-') as td:
    tmp = Path(td)
    module.patched_sources(manifest, tmp)
    source = (tmp / 'src/app-grid.c').read_text()
    start = source.index('static void\non_lmi_drawer_transition_running (')
    end = source.index('\n}\n', start) + 3
    callback = source[start:end]
    before = r'''
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef struct { int running; const char *child; } GObject;
typedef void GParamSpec;
typedef void *gpointer;
typedef struct { unsigned debounce; char *search_string; char *search; } PhoshAppGridPrivate;
typedef struct { PhoshAppGridPrivate priv; } PhoshAppGrid;
static int removed, searches;
#define PHOSH_IS_APP_GRID(s) ((s) != NULL)
#define HDY_DECK(o) (o)
#define GTK_ENTRY(o) (o)
#define g_return_if_fail(v) do { assert(v); } while (0)
#define g_clear_handle_id(p,f) do { if (*(p)) { f(*(p)); *(p)=0; } } while (0)
#define g_clear_pointer(p,f) do { if (*(p)) f(*(p)); *(p)=NULL; } while (0)
#define g_free free
static PhoshAppGridPrivate *phosh_app_grid_get_instance_private(PhoshAppGrid *s) { return &s->priv; }
static int hdy_deck_get_transition_running(GObject *o) { return o->running; }
static const char *hdy_deck_get_visible_child_name(GObject *o) { return o->child; }
static int g_strcmp0(const char *a,const char *b) { return a&&b?strcmp(a,b):a!=b; }
static void g_source_remove(unsigned id) { assert(id); removed++; }
static void gtk_entry_set_text(char *entry,const char *text) { assert(!*text); entry[0]=0; }
static void do_search(PhoshAppGrid *self) { assert(self->priv.search_string==NULL); searches++; }
'''
    after = r'''
static void reset(PhoshAppGrid *s,char *entry,const char *query) {
  free(s->priv.search_string);s->priv.search_string=strdup(query);
  strcpy(entry,query);s->priv.search=entry;s->priv.debounce=123;
  removed=searches=0;
}
int main(void) {
  char entry[80];PhoshAppGrid s={0};GObject deck={1,"home"};
  reset(&s,entry,"Calculatrice");
  on_lmi_drawer_transition_running(&deck,NULL,&s);
  assert(!strcmp(entry,"Calculatrice")&&s.priv.debounce==123&&searches==0);
  deck.running=0;deck.child="apps";
  on_lmi_drawer_transition_running(&deck,NULL,&s);
  assert(!strcmp(entry,"Calculatrice")&&searches==0);
  deck.child="home";
  on_lmi_drawer_transition_running(&deck,NULL,&s);
  assert(!*entry&&s.priv.search_string==NULL&&!s.priv.debounce&&removed==1&&searches==1);
  reset(&s,entry,"zzzz-introuvable");
  on_lmi_drawer_transition_running(&deck,NULL,&s);
  assert(!*entry&&!s.priv.search_string&&!s.priv.debounce&&removed==1);
  reset(&s,entry,"old applied query");strcpy(entry,"fresh pending query");
  on_lmi_drawer_transition_running(&deck,NULL,&s);
  assert(!*entry&&!s.priv.search_string&&!s.priv.debounce);
  on_lmi_drawer_transition_running(&deck,NULL,&s);
  assert(!*entry&&removed==1);
  reset(&s,entry,"new query after reopening");deck.child="apps";
  on_lmi_drawer_transition_running(&deck,NULL,&s);
  assert(!strcmp(entry,"new query after reopening")&&searches==0);
  free(s.priv.search_string);
  puts("7 exact-callback gesture/search state checks PASS (stubbed GTK, not tactile acceptance)");
}
'''
    c = tmp / 'probe.c'
    c.write_text(before + callback + after)
    exe = tmp / 'probe'
    subprocess.run(['cc', '-D_POSIX_C_SOURCE=200809L', '-std=c11', '-Wall', '-Wextra',
                    '-Werror', '-Wno-unused-parameter', '-fsanitize=address,undefined',
                    str(c), '-o', str(exe)], check=True)
    output = subprocess.check_output([str(exe)], text=True)
    print(output)
    (task / 'host-validation.json').write_text(json.dumps({
        'actual_callback_extracted': True, 'checks': 7, 'result': 'PASS',
        'sanitizers': ['ASan', 'UBSan'],
        'limits': 'GTK APIs stubbed. No real GTK gesture or ARM64 package execution.',
        'source_after_sha256': manifest['sources'][0]['after'],
    }, indent=2) + '\n')
