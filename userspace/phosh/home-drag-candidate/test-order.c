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
  g_print ("FAVORITE_ORDER_AND_HOME_SLOT_TESTS_OK\n");
  return 0;
}
