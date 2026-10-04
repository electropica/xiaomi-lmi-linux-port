#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get install -y --no-install-recommends \
    epiphany-browser \
    gnome-console \
    gnome-calculator \
    gnome-text-editor \
    nautilus \
    xdg-desktop-portal \
    xdg-desktop-portal-gnome \
    dbus-bin \
    papers \
    showtime \
    amberol \
    gnome-clocks \
    feedbackd \
    libcanberra-pulse \
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
apps_files=${LMI_APPS_FILES_DIR:-"$script_dir/../files"}
install -m 0755 "$apps_files/lmi-photos" /usr/local/bin/lmi-photos
install -m 0755 "$apps_files/lmi-photos-thumbnails" /usr/local/bin/lmi-photos-thumbnails
install -Dm 0644 /usr/share/applications/org.kde.koko.desktop /usr/local/share/applications/org.kde.koko.desktop
sed -i 's|^Exec=koko\( .*\)\?$|Exec=/usr/local/bin/lmi-photos %U|' /usr/local/share/applications/org.kde.koko.desktop
grep -q '^Exec=/usr/local/bin/lmi-photos %U$' /usr/local/share/applications/org.kde.koko.desktop


# Nautilus 48 provides a usable mobile Save/Open dialog through the GNOME
# portal. Keep Phosh's other portal preferences unchanged.
install -m 0755 "$apps_files/lmi-text-editor" /usr/local/bin/lmi-text-editor
install -Dm 0644 "$apps_files/phosh-portals.conf" /etc/xdg/xdg-desktop-portal/phosh-portals.conf
install -Dm 0644 /usr/share/applications/org.gnome.TextEditor.desktop /usr/local/share/applications/org.gnome.TextEditor.desktop
sed -i -e 's|^Exec=gnome-text-editor|Exec=/usr/local/bin/lmi-text-editor|' -e 's|^DBusActivatable=true$|DBusActivatable=false|' /usr/local/share/applications/org.gnome.TextEditor.desktop
grep -q '^Exec=/usr/local/bin/lmi-text-editor %U$' /usr/local/share/applications/org.gnome.TextEditor.desktop


# Recorder: load the existing KDE/Breeze theme only in this process.
# Preserve upstream translations and use the normal app binary.
install -m 0755 "$apps_files/lmi-recorder" /usr/local/bin/lmi-recorder
install -Dm 0644 /usr/share/applications/org.kde.krecorder.desktop /usr/local/share/applications/org.kde.krecorder.desktop
sed -i 's|^Exec=krecorder$|Exec=/usr/local/bin/lmi-recorder|' /usr/local/share/applications/org.kde.krecorder.desktop
grep -q '^Exec=/usr/local/bin/lmi-recorder$' /usr/local/share/applications/org.kde.krecorder.desktop


# Calculator has its own keypad; suppress automatic OSK only in this app.
install -m 0755 "$apps_files/lmi-calculator" /usr/local/bin/lmi-calculator
install -Dm 0644 /usr/share/applications/org.gnome.Calculator.desktop /usr/local/share/applications/org.gnome.Calculator.desktop
sed -i -e 's|^Exec=gnome-calculator|Exec=/usr/local/bin/lmi-calculator|' -e 's|^DBusActivatable=true$|DBusActivatable=false|' /usr/local/share/applications/org.gnome.Calculator.desktop
grep -q '^Exec=/usr/local/bin/lmi-calculator' /usr/local/share/applications/org.gnome.Calculator.desktop


# Contacts: app-only Cairo workaround for the observed deletion-dialog crash.
install -m 0755 "$apps_files/lmi-contacts" /usr/local/bin/lmi-contacts
install -Dm 0644 /usr/share/applications/org.gnome.Contacts.desktop /usr/local/share/applications/org.gnome.Contacts.desktop
sed -i -e 's|^Exec=gnome-contacts|Exec=/usr/local/bin/lmi-contacts|' -e 's|^DBusActivatable=true$|DBusActivatable=false|' /usr/local/share/applications/org.gnome.Contacts.desktop
grep -q '^Exec=/usr/local/bin/lmi-contacts' /usr/local/share/applications/org.gnome.Contacts.desktop
grep -q '^DBusActivatable=false$' /usr/local/share/applications/org.gnome.Contacts.desktop
