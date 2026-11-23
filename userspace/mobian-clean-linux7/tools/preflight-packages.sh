#!/bin/sh
# Verify external package inputs before starting a long image build.
set -eu
custom=${1:?usage: preflight-packages.sh CUSTOM_DIR BATTERY_DIR}
battery=${2:?usage: preflight-packages.sh CUSTOM_DIR BATTERY_DIR}
phosh='0.46.0-3+deb13u1+lmigaugewake3+homedrag8+esrquiet1+drawerscroll1+irqnames1+drawerpreview1+drawersearch1+draweremptysearch1+searchclose1+drawertouchfix1+drawerpreview2+pulldown1+previewdouble1+drawerlayout1+pulldownbubble1'
gsd='48.1-1+lmiquietgauge3+esrquiet1+irqnames1+sleeprefusal1+retry2'
check_dir() (
    cd "$1"
    [ -f SHA256SUMS ] || { echo "Missing SHA256SUMS: $1" >&2; exit 1; }
    count=0
    for deb in ./*.deb; do
        [ -f "$deb" ] || continue
        name=${deb#./}
        awk -v name="$name" 'length($1) == 64 && $1 !~ /[^[:xdigit:]]/ { f=$2; sub(/\r$/, "", f); sub(/^\*/, "", f); sub(/^\.\//, "", f); if (f == name) found=1 } END { exit !found }' SHA256SUMS || { echo "Missing checksum: $name" >&2; exit 1; }
        count=$((count + 1))
    done
    [ "$count" -eq "$2" ] || { echo "Expected $2 packages in $1; found $count" >&2; exit 1; }
    sha256sum -c SHA256SUMS
)
check_packages() (
    cd "$1"
    seen=' '
    for deb in ./*.deb; do
        pkg=$(dpkg-deb -f "$deb" Package)
        version=$(dpkg-deb -f "$deb" Version)
        arch=$(dpkg-deb -f "$deb" Architecture)
        case " $seen " in *" $pkg "*) echo "Duplicate package: $pkg" >&2; exit 1;; esac
        seen="$seen$pkg "
        case "$2:$pkg" in
            custom:phosh|custom:phosh-common|custom:libphosh-0.45-0|custom:phoc|custom:gnome-settings-daemon|custom:gnome-settings-daemon-common|custom:libcamera0.4|custom:libcamera-ipa|battery:battery-logger|battery:battery-viewer|battery:battery-sleep-boundaries) ;;
            *) echo "Wrong package group: $pkg in $2" >&2; exit 1 ;;
        esac
        case "$pkg" in
            phosh|phosh-common|libphosh-0.45-0) expected=$phosh ;;
            phoc) expected='0.46.0-1+lmishelldnd1+thumblinear1+thumbrows1+thumbfbo1' ;;
            gnome-settings-daemon|gnome-settings-daemon-common) expected=$gsd ;;
            libcamera0.4|libcamera-ipa) expected='0.4.0-7+lmi4' ;;
            battery-logger) expected='0.1.1' ;;
            battery-viewer) expected='0.1.13' ;;
            battery-sleep-boundaries) expected='0.1.0' ;;
            *) echo "Unexpected package: $pkg" >&2; exit 1 ;;
        esac
        [ "$version" = "$expected" ] || { echo "Wrong version: $pkg $version" >&2; exit 1; }
        case "$pkg:$arch" in
            phosh-common:all|gnome-settings-daemon-common:all|battery-sleep-boundaries:all|phosh:arm64|libphosh-0.45-0:arm64|phoc:arm64|gnome-settings-daemon:arm64|libcamera0.4:arm64|libcamera-ipa:arm64|battery-logger:arm64|battery-viewer:arm64) ;;
            *) echo "Wrong architecture: $pkg $arch" >&2; exit 1 ;;
        esac
        echo "  $pkg $version $arch"
    done
)
check_dir "$custom" 8
check_packages "$custom" custom
check_dir "$battery" 3
check_packages "$battery" battery
echo PACKAGE_PREFLIGHT_PASS
