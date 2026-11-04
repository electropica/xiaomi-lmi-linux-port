#!/bin/sh
# Run as the desktop user in its live D-Bus session, using the private export.
set -eu
input=${1:?private favorites export required}
[ "$(id -u)" = 1000 ] || { echo 'run as the mobian desktop user' >&2; exit 1; }
[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ] || { echo 'desktop D-Bus session required' >&2; exit 1; }
[ -f "$input" ] || { echo 'favorites export missing' >&2; exit 1; }
command -v dconf >/dev/null || { echo 'dconf is missing' >&2; exit 1; }
value=$(cat "$input")
[ -n "$value" ] || { echo 'favorites export is empty' >&2; exit 1; }
dconf write /sm/puri/phosh/favorites "$value"
actual=$(dconf read /sm/puri/phosh/favorites)
[ "$actual" = "$value" ] || { echo 'favorites readback differs' >&2; exit 1; }
echo PHOSH_FAVORITES_RESTORED
