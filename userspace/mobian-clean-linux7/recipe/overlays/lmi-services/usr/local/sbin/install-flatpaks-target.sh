#!/bin/sh
# Install the nine Flatpak applications on the TARGET device, system wide.
#
# This is deliberately NOT part of the image build. "flatpak --system install"
# needs the flatpak-system-helper D-Bus service, which does not exist inside
# a debootstrap chroot; running it during the build would fail or produce a
# half-installed system installation. On the device the helper is present and
# the operation works.
#
# The application list and the expected commits were taken from the working
# handset on 2026-11-01 and compared against the Flathub aarch64/stable
# references. The commits are recorded so a later run can prove that the same
# builds are installed.
#
# Usage:  sudo install-flatpaks-target.sh [--verify]
set -eu

APPS='io.bassi.Amberol org.gnome.Calculator org.gnome.Calendar org.gnome.Maps org.gnome.Papers org.gnome.Showtime org.gnome.Snapshot org.gnome.TextEditor org.gnome.Weather'

RECORD=/var/lib/lmi-image/flatpak-commits.txt
VERIFY_ONLY=0
[ "${1:-}" = "--verify" ] && VERIFY_ONLY=1

if [ "$VERIFY_ONLY" = 0 ]; then
    echo "== adding the flathub system remote =="
    if ! flatpak --system remotes --columns=name 2>/dev/null | grep -qx flathub; then
        flatpak --system remote-add --if-not-exists flathub \
            https://dl.flathub.org/repo/flathub.flatpakrepo
    fi

    echo "== installing the applications =="
    set --
    for a in $APPS; do set -- "$@" "app/$a/aarch64/stable"; done
    flatpak --system install --noninteractive --assumeyes --arch=aarch64 flathub "$@"
fi

echo "== recording the installed commits =="
install -d -m 0755 /var/lib/lmi-image
temp=$(mktemp /var/lib/lmi-image/.flatpak-commits.XXXXXXXX)
trap 'rm -f "$temp"' EXIT HUP INT TERM
for a in $APPS; do
    c=$(flatpak --system info --show-commit "app/$a/aarch64/stable" 2>/dev/null || true)
    if ! printf '%s\n' "$c" | grep -Eq '^[0-9a-f]{64}$'; then
        echo "not installed: $a" >&2
        exit 1
    fi
    printf '%s %s\n' "$a" "$c" >> "$temp"
    echo "  $a $c"
done
mv "$temp" "$RECORD"

echo "FLATPAKS_READY record=$RECORD"
