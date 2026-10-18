/* SPDX-License-Identifier: GPL-3.0-or-later */
static void
lmi_home_rebuild (PhoshAppGrid *self)
{
  PhoshAppGridPrivate *priv = phosh_app_grid_get_instance_private (self);
  g_auto (GStrv) slots = g_settings_get_strv (priv->settings, "lmi-home-slots");
  g_autoptr (GList) children = gtk_container_get_children (GTK_CONTAINER (priv->lmi_home_slots));

  if (g_strv_length (slots) != LMI_HOME_SLOT_COUNT) return;
  for (GList *l = children; l; l = l->next)
    gtk_widget_destroy (GTK_WIDGET (l->data));
  for (int i = 0; i < LMI_HOME_SLOT_COUNT; i++) {
    g_autoptr (GDesktopAppInfo) app = *slots[i] ? g_desktop_app_info_new (slots[i]) : NULL;
    GtkWidget *cell;
    GtkWidget *target;

    if (app) {
      cell = phosh_app_grid_button_new (G_APP_INFO (app));
      target = GTK_WIDGET (gtk_widget_get_template_child (cell, PHOSH_TYPE_APP_GRID_BASE_BUTTON, "button"));
      g_signal_connect (cell, "app-launched", G_CALLBACK (app_launched_cb), self);
    } else {
      cell = gtk_flow_box_child_new ();
      target = gtk_event_box_new ();
      gtk_widget_set_size_request (target, 84, 84);
      gtk_container_add (GTK_CONTAINER (cell), target);
    }
    lmi_home_enable_target (target, NULL, i);
    gtk_container_add (GTK_CONTAINER (priv->lmi_home_slots), cell);
    gtk_widget_show_all (cell);
  }
}

static gboolean
lmi_home_reveal_for_drag (gpointer data)
{
  PhoshAppGrid *self = PHOSH_APP_GRID (data);
  PhoshAppGridPrivate *priv = phosh_app_grid_get_instance_private (self);

  priv->lmi_drag_home_timer = 0;
  g_object_set (priv->lmi_favorites_drawer, "visible-child-name", "home", NULL);
  return G_SOURCE_REMOVE;
}

static gboolean
lmi_home_drag_motion (GtkWidget *widget, GdkDragContext *context, int x, int y,
                       guint time, PhoshAppGrid *self)
{
  PhoshAppGridPrivate *priv = phosh_app_grid_get_instance_private (self);

  if (!lmi_home_source_id (context)) return FALSE;
  if (y < 48) {
    if (!priv->lmi_drag_home_timer)
      priv->lmi_drag_home_timer = g_timeout_add (500, lmi_home_reveal_for_drag, self);
  } else {
    g_clear_handle_id (&priv->lmi_drag_home_timer, g_source_remove);
  }
  gdk_drag_status (context, GDK_ACTION_MOVE, time);
  return TRUE;
}

static void
lmi_home_drag_leave (GtkWidget *widget, GdkDragContext *context, guint time,
                      PhoshAppGrid *self)
{
  PhoshAppGridPrivate *priv = phosh_app_grid_get_instance_private (self);
  g_clear_handle_id (&priv->lmi_drag_home_timer, g_source_remove);
}

static void
lmi_home_settings_changed (PhoshAppGrid *self, const char *key, GSettings *settings)
{
  lmi_home_rebuild (self);
}

static void
lmi_home_setup (PhoshAppGrid *self)
{
  PhoshAppGridPrivate *priv = phosh_app_grid_get_instance_private (self);

  g_signal_connect_object (priv->settings, "changed::lmi-home-slots",
                            G_CALLBACK (lmi_home_settings_changed), self, G_CONNECT_SWAPPED);
  gtk_drag_dest_set (priv->lmi_favorites_drawer, 0, lmi_home_targets,
                     G_N_ELEMENTS (lmi_home_targets), GDK_ACTION_MOVE);
  g_signal_connect (priv->lmi_favorites_drawer, "drag-motion", G_CALLBACK (lmi_home_drag_motion), self);
  g_signal_connect (priv->lmi_favorites_drawer, "drag-leave", G_CALLBACK (lmi_home_drag_leave), self);
  lmi_home_rebuild (self);
}
