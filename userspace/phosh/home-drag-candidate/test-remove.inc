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

static LmiHomeDrop *
test_transfer_snapshot (void)
{
  LmiHomeDrop *drop = g_new0 (LmiHomeDrop, 1);

  drop->settings = g_settings_new ("sm.puri.phosh");
  drop->key = g_strdup ("lmi-home-slots");
  drop->before = g_settings_get_strv (drop->settings, drop->key);
  drop->after = lmi_home_place ((const char * const *) drop->before, "demo.app.First.desktop", 3);
  drop->source_key = g_strdup ("favorites");
  drop->source_before = g_settings_get_strv (drop->settings, drop->source_key);
  drop->source_after = lmi_shortcut_remove ((const char * const *) drop->source_before,
                                           "demo.app.First.desktop", FALSE);
  return drop;
}

static void
test_phosh_home_transfer (void)
{
  g_autoptr (GSettings) settings = g_settings_new ("sm.puri.phosh");
  const char *home[] = {"", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", NULL};
  const char *favorites[] = {"demo.app.First.desktop", "demo.app.Second.desktop", NULL};
  const char *changed[] = {"demo.app.First.desktop", "demo.app.Second.desktop", "other.desktop", NULL};
  g_auto (GStrv) saved_home = g_settings_get_strv (settings, "lmi-home-slots");
  g_auto (GStrv) saved_favs = g_settings_get_strv (settings, "favorites");
  g_auto (GStrv) got_home = NULL;
  g_auto (GStrv) got_favs = NULL;
  LmiHomeDrop *drop;

  g_settings_set_strv (settings, "lmi-home-slots", home);
  g_settings_set_strv (settings, "favorites", favorites);
  drop = test_transfer_snapshot ();
  lmi_home_drop_apply (drop);
  lmi_home_drop_free (drop);
  got_home = g_settings_get_strv (settings, "lmi-home-slots");
  got_favs = g_settings_get_strv (settings, "favorites");
  g_assert_cmpstr (got_home[3], ==, "demo.app.First.desktop");
  g_assert_cmpuint (g_strv_length (got_favs), ==, 1);
  g_assert_cmpstr (got_favs[0], ==, "demo.app.Second.desktop");
  g_clear_pointer (&got_home, g_strfreev);
  g_clear_pointer (&got_favs, g_strfreev);

  /* A source change cancels both writes, including the destination insert. */
  g_settings_set_strv (settings, "lmi-home-slots", home);
  g_settings_set_strv (settings, "favorites", favorites);
  drop = test_transfer_snapshot ();
  g_settings_set_strv (settings, "favorites", changed);
  lmi_home_drop_apply (drop);
  lmi_home_drop_free (drop);
  got_home = g_settings_get_strv (settings, "lmi-home-slots");
  got_favs = g_settings_get_strv (settings, "favorites");
  g_assert_cmpstr (got_home[3], ==, "");
  g_assert_true (g_strv_equal ((const char * const *) got_favs, changed));
  g_settings_set_strv (settings, "lmi-home-slots", (const char * const *) saved_home);
  g_settings_set_strv (settings, "favorites", (const char * const *) saved_favs);
}
