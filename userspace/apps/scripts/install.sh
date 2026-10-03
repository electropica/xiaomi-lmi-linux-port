#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get install -y --no-install-recommends \
    epiphany-browser \
    gnome-console \
    gnome-calculator \
    gnome-text-editor \
    papers \
    showtime \
    amberol \
    gnome-clocks \
    gnome-contacts \
    gnome-weather \
    gnome-calls \
    chatty \
    megapixels \
    gnome-calendar \
    gnome-maps \
    geary \
    krecorder \
    koko \
    python3 \
    libgdk-pixbuf2.0-bin \
    kio-extras \
    kf6-breeze-icon-theme \
    qml6-module-org-kde-breeze \
    qt6-wayland \
    qt6-svg-plugins \
    libqt6sql6-sqlite \
    qml6-module-org-kde-kquickcontrolsaddons \
    qml6-module-org-kde-purpose

audit=$(dpkg --audit)
if [[ -n $audit ]]; then
    printf '%s\n' "$audit" >&2
    exit 1
fi


# Preserve the upstream launcher translations while routing Photos through
# the lmi-specific rendering and thumbnail-cache workaround.
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
photos_files=${LMI_APPS_FILES_DIR:-"$script_dir/../files"}
install -m 0755 "$photos_files/lmi-photos" /usr/local/bin/lmi-photos
install -m 0755 "$photos_files/lmi-photos-thumbnails" /usr/local/bin/lmi-photos-thumbnails
install -Dm 0644 /usr/share/applications/org.kde.koko.desktop /usr/local/share/applications/org.kde.koko.desktop
sed -i 's|^Exec=koko\( .*\)\?$|Exec=/usr/local/bin/lmi-photos %U|' /usr/local/share/applications/org.kde.koko.desktop
grep -q '^Exec=/usr/local/bin/lmi-photos %U$' /usr/local/share/applications/org.kde.koko.desktop
