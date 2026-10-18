/* SPDX-License-Identifier: GPL-3.0-or-later */
static void
lmi_home_remove_activated (GSimpleAction *action, GVariant *parameter, gpointer data)
{
  PhoshAppGridButton *self = PHOSH_APP_GRID_BUTTON (data);
  PhoshAppGridButtonPrivate *priv = phosh_app_grid_button_get_instance_private (self);
  int slot = GPOINTER_TO_INT (g_object_get_data (G_OBJECT (self), "lmi-home-remove-slot")) - 1;
  LmiHomeDrop *drop;

  if (slot < 0 || slot >= LMI_HOME_SLOT_COUNT || !priv->info) return;
  gtk_popover_popdown (GTK_POPOVER (priv->popover));
  drop = g_new0 (LmiHomeDrop, 1);
  drop->settings = g_settings_new ("sm.puri.phosh");
  drop->key = g_strdup ("lmi-home-slots");
  drop->before = g_settings_get_strv (drop->settings, drop->key);
  if (g_strv_length (drop->before) != LMI_HOME_SLOT_COUNT ||
      g_strcmp0 (drop->before[slot], g_app_info_get_id (priv->info)) != 0) {
    lmi_home_drop_free (drop);
    return;
  }
  drop->after = g_strdupv (drop->before);
  g_free (drop->after[slot]);
  drop->after[slot] = g_strdup ("");
  /* Rebuild only after the menu activation has returned. */
  g_idle_add_full (G_PRIORITY_DEFAULT_IDLE, lmi_home_drop_apply, drop, lmi_home_drop_free);
}
