/* SPDX-License-Identifier: GPL-3.0-or-later */
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wayland-client.h>
#include "wlr-foreign-toplevel-management-unstable-v1-client-protocol.h"

struct window {
  struct window *next;
  struct zwlr_foreign_toplevel_handle_v1 *handle;
  bool snapshot, active;
};
static struct window *windows;
static int last = -1;
static bool running = true;
static struct zwlr_foreign_toplevel_manager_v1 *manager;

static void report (void) {
  int active = 0;
  for (struct window *w = windows; w; w = w->next)
    if (w->snapshot && w->active) active = 1;
  if (active != last) { printf ("%d\n", active); fflush (stdout); last = active; }
}
static void title (void *data, struct zwlr_foreign_toplevel_handle_v1 *h, const char *s) {}
static void app_id (void *data, struct zwlr_foreign_toplevel_handle_v1 *h, const char *s) {
  struct window *w = data;
  w->snapshot = !strcmp (s, "org.gnome.Snapshot");
}
static void output (void *data, struct zwlr_foreign_toplevel_handle_v1 *h, struct wl_output *o) {}
static void state (void *data, struct zwlr_foreign_toplevel_handle_v1 *h, struct wl_array *a) {
  struct window *w = data;
  uint32_t *p;
  w->active = false;
  wl_array_for_each (p, a)
    if (*p == ZWLR_FOREIGN_TOPLEVEL_HANDLE_V1_STATE_ACTIVATED) w->active = true;
}
static void done (void *data, struct zwlr_foreign_toplevel_handle_v1 *h) { report (); }
static void parent (void *data, struct zwlr_foreign_toplevel_handle_v1 *h, struct zwlr_foreign_toplevel_handle_v1 *p) {}
static void closed (void *data, struct zwlr_foreign_toplevel_handle_v1 *h) {
  struct window *w = data, **link = &windows;
  while (*link && *link != w) link = &(*link)->next;
  if (*link) *link = w->next;
  zwlr_foreign_toplevel_handle_v1_destroy (h);
  free (w); report ();
}
static const struct zwlr_foreign_toplevel_handle_v1_listener handle_listener = {
  .title=title, .app_id=app_id, .output_enter=output, .output_leave=output,
  .state=state, .done=done, .closed=closed, .parent=parent
};
static void toplevel (void *data, struct zwlr_foreign_toplevel_manager_v1 *m, struct zwlr_foreign_toplevel_handle_v1 *h) {
  struct window *w = calloc (1, sizeof (*w));
  if (!w) { running = false; return; }
  w->handle=h; w->next=windows; windows=w;
  zwlr_foreign_toplevel_handle_v1_add_listener (h, &handle_listener, w);
}
static void finished (void *data, struct zwlr_foreign_toplevel_manager_v1 *m) { running=false; }
static const struct zwlr_foreign_toplevel_manager_v1_listener manager_listener = {
  .toplevel=toplevel, .finished=finished
};
static void global (void *data, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version) {
  if (!strcmp (interface, zwlr_foreign_toplevel_manager_v1_interface.name) && !manager) {
    manager=wl_registry_bind (registry, name, &zwlr_foreign_toplevel_manager_v1_interface, version < 3 ? version : 3);
    zwlr_foreign_toplevel_manager_v1_add_listener (manager, &manager_listener, NULL);
  }
}
static void removed (void *data, struct wl_registry *registry, uint32_t name) {}
static const struct wl_registry_listener registry_listener = {.global=global, .global_remove=removed};
int main (void) {
  struct wl_display *display = wl_display_connect (NULL);
  struct wl_registry *registry;
  if (!display) return 1;
  registry=wl_display_get_registry (display);
  wl_registry_add_listener (registry, &registry_listener, NULL);
  if (wl_display_roundtrip (display) < 0 || !manager) { wl_display_disconnect (display); return 2; }
  report ();
  while (running && wl_display_dispatch (display) >= 0) {}
  if (last != 0) { puts ("0"); fflush (stdout); }
  wl_display_disconnect (display);
  return 0;
}
