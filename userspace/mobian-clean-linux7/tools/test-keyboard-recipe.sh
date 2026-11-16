#!/bin/sh
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")/../recipe" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
mkdir -p "$tmp/etc/systemd/user"
cp "$base/overlays/lmi-services/etc/systemd/user/lmi-osk-hide-button.service" "$tmp/etc/systemd/user/"
systemctl --root="$tmp" --global enable lmi-osk-hide-button.service
test -L "$tmp/etc/systemd/user/graphical-session.target.wants/lmi-osk-hide-button.service"
for script in install-lmi-debs-linux7.sh install-battery-debs-linux7.sh setup-lmi-hardware-linux7.sh setup-system-linux7.sh verify-lmi-image-linux7.sh; do
    sh -n "$base/scripts/$script"
done
python3 -m py_compile "$base/overlays/lmi-services/usr/local/libexec/lmi-osk-hide-button.py"
echo KEYBOARD_RECIPE_CHECK_PASS
