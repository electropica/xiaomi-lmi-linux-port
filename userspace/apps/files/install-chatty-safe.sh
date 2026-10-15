#!/bin/bash
set -euo pipefail

# lmi downstream video enumeration requires a process-local plugin view.
files=${LMI_APPS_FILES_DIR:-"$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../files" && pwd)"}
plugins=/usr/lib/aarch64-linux-gnu/gstreamer-1.0
view=/usr/local/lib/lmi-chatty/gstreamer
test -d "$plugins"
test -f /usr/share/applications/sm.puri.Chatty.desktop
test -d /home/mobian
install -m 0755 "$files/lmi-chatty-safe" /usr/local/bin/lmi-chatty-safe
install -d -m 0755 "$view"
for plugin in "$plugins"/*.so; do
    test -f "$plugin" || continue
    name=${plugin##*/}
    case "$name" in libgstvideo4linux2.so|libgstuvch264.so) continue;; esac
    ln -sfn -- "$plugin" "$view/$name"
done
for name in libgstvideo4linux2.so libgstuvch264.so; do
    # Do not silently reuse an unsafe plugin view from an earlier installation.
    test ! -e "$view/$name" && test ! -L "$view/$name"
done

install -d -m 0755 /usr/local/share/applications
install -m 0644 /usr/share/applications/sm.puri.Chatty.desktop /usr/local/share/applications/sm.puri.Chatty.desktop
sed -i -e 's|^Exec=chatty|Exec=/usr/local/bin/lmi-chatty-safe|' \
    -e 's|^DBusActivatable=true$|DBusActivatable=false|' \
    /usr/local/share/applications/sm.puri.Chatty.desktop
grep -q '^Exec=/usr/local/bin/lmi-chatty-safe %u$' /usr/local/share/applications/sm.puri.Chatty.desktop
grep -q '^DBusActivatable=false$' /usr/local/share/applications/sm.puri.Chatty.desktop

# The daemon and D-Bus activation must not bypass the protected manual launcher.
install -d -o mobian -g mobian -m 0755 /home/mobian/.config/autostart \
    /home/mobian/.local/share/applications /home/mobian/.local/share/dbus-1/services
install -o mobian -g mobian -m 0644 /usr/local/share/applications/sm.puri.Chatty.desktop \
    /home/mobian/.local/share/applications/sm.puri.Chatty.desktop
cat > /home/mobian/.config/autostart/sm.puri.Chatty-daemon.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Chats (daemon)
Hidden=true
EOF
cat > /home/mobian/.local/share/dbus-1/services/sm.puri.Chatty.service <<'EOF'
[D-BUS Service]
Name=sm.puri.Chatty
Exec=/usr/local/bin/lmi-chatty-safe --gapplication-service
EOF
chown mobian:mobian /home/mobian/.config/autostart/sm.puri.Chatty-daemon.desktop \
    /home/mobian/.local/share/dbus-1/services/sm.puri.Chatty.service
chmod 0644 /home/mobian/.config/autostart/sm.puri.Chatty-daemon.desktop \
    /home/mobian/.local/share/dbus-1/services/sm.puri.Chatty.service
