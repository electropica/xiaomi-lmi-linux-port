/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "lmi-home-order.h"

int main (void)
{
  const char *favs[] = { "A.desktop", "missing.desktop", "B.desktop", "C.desktop", NULL };
  g_auto (GStrv) moved = lmi_favorites_move (favs, "A.desktop", "C.desktop");
  g_auto (GStrv) back = lmi_favorites_move ((const char * const *) moved, "A.desktop", "missing.desktop");
  const char *slots[LMI_HOME_SLOT_COUNT + 1] = { "A.desktop", "B.desktop", "", "", "", "", "", "", "", "", "", "", "", "", "", "", NULL };
  g_auto (GStrv) placed = lmi_home_place (slots, "C.desktop", 0);
  g_auto (GStrv) swapped = lmi_home_place (slots, "A.desktop", 1);

  g_assert_cmpstr (moved[0], ==, "missing.desktop");
  g_assert_cmpstr (moved[3], ==, "A.desktop");
  g_assert_true (g_strv_equal ((const char * const *) back, favs));
  g_assert_cmpstr (favs[0], ==, "A.desktop");
  g_assert_null (lmi_favorites_move (favs, "absent.desktop", "A.desktop"));
  g_assert_null (lmi_favorites_move (favs, "A.desktop", "A.desktop"));
  g_assert_cmpstr (placed[0], ==, "C.desktop");
  g_assert_cmpstr (placed[2], ==, "A.desktop");
  g_assert_cmpstr (placed[1], ==, "B.desktop");
  g_assert_cmpstr (swapped[0], ==, "B.desktop");
  g_assert_cmpstr (swapped[1], ==, "A.desktop");
  g_assert_null (lmi_home_place (slots, "A.desktop", 0));
  g_assert_null (lmi_home_place (slots, "C.desktop", LMI_HOME_SLOT_COUNT));
  g_assert_null (lmi_home_place (slots, "", 1));
  const char *four[] = {"A.desktop", "B.desktop", "C.desktop", "D.desktop", NULL};
  const char *none[] = {NULL};
  g_auto (GStrv) fifth = lmi_favorites_place (four, "E.desktop", NULL);
  g_auto (GStrv) inserted = lmi_favorites_place (four, "E.desktop", "B.desktop");
  g_auto (GStrv) reordered = lmi_favorites_place ((const char * const *) fifth, "A.desktop", "E.desktop");
  g_auto (GStrv) first = lmi_favorites_place (none, "A.desktop", NULL);

  g_assert_cmpuint (g_strv_length (fifth), ==, 5);
  g_assert_cmpstr (fifth[4], ==, "E.desktop");
  g_assert_cmpstr (inserted[1], ==, "E.desktop");
  g_assert_cmpstr (inserted[2], ==, "B.desktop");
  g_assert_null (lmi_favorites_place ((const char * const *) fifth, "F.desktop", NULL));
  g_assert_cmpuint (g_strv_length (reordered), ==, 5);
  g_assert_cmpstr (reordered[4], ==, "A.desktop");
  g_assert_cmpstr (first[0], ==, "A.desktop");
  g_assert_cmpstr (four[0], ==, "A.desktop");
  g_assert_null (lmi_favorites_place (four, "E.desktop", "absent.desktop"));
  g_assert_null (lmi_favorites_place (four, "", NULL));
  g_auto (GStrv) removed_fav = lmi_shortcut_remove (four, "B.desktop", FALSE);
  g_auto (GStrv) removed_home = lmi_shortcut_remove (slots, "A.desktop", TRUE);
  const char *duplicate[] = {"A.desktop", "A.desktop", NULL};

  g_assert_cmpuint (g_strv_length (removed_fav), ==, 3);
  g_assert_cmpstr (removed_fav[1], ==, "C.desktop");
  g_assert_cmpuint (g_strv_length (removed_home), ==, 16);
  g_assert_cmpstr (removed_home[0], ==, "");
  g_assert_cmpstr (removed_home[1], ==, "B.desktop");
  g_assert_null (lmi_shortcut_remove (duplicate, "A.desktop", FALSE));
  g_assert_null (lmi_shortcut_remove (four, "missing.desktop", FALSE));
  g_print ("FAVORITE_ORDER_HOME_SLOT_AND_FIVE_FAVORITE_LIMIT_TESTS_OK\n");
  return 0;
}
