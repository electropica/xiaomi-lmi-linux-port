#!/bin/sh
# Verify a built rootfs tarball on the host, without the phone and without
# running the image.
#
# It unpacks the tarball into a temporary directory and applies the same
# checks as RECIPE/scripts/verify-lmi-image-linux7.sh, but on the unpacked
# tree instead of inside the build chroot.
#
# Usage:  sh verify-rootfs-tarball.sh <rootfs.tar.xz>
set -eu

TAR=${1:?rootfs tarball required}
[ -f "$TAR" ] || { echo "missing $TAR" >&2; exit 1; }

fail() { echo "ROOTFS_CHECK_FAILED: $*" >&2; exit 1; }
ok()   { echo "  ok  $*"; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

echo "== unpacking =="
tar -xJf "$TAR" -C "$TMP"
R="$TMP"
[ -d "$R/etc" ] || fail "the tarball has no /etc"

echo "== the account =="
[ -d "$R/home/mobian" ] || fail "no /home/mobian"
if [ -f "$R/etc/passwd" ]; then
    grep -q '^mobian:' "$R/etc/passwd" || fail "no mobian user"
    ok "mobian user present"
fi
if [ -f "$R/etc/shadow" ]; then
    pw=$(awk -F: '$1=="mobian"{print $2}' "$R/etc/shadow")
    case "$pw" in
        ''|'!'*|'*'*) ok "mobian is locked" ;;
        *) fail "mobian has a password in the image" ;;
    esac
fi

echo "== audio routing =="
for f in \
    "$R/etc/pipewire/pipewire.conf.d/99-lmi-audio.conf" \
    "$R/home/mobian/.asoundrc" \
    "$R/usr/share/alsa/ucm2/Xiaomi/lmi/HiFi.conf" \
    "$R/usr/share/alsa/ucm2/conf.d/sm8250/Xiaomi lmi.conf"; do
    [ -f "$f" ] || fail "missing ${f#$R/}"
    ok "${f#$R/}"
done

echo "== the Phosh session and the GPU stack =="
for f in \
    "$R/etc/systemd/system/phosh-m0.service" \
    "$R/etc/systemd/system/phosh-m0.service.d/50-lmi-seat-vtnr.conf" \
    "$R/etc/systemd/system/phosh-m0.service.d/51-lmi-restart-guard.conf" \
    "$R/opt/mobian-gpu/icd.d/freedreno_icd.aarch64.json" \
    "$R/opt/mobian-gpu/lib/libvulkan_freedreno.so" \
    "$R/usr/local/libexec/lmi-clean-adsp-start" \
    "$R/usr/local/libexec/lmi-linux7-wifi-reprobe" \
    "$R/usr/local/sbin/lmi-geoclue-bss-reseed" \
    "$R/usr/local/bin/lmi-snapshot"; do
    [ -f "$f" ] || fail "missing ${f#$R/}"
    ok "${f#$R/}"
done

echo "== the firmware layer =="
n=$(ls "$R/usr/lib/firmware/qcom/sm8250/adsp.b"* 2>/dev/null | wc -l)
[ "$n" -eq 19 ] || fail "expected 19 ADSP segments, found $n"
[ -f "$R/usr/lib/firmware/qcom/sm8250/adsp.mdt" ] || fail "missing adsp.mdt"
[ -f "$R/usr/lib/firmware/qcom/sm8250/adsp.mbn" ] || fail "missing adsp.mbn"
[ -f "$R/usr/lib/firmware/ath11k/QCA6390/hw2.0/amss.bin" ] || fail "missing ath11k firmware"
[ -f "$R/usr/lib/firmware/tfa98xx.cnt" ] || fail "missing TFA firmware"
ok "firmware layer complete"

echo "== the repositories =="
grep -Eq '^deb .* trixie main( .*)?$' "$R/etc/apt/sources.list" || fail "the Debian trixie suite is missing"
grep -Eq '^deb .* trixie-updates main( .*)?$' "$R/etc/apt/sources.list" || fail "the trixie-updates suite is missing"
grep -Eq '^deb .* trixie-security main( .*)?$' "$R/etc/apt/sources.list" || fail "the trixie-security suite is missing"
grep -q '^Suites: trixie$' "$R/etc/apt/sources.list.d/mobian.sources" || fail "the Mobian suite is not trixie"
grep -q 'Pin-Priority: 700' "$R/etc/apt/preferences.d/00-mobian-priority" || fail "the Mobian priority pin is missing"
ok "repositories configured like the working handset"

echo "== the repart overlay must be absent =="
[ ! -e "$R/etc/repart.d/10-root.conf" ] || fail "the repart overlay is present"
if [ -f "$R/var/lib/dpkg/status" ]; then
    if awk '/^Package: systemd-repart$/{f=1} f&&/^Status: install ok installed$/{print "found"; exit}' \
        "$R/var/lib/dpkg/status" | grep -q found; then
        fail "systemd-repart is installed"
    fi
    ok "systemd-repart is not installed"
fi

echo "== no 4.19 era unit =="
for u in lmi-cpu-idle.service lmi-adsp-btfm.service lmi-wlan-on.service \
         lmi-cnss-daemon.service lmi-cnss-fs-ready.service lmi-pd-mapper.service \
         lmi-wlan-firmware-prepare.service lmi-adsp-boot-mainline.service \
         lmi-adsp-firmware-prepare.service lmi-android-wifi-mounts.service \
         lmi-splash-release.service lmi-venus-firmware-prepare.service \
         lmi-time-seed.service lmi-time-seed-save.service lmi-time-seed-save.timer \
         lmi-rtc-time-restore.service lmi-camera-preview.service; do
    [ ! -e "$R/etc/systemd/system/$u" ] || fail "4.19 era unit present: $u"
    [ ! -e "$R/usr/lib/systemd/system/$u" ] || fail "4.19 era unit present: $u"
done
ok "no 4.19 era unit present"

echo "== the enabled services =="
for l in \
    "$R/etc/systemd/system/multi-user.target.wants/lmi-clean-adsp.service" \
    "$R/etc/systemd/system/multi-user.target.wants/lmi-linux7-wifi-reprobe.service" \
    "$R/etc/systemd/system/multi-user.target.wants/lmi-geoclue-bss-reseed.service" \
    "$R/etc/systemd/system/graphical.target.wants/phosh-m0.service"; do
    [ -L "$l" ] || fail "not enabled: ${l#$R/}"
    expected="/etc/systemd/system/$(basename "$l")"
    [ "$(readlink "$l")" = "$expected" ] || fail "unexpected service link: ${l#$R/}"
    [ -f "$R$expected" ] || fail "missing service target: $expected"
    ok "enabled ${l#$R/}"
done

echo
echo "ROOTFS_CHECK_PASSED"
