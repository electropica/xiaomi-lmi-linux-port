/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <gtk/gtk.h>
#include <gio/gdesktopappinfo.h>
#include "lmi-home-order.h"

static const GtkTargetEntry lmi_home_targets[] = {
  { (char *) "application/x-lmi-phosh-app", GTK_TARGET_SAME_APP, 0 }
};

typedef struct {
  GSettings *settings;
  char *key;
  char **before;
  char **after;
} LmiHomeDrop;

static inline gboolean
lmi_home_drop_apply (gpointer data)
{
  LmiHomeDrop *drop = data;
  g_auto (GStrv) current = g_settings_get_strv (drop->settings, drop->key);

  /* Do not overwrite a simultaneous settings change. Rebuild after drag-end. */
  if (g_strv_equal ((const char * const *) current,
                    (const char * const *) drop->before))
    g_settings_set_strv (drop->settings, drop->key,
                        (const char * const *) drop->after);
  return G_SOURCE_REMOVE;
}

static inline void
lmi_home_drop_free (gpointer data)
{
  LmiHomeDrop *drop = data;
  g_object_unref (drop->settings);
  g_free (drop->key);
  g_strfreev (drop->before);
  g_strfreev (drop->after);
  g_free (drop);
}

static inline const char *
lmi_home_source_id (GdkDragContext *context)
{
  GtkWidget *source = gtk_drag_get_source_widget (context);
  return source ? g_object_get_data (G_OBJECT (source), "lmi-home-app-id") : NULL;
}

static inline void
lmi_home_drag_data_get (GtkWidget *widget, GdkDragContext *context,
                        GtkSelectionData *selection, guint info, guint time,
                        gpointer unused)
{
  const char *id = g_object_get_data (G_OBJECT (widget), "lmi-home-app-id");

  if (id)
    gtk_selection_data_set (selection, gtk_selection_data_get_target (selection),
                            8, (const guchar *) id, strlen (id));
}

static inline void
lmi_home_drag_begin (GtkWidget *widget, GdkDragContext *context, gpointer unused)
{
  const char *id = g_object_get_data (G_OBJECT (widget), "lmi-home-app-id");
  g_autoptr (GDesktopAppInfo) app = id ? g_desktop_app_info_new (id) : NULL;

  if (app && g_app_info_get_icon (G_APP_INFO (app)))
    gtk_drag_set_icon_gicon (context, g_app_info_get_icon (G_APP_INFO (app)), 16, 16);
}

static inline void
lmi_home_enable_source (GtkWidget *button, GAppInfo *app)
{
  const char *id = app ? g_app_info_get_id (app) : NULL;

  if (!id || !*id) return;
  g_object_set_data_full (G_OBJECT (button), "lmi-home-app-id", g_strdup (id), g_free);
  gtk_drag_source_set (button, GDK_BUTTON1_MASK, lmi_home_targets,
                       G_N_ELEMENTS (lmi_home_targets), GDK_ACTION_MOVE);
  g_signal_connect (button, "drag-data-get", G_CALLBACK (lmi_home_drag_data_get), NULL);
  g_signal_connect (button, "drag-begin", G_CALLBACK (lmi_home_drag_begin), NULL);
}

static inline void
lmi_home_drag_received (GtkWidget *widget, GdkDragContext *context, int x, int y,
                        GtkSelectionData *selection, guint info, guint time,
                        gpointer unused)
{
  const char *source = lmi_home_source_id (context);
  const char *favorite = g_object_get_data (G_OBJECT (widget), "lmi-favorite-target");
  int slot = GPOINTER_TO_INT (g_object_get_data (G_OBJECT (widget), "lmi-home-slot")) - 1;
  int size = gtk_selection_data_get_length (selection);
  LmiHomeDrop *drop;
  g_autofree char *payload = NULL;

  if (!source || size <= 0 || size > 1024) goto reject;
  payload = g_strndup ((const char *) gtk_selection_data_get_data (selection), size);
  if (strlen (payload) != (gsize) size || !g_str_equal (source, payload)) goto reject;
  if (!favorite && slot < 0) goto reject;

  drop = g_new0 (LmiHomeDrop, 1);
  drop->settings = g_settings_new ("sm.puri.phosh");
  drop->key = g_strdup (favorite ? "favorites" : "lmi-home-slots");
  drop->before = g_settings_get_strv (drop->settings, drop->key);
  drop->after = favorite ? lmi_favorites_move ((const char * const *) drop->before, source, favorite)
                         : lmi_home_place ((const char * const *) drop->before, source, slot);
  if (!drop->after) {
    lmi_home_drop_free (drop);
    goto reject;
  }
  gtk_drag_finish (context, TRUE, FALSE, time);
  g_idle_add_full (G_PRIORITY_DEFAULT_IDLE, lmi_home_drop_apply, drop, lmi_home_drop_free);
  return;
reject:
  gtk_drag_finish (context, FALSE, FALSE, time);
}

static inline void
lmi_home_enable_target (GtkWidget *widget, const char *favorite, int slot)
{
  if (favorite)
    g_object_set_data_full (G_OBJECT (widget), "lmi-favorite-target", g_strdup (favorite), g_free);
  else
    g_object_set_data (G_OBJECT (widget), "lmi-home-slot", GINT_TO_POINTER (slot + 1));
  gtk_drag_dest_set (widget, GTK_DEST_DEFAULT_ALL, lmi_home_targets,
                     G_N_ELEMENTS (lmi_home_targets), GDK_ACTION_MOVE);
  g_signal_connect (widget, "drag-data-received", G_CALLBACK (lmi_home_drag_received), NULL);
}
