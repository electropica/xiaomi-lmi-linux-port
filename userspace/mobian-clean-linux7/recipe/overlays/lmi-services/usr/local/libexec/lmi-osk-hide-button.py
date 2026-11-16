#!/usr/bin/python3
"""Small Phosh overlay: hide the on-screen keyboard when it is visible."""
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gdk, Gio, GLib, Gtk, GtkLayerShell


class HideKeyboard:
    def __init__(self):
        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_name('lmi-osk-hide')
        self.window.set_decorated(False)
        self.window.set_accept_focus(False)
        self.window.set_focus_on_map(False)
        self.window.set_default_size(40, 28)
        GtkLayerShell.init_for_window(self.window)
        GtkLayerShell.set_namespace(self.window, 'lmi-osk-hide')
        GtkLayerShell.set_layer(self.window, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.BOTTOM, True)
        GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.BOTTOM, 2)
        GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.RIGHT, 4)
        GtkLayerShell.set_exclusive_zone(self.window, 0)
        GtkLayerShell.set_keyboard_mode(self.window, GtkLayerShell.KeyboardMode.NONE)
        button = Gtk.Button(label='⌄')
        button.set_name('lmi-osk-hide-button')
        button.set_size_request(40, 28)
        button.set_tooltip_text('Masquer le clavier')
        button.get_accessible().set_name('Masquer le clavier')
        button.connect('clicked', self.hide_keyboard)
        self.window.add(button)
        css = Gtk.CssProvider()
        css.load_from_data(b'#lmi-osk-hide { background: transparent; } #lmi-osk-hide-button { background: #222; color: white; border: 1px solid #888; border-radius: 8px; padding: 0; font-size: 22px; min-height: 24px; min-width: 36px; }')
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.proxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION, Gio.DBusProxyFlags.NONE, None,
            'sm.puri.OSK0', '/sm/puri/OSK0', 'sm.puri.OSK0', None)
        self.proxy.connect('g-properties-changed', self.on_properties_changed)
        self.proxy.connect('notify::g-name-owner', self.on_owner_changed)
        self.refresh()

    def on_properties_changed(self, proxy, changed, invalidated):
        self.refresh()

    def on_owner_changed(self, proxy, prop):
        self.refresh()

    def refresh(self):
        value = self.proxy.get_cached_property('Visible')
        if self.proxy.get_name_owner() and value and value.get_boolean():
            self.window.show_all()
        else:
            self.window.hide()

    def hide_keyboard(self, button):
        self.proxy.call('SetVisible', GLib.Variant('(b)', (False,)),
                        Gio.DBusCallFlags.NONE, 3000, None, self.on_hide_done)

    def on_hide_done(self, proxy, result):
        try:
            proxy.call_finish(result)
        except GLib.Error as exc:
            print('Impossible de masquer le clavier:', exc, flush=True)


if __name__ == '__main__':
    HideKeyboard()
    Gtk.main()
