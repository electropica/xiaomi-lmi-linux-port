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
