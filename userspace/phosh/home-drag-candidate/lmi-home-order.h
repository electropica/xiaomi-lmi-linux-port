/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <glib.h>
#include <string.h>
#define LMI_HOME_SLOT_COUNT 16

static inline char **
lmi_favorites_move (const char * const *before, const char *source, const char *target)
{
  int from = -1, to = -1;
  char **after;
  char *item;

  if (!before || !source || !target || g_str_equal (source, target))
    return NULL;
  for (int i = 0; before[i]; i++) {
    if (g_str_equal (before[i], source)) {
      if (from >= 0) return NULL;
      from = i;
    }
    if (g_str_equal (before[i], target)) {
      if (to >= 0) return NULL;
      to = i;
    }
  }
  if (from < 0 || to < 0) return NULL;
  after = g_strdupv ((char **) before);
  item = after[from];
  if (from < to)
    memmove (&after[from], &after[from + 1], (to - from) * sizeof (char *));
  else
    memmove (&after[to + 1], &after[to], (from - to) * sizeof (char *));
  after[to] = item;
  return after;
}

/* Add from the drawer or reorder an existing favorite. Never truncate IDs. */
#define LMI_FAVORITE_LIMIT 5
static inline char **
lmi_favorites_place (const char * const *before, const char *source, const char *target)
{
  guint count;
  int from = -1, to = -1;
  char **after;

  if (!before || !source || !*source) return NULL;
  count = g_strv_length ((char **) before);
  for (guint i = 0; i < count; i++) {
    if (g_str_equal (before[i], source)) {
      if (from >= 0) return NULL;
      from = i;
    }
    if (target && g_str_equal (before[i], target)) {
      if (to >= 0) return NULL;
      to = i;
    }
  }
  if (target && to < 0) return NULL;
  if (from >= 0)
    return lmi_favorites_move (before, source, target ? target : before[count - 1]);
  if (count >= LMI_FAVORITE_LIMIT) return NULL;
  if (to < 0) to = count;
  after = g_new0 (char *, count + 2);
  for (guint i = 0, j = 0; i < count + 1; i++)
    after[i] = i == (guint) to ? g_strdup (source) : g_strdup (before[j++]);
  return after;
}

static inline char **
lmi_home_place (const char * const *before, const char *source, guint target)
{
  int from = -1, empty = -1;
  char **after;

  if (!before || !source || !*source || target >= LMI_HOME_SLOT_COUNT ||
      g_strv_length ((char **) before) != LMI_HOME_SLOT_COUNT) return NULL;
  for (int i = 0; i < LMI_HOME_SLOT_COUNT; i++) {
    if (g_str_equal (before[i], source)) {
      if (from >= 0) return NULL;
      from = i;
    }
    if (!*before[i] && empty < 0) empty = i;
  }
  if (from == (int) target) return NULL;
  if (from < 0 && *before[target] && empty < 0) return NULL;
  after = g_strdupv ((char **) before);
  if (from >= 0) {
    char *item = after[from];
    after[from] = after[target];
    after[target] = item;
  } else {
    if (*after[target]) {
      g_free (after[empty]);
      after[empty] = after[target];
    } else {
      g_free (after[target]);
    }
    after[target] = g_strdup (source);
  }
  return after;
}

/* Remove exactly one source shortcut; preserve empty fixed home slots. */
static inline char **
lmi_shortcut_remove (const char * const *before, const char *id, gboolean home)
{
  int found = -1;
  guint count;
  char **after;

  if (!before || !id || !*id) return NULL;
  count = g_strv_length ((char **) before);
  if (home && count != LMI_HOME_SLOT_COUNT) return NULL;
  for (guint i = 0; i < count; i++) {
    if (!g_str_equal (before[i], id)) continue;
    if (found >= 0) return NULL;
    found = i;
  }
  if (found < 0) return NULL;
  if (home) {
    after = g_strdupv ((char **) before);
    g_free (after[found]);
    after[found] = g_strdup ("");
  } else {
    after = g_new0 (char *, count);
    for (guint i = 0, j = 0; i < count; i++)
      if (i != (guint) found) after[j++] = g_strdup (before[i]);
  }
  return after;
}
