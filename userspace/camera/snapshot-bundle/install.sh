#!/bin/bash
# Runs inside an offline image; never enables or starts camera acquisition.
set -euo pipefail
test "$(id -u)" -eq 0
test -f /usr/sbin/policy-rc.d
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
(cd "$src"; sha256sum -c SHA256SUMS)
test "$(getent passwd 1000 | cut -d: -f1)" = mobian
export DEBIAN_FRONTEND=noninteractive
apt-get install -y --no-remove --no-install-recommends gnome-snapshot=48.0.1-1
test "$(dpkg-query -W -f='${Version}' gnome-snapshot)" = 48.0.1-1
test "$(dpkg-query -W -f='${Version}' libpipewire-0.3-0t64)" = 1.4.2-1
base=/usr/local/lib/lmi-camera
for name in camera-module-capture liblmi_qti_bridge.so lmi-camera-private-context-test.so native-pipewire-source native-pipewire-v4l2-source snapshot-focus lmi-snapshot-tuning.so; do
    install -Dm755 "$src/$name" "$base/$name"
done
for name in camera-test-capture.py camera-test-rear-preview.py preview-service.py lmi-camera-super-metadata.py; do
    install -Dm644 "$src/$name" "$base/$name"
done
install -Dm755 "$src/lmi-snapshot" /usr/local/bin/lmi-snapshot
install -Dm644 "$src/lmi-camera-preview.service" /etc/systemd/system/lmi-camera-preview.service
install -Dm644 "$src/49-lmi-camera.rules" /etc/polkit-1/rules.d/49-lmi-camera.rules
install -Dm644 "$src/org.gnome.Snapshot.desktop" /usr/local/share/applications/org.gnome.Snapshot.desktop
install -d -o mobian -g mobian -m700 /home/mobian/.local/share/applications
install -o mobian -g mobian -m644 "$src/org.gnome.Snapshot.desktop" /home/mobian/.local/share/applications/org.gnome.Snapshot.desktop
test ! -e /etc/systemd/system/multi-user.target.wants/lmi-camera-preview.service
test -z "$(dpkg --audit)"
printf 'SNAPSHOT_AND_BACKEND_INTEGRATED_NO_ACQUISITION\n'
