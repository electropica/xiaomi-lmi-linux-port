#!/bin/sh
# Verify the finished clean image. Every check here runs inside the build
# chroot, before the image is packed, so a failure stops the build instead of
# producing an image that cannot boot.
#
# The checks are the off-device equivalent of what the handset is asked to do
# at first boot. They cannot replace a boot test on the device.
set -eu

fail() { echo "VERIFY_FAILED: $*" >&2; exit 1; }
ok()   { echo "  ok  $*"; }

echo "== 1. custom lmi packages are the patched builds =="
while IFS='|' read -r package expected; do
    actual=$(dpkg-query -W -f='${Version}' "$package" 2>/dev/null || true)
    [ "$actual" = "$expected" ] || fail "$package is $actual, expected $expected"
    ok "$package = $actual"
done <<'LMI_EXACT_PACKAGES'
gnome-settings-daemon|48.1-1+lmiquietgauge3+esrquiet1+irqnames1
gnome-settings-daemon-common|48.1-1+lmiquietgauge3+esrquiet1+irqnames1
libcamera-ipa|0.4.0-7+lmi4
libcamera0.4|0.4.0-7+lmi4
phoc|0.46.0-1+lmishelldnd1+thumblinear1+thumbrows1+thumbfbo1
phosh|0.46.0-3+deb13u1+lmigaugewake3+homedrag8+esrquiet1+drawerscroll1+irqnames1+drawerpreview1+drawersearch1+draweremptysearch1+searchclose1
phosh-common|0.46.0-3+deb13u1+lmigaugewake3+homedrag8+esrquiet1+drawerscroll1+irqnames1+drawerpreview1+drawersearch1+draweremptysearch1+searchclose1
LMI_EXACT_PACKAGES

echo "== 2. custom packages are held against the priority 700 repository =="
for p in phosh phosh-common phoc gnome-settings-daemon gnome-settings-daemon-common libcamera0.4 libcamera-ipa; do
    dpkg-query -W -f='${Status}\n' "$p" 2>/dev/null | grep -q 'hold ok installed' \
        || fail "$p is not held; the Mobian repository would replace it"
done
ok "all seven custom packages are held"

echo "== 3. pinned Debian updates =="
while IFS='|' read -r package minimum; do
    actual=$(dpkg-query -W -f='${Version}' "$package" 2>/dev/null || true)
    [ -n "$actual" ] || fail "$package is not installed"
    dpkg --compare-versions "$actual" ge "$minimum" || fail "$package is $actual, expected at least $minimum"
    ok "$package = $actual"
done <<'LMI_MINIMUM_UPDATES'
apt|3.0.4
libapt-pkg7.0|3.0.4
libnss3|2:3.110-1+deb13u5
linux-perf|6.12.115-2
tzdata|2026f-0+deb13u1
LMI_MINIMUM_UPDATES

echo "== 4. the image cannot repartition anything =="
if dpkg-query -W -f='${db:Status-Status}' systemd-repart 2>/dev/null | grep -qx installed; then
    fail "systemd-repart is installed"
fi
[ ! -e /etc/repart.d/10-root.conf ] || fail "the repart overlay is present"
for t in repart growfs x-systemd-growfs; do
    :
done
ok "no systemd-repart, no repart overlay"

echo "== 5. the account exists, is UID 1000 and is locked =="
uid=$(id -u mobian 2>/dev/null || echo '')
[ "$uid" = 1000 ] || fail "mobian UID is ${uid:-absent}, expected 1000"
shadow=$(getent shadow mobian | cut -d: -f2)
case "$shadow" in
    ''|'!'*|'*'*) ok "mobian is locked" ;;
    *) fail "mobian has a password set; it must be provisioned on the target" ;;
esac

echo "== 6. audio routing is in place =="
check_file() {
    [ -f "$1" ] || fail "missing $1"
    mode=$(stat -c '%a' "$1")
    [ "$mode" = "$2" ] || fail "$1 has mode $mode, expected $2"
    ok "$1 (mode $mode)"
}
check_file /etc/pipewire/pipewire.conf.d/99-lmi-audio.conf 644
check_file /home/mobian/.asoundrc 644
check_file /usr/share/alsa/ucm2/Xiaomi/lmi/HiFi.conf 644
check_file "/usr/share/alsa/ucm2/conf.d/sm8250/Xiaomi lmi.conf" 644
[ "$(stat -c '%U' /home/mobian/.asoundrc)" = mobian ] || fail "asoundrc is not owned by mobian"
ok "asoundrc owner is mobian"

echo "== 7. the Phosh session unit and the GPU stack =="
check_file /etc/systemd/system/phosh-m0.service 644
check_file /etc/phosh/phoc.ini 644
grep -qx 'scale = 3' /etc/phosh/phoc.ini || fail "Phoc scale 3 is missing"
check_file /etc/systemd/system/phosh-m0.service.d/50-lmi-seat-vtnr.conf 644
check_file /etc/systemd/system/phosh-m0.service.d/51-lmi-restart-guard.conf 644
[ -f /opt/mobian-gpu/icd.d/freedreno_icd.aarch64.json ] || fail "missing the Vulkan ICD"
[ -f /opt/mobian-gpu/lib/libvulkan_freedreno.so ] || fail "missing the freedreno Vulkan driver"
ok "GPU stack present"

echo "== 8. the Linux 7 device services are enabled =="
for u in lmi-clean-adsp.service lmi-linux7-wifi-reprobe.service \
         lmi-geoclue-bss-reseed.service phosh-m0.service; do
    systemctl --root=/ is-enabled "$u" >/dev/null 2>&1 || fail "$u is not enabled"
    ok "$u enabled"
done

echo "== 9. no 4.19 era unit is present =="
for u in lmi-cpu-idle.service lmi-adsp-btfm.service lmi-wlan-on.service \
         lmi-cnss-daemon.service lmi-cnss-fs-ready.service lmi-pd-mapper.service \
         lmi-wlan-firmware-prepare.service lmi-adsp-boot-mainline.service \
         lmi-adsp-firmware-prepare.service lmi-android-wifi-mounts.service \
         lmi-splash-release.service lmi-venus-firmware-prepare.service \
         lmi-time-seed.service lmi-time-seed-save.service lmi-time-seed-save.timer \
         lmi-rtc-time-restore.service lmi-camera-preview.service; do
    [ ! -e "/etc/systemd/system/$u" ] || fail "4.19 era unit present: $u"
    [ ! -e "/usr/lib/systemd/system/$u" ] || fail "4.19 era unit present: $u"
done
ok "no 4.19 era unit present"

echo "== 10. firmware layer =="
[ -f /usr/lib/firmware/qcom/sm8250/adsp.mdt ] || fail "missing adsp.mdt"
[ -f /usr/lib/firmware/qcom/sm8250/adsp.mbn ] || fail "missing adsp.mbn"
n=$(ls /usr/lib/firmware/qcom/sm8250/adsp.b* 2>/dev/null | wc -l)
[ "$n" -eq 19 ] || fail "expected 19 ADSP segments, found $n"
[ -f /usr/lib/firmware/ath11k/QCA6390/hw2.0/amss.bin ] || fail "missing ath11k firmware"
[ -f /usr/lib/firmware/tfa98xx.cnt ] || fail "missing TFA firmware"
[ -x /usr/local/libexec/lmi-clean-adsp-start ] || fail "missing the ADSP starter"
ok "firmware layer complete"

echo "== 11. the camera launcher =="
[ -x /usr/local/bin/lmi-snapshot ] || fail "missing the camera launcher"
[ -f /usr/local/share/applications/org.gnome.Snapshot.desktop ] || fail "missing the camera desktop entry"
ok "camera launcher present"

echo "== 12. repositories =="
grep -Eq '^deb .* trixie main( .*)?$' /etc/apt/sources.list || fail "the Debian trixie suite is missing"
grep -Eq '^deb .* trixie-updates main( .*)?$' /etc/apt/sources.list || fail "the trixie-updates suite is missing"
grep -Eq '^deb .* trixie-security main( .*)?$' /etc/apt/sources.list || fail "the trixie-security suite is missing"
grep -q '^Suites: trixie$' /etc/apt/sources.list.d/mobian.sources || fail "the Mobian suite is not trixie"
grep -q 'Pin-Priority: 700' /etc/apt/preferences.d/00-mobian-priority || fail "the Mobian priority pin is missing"
ok "repositories configured like the working handset"

echo "== 13. flatpak is available for post-install configuration =="
command -v flatpak >/dev/null || fail "flatpak is missing"
ok "flatpak available; the remote and applications remain a post-install step"

echo
echo "LMI_IMAGE_VERIFIED"
