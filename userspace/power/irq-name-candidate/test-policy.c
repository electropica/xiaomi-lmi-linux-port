
#include <glib.h>
#include <string.h>
static const char *capacity = "73", *status = "Discharging";
static gboolean readable = TRUE;
static gboolean test_read (const gchar *path, gchar **out, gsize *len, GError **err) {
  (void) len; (void) err;
  if (!readable) return FALSE;
  if (g_str_has_suffix(path, "/capacity")) *out = g_strdup(capacity);
  else if (g_str_has_suffix(path, "/status")) *out = g_strdup(status);
  else g_assert_not_reached();
  return TRUE;
}
#define g_file_get_contents test_read
static gboolean
lmi_resume_reason_has_name (const char *reason, const char *name)
{
  const char *p = reason;

  if (p == NULL || !g_ascii_isdigit (*p))
    return FALSE;
  while (g_ascii_isdigit (*p))
    p++;
  if (*p != ' ')
    return FALSE;
  while (*p == ' ')
    p++;
  return g_strcmp0 (p, name) == 0;
}

static gboolean
lmi_quiet_reason_allowed (const char *reason)
{
  g_autofree char *capacity = NULL;
  g_autofree char *status = NULL;
  char *end = NULL;
  guint64 level;

  if (lmi_resume_reason_has_name (reason, "msoc-delta"))
    return TRUE;
  if (!lmi_resume_reason_has_name (reason, "msoc-high") &&
      !lmi_resume_reason_has_name (reason, "esr-delta"))
    return FALSE;
  if (!g_file_get_contents ("/sys/class/power_supply/battery/capacity",
                            &capacity, NULL, NULL) ||
      !g_file_get_contents ("/sys/class/power_supply/battery/status",
                            &status, NULL, NULL))
    return FALSE;
  g_strstrip (capacity);
  if (!g_ascii_isdigit (capacity[0]) ||
      g_strcmp0 (g_strstrip (status), "Discharging") != 0)
    return FALSE;
  level = g_ascii_strtoull (capacity, &end, 10);
  return end != capacity && *end == '\0' && level >= 30 && level <= 100;
}

int main (void) {
  const char *yes[] = {"438 msoc-delta", "451 msoc-delta", "999999 msoc-delta", "451  msoc-delta"};
  const char *no[] = {NULL, "", "msoc-delta", "x msoc-delta", "-1 msoc-delta", "451msoc-delta", "451 msoc-delta-extra", "451 msoc-delta\n447 esr-delta", "451 msoc-delta\n", "451 msoc-low", "473 typec-cc-state-change", "362 rtc_alarm", "451 unknown"};
  guint n = 0;
  for (guint i=0;i<G_N_ELEMENTS(yes);i++,n++) g_assert_true(lmi_quiet_reason_allowed(yes[i]));
  for (guint i=0;i<G_N_ELEMENTS(no);i++,n++) g_assert_false(lmi_quiet_reason_allowed(no[i]));
  const char *guarded[] = {"441 msoc-high", "454 msoc-high", "445 esr-delta", "447 esr-delta"};
  const char *levels[] = {"0","29","30","73","100","101","abc","","73x"};
  for (guint i=0;i<G_N_ELEMENTS(guarded);i++) {
    for (guint j=0;j<G_N_ELEMENTS(levels);j++,n++) {
      capacity=levels[j]; status="Discharging"; readable=TRUE;
      g_assert_cmpint(lmi_quiet_reason_allowed(guarded[i]), ==, j>=2 && j<=4);
    }
    capacity="73"; status="Charging"; n++; g_assert_false(lmi_quiet_reason_allowed(guarded[i]));
    status="Discharging"; readable=FALSE; n++; g_assert_false(lmi_quiet_reason_allowed(guarded[i]));
  }
  /* Preserve the existing unconditional msoc-delta branch. */
  n++; g_assert_true(lmi_quiet_reason_allowed("451 msoc-delta"));
  g_print("%u exact-source policy cases PASS\n", n);
  return 0;
}
