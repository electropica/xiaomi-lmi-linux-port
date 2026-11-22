#!/usr/bin/env python3
"""Compile and exercise the actual inhibitor parser from the candidate."""
import pathlib, subprocess, tempfile

source = pathlib.Path(__file__).with_name('gsd-power-manager.c').read_text()
start = source.index('static gboolean\nlmi_sleep_blocked (')
end = source.index('\nstatic void\nlmi_retry_inhibitors_done', start)
function = source[start:end]
test = r'''
#include <gio/gio.h>
''' + function + r'''
static GVariant *row(const char *what, const char *mode) {
  GVariantBuilder b; g_variant_builder_init(&b, G_VARIANT_TYPE("a(ssssuu)"));
  if (what) g_variant_builder_add(&b, "(ssssuu)", what, "test", "test", mode, 0u, 1u);
  return g_variant_ref_sink(g_variant_new("(a(ssssuu))", &b));
}
int main(void) {
  GVariant *v;
  g_assert_true(lmi_sleep_blocked(NULL));
  v=g_variant_ref_sink(g_variant_new("(s)","bad")); g_assert_true(lmi_sleep_blocked(v)); g_variant_unref(v);
  v=row(NULL,NULL); g_assert_false(lmi_sleep_blocked(v)); g_variant_unref(v);
  v=row("sleep","delay"); g_assert_false(lmi_sleep_blocked(v)); g_variant_unref(v);
  v=row("idle:sleep","block"); g_assert_true(lmi_sleep_blocked(v)); g_variant_unref(v);
  v=row("sleep:shutdown","block-weak"); g_assert_true(lmi_sleep_blocked(v)); g_variant_unref(v);
  v=row("idle","block"); g_assert_false(lmi_sleep_blocked(v)); g_variant_unref(v);
  return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
    p = pathlib.Path(d); (p/'test.c').write_text(test)
    flags = subprocess.check_output(['pkg-config', '--cflags', '--libs', 'gio-2.0'], text=True).split()
    subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', str(p/'test.c'), '-o', str(p/'test'), *flags], check=True)
    subprocess.run([str(p/'test')], check=True)
print('INHIBITOR_PARSER_PASS')
