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
    GtkWidget *box;

    if (app) {
      cell = phosh_app_grid_button_new (G_APP_INFO (app));
      g_object_set_data (G_OBJECT (cell), "lmi-home-remove-slot", GINT_TO_POINTER (i + 1));
      box = GTK_WIDGET (gtk_widget_get_template_child (cell, PHOSH_TYPE_APP_GRID_BASE_BUTTON, "box"));
      gtk_widget_set_valign (box, GTK_ALIGN_CENTER);
      gtk_box_set_spacing (GTK_BOX (box), 3);
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
  /* Only actual slots/favorites accept drops; the deck must not steal them. */
  g_object_set_data (G_OBJECT (self), "lmi-home-drag-deck", priv->lmi_favorites_drawer);
  lmi_home_rebuild (self);
}
