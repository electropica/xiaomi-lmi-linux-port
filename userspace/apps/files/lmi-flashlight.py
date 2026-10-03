#!/usr/bin/python3
"""Small lmi torch UI using logind's session-scoped LED interface."""
import os
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gio

bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
def call(path, interface, method, args=None):
    return bus.call_sync('org.freedesktop.login1', path, interface, method, args, None, Gio.DBusCallFlags.NONE, 5000, None).unpack()
session = None
for sid, uid, user, seat, path in call('/org/freedesktop/login1', 'org.freedesktop.login1.Manager', 'ListSessions')[0]:
    if int(uid) != os.getuid():
        continue
    def prop(name):
        return call(path, 'org.freedesktop.DBus.Properties', 'Get', GLib.Variant('(ss)', ('org.freedesktop.login1.Session', name)))[0]
    if prop('Class') == 'user' and prop('Active'):
        session = path
        break
if session is None:
    raise SystemExit('Aucune session utilisateur active.')

def brightness(value):
    call(session, 'org.freedesktop.login1.Session', 'SetBrightness', GLib.Variant('(ssu)', ('leds', 'flashlight', value)))

window = Gtk.Window(title='Lampe torche lmi')
window.set_default_size(320, 220)
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
box.set_border_width(24)
window.add(box)
status = Gtk.Label(label='Lampe éteinte')
box.pack_start(status, True, True, 0)
timer = 0

def switch(value):
    global timer
    try:
        brightness(value)
        if timer:
            GLib.source_remove(timer)
            timer = 0
        if value:
            timer = GLib.timeout_add_seconds(180, auto_off)
        status.set_text('Allumée — arrêt automatique après 3 min' if value else 'Lampe éteinte')
    except GLib.Error as error:
        status.set_text('Commande refusée : ' + error.message)

def auto_off():
    global timer
    timer = 0
    switch(0)
    return False

for label, value in [('Allumer', 20), ('Éteindre', 0)]:
    button = Gtk.Button(label=label)
    button.connect('clicked', lambda button, value=value: switch(value))
    box.pack_start(button, False, False, 0)

def close(window, event):
    switch(0)
    Gtk.main_quit()
    return False

window.connect('delete-event', close)
window.show_all()
Gtk.main()
