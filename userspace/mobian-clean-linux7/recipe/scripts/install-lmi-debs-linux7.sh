#!/bin/sh
# Install, in one APT transaction group:
#   1. the five Debian point updates the image requires, at pinned versions;
#   2. the base runtime packages the lmi session needs;
#   3. the seven custom lmi .deb packages, forced over the repository builds.
#
# Ordering matters. The Mobian repository has Pin-Priority 700, so a plain
# "apt install mobian-phosh" would pull the repository phosh/phoc/GSD and
# silently replace Julien's patched builds. The custom packages are therefore
# installed last, with --allow-downgrades, and then held.
#
# The five update versions are pinned, not "latest". That makes the build
# reproducible and makes a superseded version fail loudly instead of drifting.
# Refresh them deliberately with CHECKS/probe-debian-versions.sh.
set -eu

DEB_DIR=/var/lib/lmi-image-staging/lmi-debs
export DEBIAN_FRONTEND=noninteractive

PIN_APT=3.0.4
PIN_LIBAPT=3.0.4
PIN_LIBNSS3=2:3.110-1+deb13u5
PIN_LINUXPERF=6.12.115-2
PIN_TZDATA=2026f-0+deb13u1

CUSTOM_PACKAGES='phosh phosh-common phoc gnome-settings-daemon gnome-settings-daemon-common libcamera0.4 libcamera-ipa'

BASE_RUNTIME='
dbus
systemd-sysv
seatd
pipewire
pipewire-audio
pipewire-alsa
pipewire-pulse
wireplumber
alsa-utils
alsa-ucm-conf
network-manager
upower
gnome-clocks
squeekboard
xdg-desktop-portal
xdg-desktop-portal-gtk
xdg-desktop-portal-gnome
geoclue-2.0
flatpak
gnome-calls
grim
'

# Never start services while the image is being assembled.
created_policy=0
if [ ! -e /usr/sbin/policy-rc.d ] && [ ! -L /usr/sbin/policy-rc.d ]; then
    printf '#!/bin/sh\n# lmi-build-policy-20261104\nexit 101\n' > /usr/sbin/policy-rc.d
    chmod 0755 /usr/sbin/policy-rc.d
    created_policy=1
fi
cleanup() {
    if [ "$created_policy" = 1 ] && [ -f /usr/sbin/policy-rc.d ] &&
       grep -qx '# lmi-build-policy-20261104' /usr/sbin/policy-rc.d; then
        rm -f /usr/sbin/policy-rc.d
    fi
}
trap cleanup EXIT HUP INT TERM

echo "== verifying the custom package set =="
cd "$DEB_DIR"
sha256sum -c SHA256SUMS

set -- ./*.deb
[ "$#" -eq 7 ] || { echo "expected 7 custom packages, found $#" >&2; exit 1; }

echo "== apt-get update =="
apt-get update

echo "== base runtime packages =="
# shellcheck disable=SC2086
apt-get install -y --no-install-recommends $BASE_RUNTIME

echo "== pinned Debian updates =="
for spec in "apt=$PIN_APT" "libapt-pkg7.0=$PIN_LIBAPT" "libnss3=$PIN_LIBNSS3" \
            "linux-perf=$PIN_LINUXPERF" "tzdata=$PIN_TZDATA"; do
    if ! apt-get install -y --no-install-recommends "$spec"; then
        echo "PINNED VERSION UNAVAILABLE: $spec" >&2
        echo "Refresh the pins with CHECKS/probe-debian-versions.sh if this is expected." >&2
        exit 1
    fi
done

echo "== custom lmi packages =="
# --allow-downgrades lets a local file win even when the repository carries a
# higher version, which is exactly the situation the priority-700 pin creates.
if ! apt-get install -y --no-install-recommends --allow-downgrades "$@"; then
    echo "custom package installation failed" >&2
    exit 1
fi

echo "== holding the custom packages =="
# shellcheck disable=SC2086
apt-mark hold $CUSTOM_PACKAGES

echo "== checking the resulting versions =="
for p in $CUSTOM_PACKAGES; do
    v=$(dpkg-query -W -f='${Version}' "$p" 2>/dev/null || true)
    [ -n "$v" ] || { echo "custom package missing after install: $p" >&2; exit 1; }
    case "$p" in
        phosh|phosh-common) want='0.46.0-3+deb13u1+lmigaugewake3+homedrag8+esrquiet1+drawerscroll1+irqnames1+drawerpreview1+drawersearch1+draweremptysearch1+searchclose1' ;;
        phoc) want='0.46.0-1+lmishelldnd1+thumblinear1+thumbrows1+thumbfbo1' ;;
        gnome-settings-daemon|gnome-settings-daemon-common) want='48.1-1+lmiquietgauge3+esrquiet1+irqnames1' ;;
        libcamera0.4|libcamera-ipa) want='0.4.0-7+lmi4' ;;
    esac
    [ "$v" = "$want" ] || { echo "custom package replaced by the repository: $p = $v (wanted $want)" >&2; exit 1; }
    echo "  $p = $v"
done

echo "LMI_DEBS_INSTALLED"
