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
    qt6-wayland \
    libqt6sql6-sqlite \
    qml6-module-org-kde-kquickcontrolsaddons \
    qml6-module-org-kde-purpose

audit=$(dpkg --audit)
if [[ -n $audit ]]; then
    printf '%s\n' "$audit" >&2
    exit 1
fi
