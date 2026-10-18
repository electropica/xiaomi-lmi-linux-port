static void
test_phosh_home_remove (void)
{
  g_autoptr (GSettings) settings = g_settings_new ("sm.puri.phosh");
  g_autoptr (GAppInfo) info = G_APP_INFO (g_desktop_app_info_new ("demo.app.First.desktop"));
  const char *slots[] = {"demo.app.First.desktop", "demo.app.Second.desktop", "", "", "", "", "", "", "", "", "", "", "", "", "", "", NULL};
  GtkWidget *btn = phosh_app_grid_button_new (info);
  GActionGroup *actions = gtk_widget_get_action_group (btn, "app-btn");
  g_auto (GStrv) got = NULL;

  g_settings_set_strv (settings, "lmi-home-slots", slots);
  g_object_set_data (G_OBJECT (btn), "lmi-home-remove-slot", GINT_TO_POINTER (1));
  g_action_group_activate_action (actions, "home-remove", NULL);
  while (g_main_context_iteration (NULL, FALSE));
  got = g_settings_get_strv (settings, "lmi-home-slots");
  g_assert_cmpstr (got[0], ==, "");
  g_assert_cmpstr (got[1], ==, "demo.app.Second.desktop");
  g_assert_cmpuint (g_strv_length (got), ==, 16);
  g_clear_pointer (&got, g_strfreev);

  /* A settings change between activation and idle must not be overwritten. */
  g_settings_set_strv (settings, "lmi-home-slots", slots);
  g_action_group_activate_action (actions, "home-remove", NULL);
  slots[0] = "demo.app.Second.desktop";
  g_settings_set_strv (settings, "lmi-home-slots", slots);
  while (g_main_context_iteration (NULL, FALSE));
  got = g_settings_get_strv (settings, "lmi-home-slots");
  g_assert_cmpstr (got[0], ==, "demo.app.Second.desktop");
  gtk_widget_destroy (btn);
}
