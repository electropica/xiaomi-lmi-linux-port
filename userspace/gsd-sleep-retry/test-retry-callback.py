#!/usr/bin/env python3
"""Exercise the candidate's real inhibitor completion callback with mocked D-Bus."""
import pathlib, subprocess, tempfile
src = pathlib.Path(__file__).with_name('gsd-power-manager.c').read_text()
start = src.index('static gboolean\nlmi_sleep_blocked (')
end = src.index('\nstatic gboolean\nlmi_retry_cb', start)
actual = src[start:end]
program = r'''
#include <gio/gio.h>
enum { GSD_POWER_IDLE_MODE_NORMAL, GSD_POWER_IDLE_MODE_DIM };
typedef struct {
  GCancellable *cancellable;
  gboolean session_is_active, screensaver_active, lmi_suspend_pending;
  guint lmi_retry_id, lmi_retry_delay;
  int current_idle_mode;
} GsdPowerManager;
static GVariant *fake_response;
static unsigned rechecks, timers;
static gboolean lmi_retry_cb(gpointer p) { (void)p; return G_SOURCE_REMOVE; }
static void idle_configure(GsdPowerManager *p) { (void)p; rechecks++; }
static GVariant *fake_finish(gpointer p, gpointer r, GError **e) {
  (void)p; (void)r; (void)e;
  return fake_response ? g_variant_ref(fake_response) : NULL;
}
static guint fake_timer(guint delay, GSourceFunc f, gpointer p) {
  (void)delay; (void)f; (void)p; return ++timers;
}
#define g_dbus_proxy_call_finish(a,b,c) fake_finish((a),(b),(c))
#define g_timeout_add_seconds(a,b,c) fake_timer((a),(b),(c))
#define g_object_unref(a) ((void)(a))
''' + actual + r'''
static GVariant *response(const char *what, const char *mode) {
  GVariantBuilder b; g_variant_builder_init(&b, G_VARIANT_TYPE("a(ssssuu)"));
  if (what) g_variant_builder_add(&b,"(ssssuu)",what,"test","test",mode,0u,1u);
  return g_variant_ref_sink(g_variant_new("(a(ssssuu))",&b));
}
int main(void) {
  GsdPowerManager m={0}; m.cancellable=g_cancellable_new();
  m.session_is_active=TRUE; m.screensaver_active=FALSE; m.lmi_retry_delay=60;
  m.current_idle_mode=GSD_POWER_IDLE_MODE_DIM;
  fake_response=response("sleep","block");
  lmi_retry_inhibitors_done(NULL,NULL,&m);
  g_assert_cmpuint(rechecks,==,0); g_assert_cmpuint(timers,==,1);
  g_assert_cmpuint(m.lmi_retry_delay,==,120); g_variant_unref(fake_response);
  m.lmi_retry_id=0; fake_response=response(NULL,NULL);
  lmi_retry_inhibitors_done(NULL,NULL,&m);
  g_assert_cmpuint(rechecks,==,1); g_assert_cmpuint(timers,==,1);
  m.current_idle_mode=GSD_POWER_IDLE_MODE_NORMAL;
  lmi_retry_inhibitors_done(NULL,NULL,&m);
  g_assert_cmpuint(rechecks,==,1); g_assert_cmpuint(timers,==,1);
  m.current_idle_mode=GSD_POWER_IDLE_MODE_DIM; m.session_is_active=FALSE;
  lmi_retry_inhibitors_done(NULL,NULL,&m);
  g_assert_cmpuint(rechecks,==,1);
  m.session_is_active=TRUE; m.lmi_suspend_pending=TRUE;
  lmi_retry_inhibitors_done(NULL,NULL,&m);
  g_assert_cmpuint(rechecks,==,1); g_assert_cmpuint(timers,==,2);
  g_cancellable_cancel(m.cancellable); m.lmi_retry_id=0;
  lmi_retry_inhibitors_done(NULL,NULL,&m);
  g_assert_cmpuint(timers,==,2); g_assert_cmpuint(rechecks,==,1);
  g_variant_unref(fake_response); return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
    p = pathlib.Path(d); (p/'test.c').write_text(program)
    flags = subprocess.check_output(['pkg-config','--cflags','--libs','gio-2.0'],text=True).split()
    subprocess.run(['cc','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test'),*flags],check=True)
    subprocess.run([str(p/'test')],check=True)
print('RETRY_CALLBACK_PASS')
