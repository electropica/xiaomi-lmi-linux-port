static gboolean
test_home_busy (gpointer unused)
{
  return G_SOURCE_CONTINUE;
}

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
  guint busy = g_idle_add_full (G_PRIORITY_DEFAULT, test_home_busy, NULL, NULL);
  g_action_group_activate_action (actions, "home-remove", NULL);
  for (int i = 0; i < 5; i++) g_main_context_iteration (NULL, FALSE);
  g_source_remove (busy);
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

static void
test_phosh_home_row_width (void)
{
  g_autoptr (GtkCssProvider) css = gtk_css_provider_new ();
  GdkScreen *screen = gdk_screen_get_default ();
  g_autoptr (GAppInfo) info = G_APP_INFO (g_desktop_app_info_new ("demo.app.First.desktop"));

  gtk_css_provider_load_from_resource (css, "/mobi/phosh/stylesheet/adwaita-dark.css");
  gtk_style_context_add_provider_for_screen (screen, GTK_STYLE_PROVIDER (css), GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
  for (int favorite = 0; favorite < 2; favorite++) {
    GtkWidget *row = gtk_flow_box_new ();
    int count = favorite ? 5 : 4;
    int minimum, natural;

    gtk_flow_box_set_homogeneous (GTK_FLOW_BOX (row), TRUE);
    gtk_flow_box_set_min_children_per_line (GTK_FLOW_BOX (row), count);
    gtk_flow_box_set_max_children_per_line (GTK_FLOW_BOX (row), count);
    gtk_flow_box_set_column_spacing (GTK_FLOW_BOX (row), 6);
    for (int i = 0; i < count; i++) {
      GtkWidget *cell = favorite ? phosh_app_grid_button_new_favorite (info)
                                : phosh_app_grid_button_new (info);
      if (!favorite) lmi_home_compact_cell (cell);
      gtk_container_add (GTK_CONTAINER (row), cell);
    }
    gtk_widget_show_all (row);
    gtk_widget_get_preferred_width (row, &minimum, &natural);
    g_test_message ("%d columns need %d logical pixels", count, minimum);
    g_assert_cmpint (minimum + 6, <=, 360);
    gtk_widget_destroy (row);
  }
  gtk_style_context_remove_provider_for_screen (screen, GTK_STYLE_PROVIDER (css));
}
