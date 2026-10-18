#!/bin/bash
# Runs only inside the offline image chroot, with policy-rc.d installed.
set -euo pipefail
test "$(id -u)" = 0
test -f /run/lmi-current-profile/inputs/SHA256SUMS
test -f /usr/sbin/policy-rc.d
src=/run/lmi-current-profile
(cd "$src/inputs"; sha256sum -c SHA256SUMS)
export DEBIAN_FRONTEND=noninteractive
apt-get install -y --no-remove --no-install-recommends python3-gi gir1.2-gtk-3.0 psmisc \
    "$src"/inputs/upower_*.deb "$src"/inputs/libupower-glib3_*.deb \
    "$src"/inputs/gir1.2-upowerglib-1.0_*.deb \
    "$src"/inputs/phosh_*.deb "$src"/inputs/phosh-common_*.deb \
    "$src"/inputs/gnome-settings-daemon_*.deb "$src"/inputs/gnome-settings-daemon-common_*.deb
test -z "$(dpkg --audit)"
# The 4.19 extractor lacks Landlock and failed PIDFD reaping exhausted user tasks.
# Keep files/databases; disable only incompatible background metadata indexing.
systemctl --global mask localsearch-3.service
for p in upower libupower-glib3 gir1.2-upowerglib-1.0; do
    test "$(dpkg-query -W -f='${Version}' "$p")" = 1.90.9-1+lmi1
done
for p in phosh phosh-common; do
    test "$(dpkg-query -W -f='${Version}' "$p")" = 0.46.0-3+deb13u1+lmigaugewake3
done
for p in gnome-settings-daemon gnome-settings-daemon-common; do
    test "$(dpkg-query -W -f='${Version}' "$p")" = 48.1-1+lmiquietgauge3
done
# Enable only the paired qualified quiet-resume paths; no debug environment.
install -Dm644 "$src/power/phosh-quiet-resume.conf" /etc/systemd/user/mobi.phosh.Shell.service.d/60-lmi-quiet-gauge-resume.conf
install -Dm644 "$src/power/gsd-quiet-resume.conf" /etc/systemd/user/org.gnome.SettingsDaemon.Power.service.d/60-lmi-quiet-gauge-resume.conf
install -Dm644 "$src/inputs/tfa98xx.cnt" /lib/firmware/postmarketos/tfa98xx.cnt
test "$(dpkg-query -W -f='${Version}' krecorder)" = 25.04.0-2
test "$(getent passwd 1000 | cut -d: -f1)" = mobian
home=/home/mobian
install -d -o mobian -g mobian -m700 "$home/.config" "$home/.config/pipewire" "$home/.config/pipewire/pipewire.conf.d"
test ! -e "$home/.asoundrc"
cat "$src/audio/lmi-speaker.asoundrc" "$src/audio/lmi-microphone.asoundrc" > "$home/.asoundrc"
chown mobian:mobian "$home/.asoundrc"
chmod 644 "$home/.asoundrc"
for f in 90-lmi-speaker.conf 91-lmi-microphone.conf; do
    install -o mobian -g mobian -m644 "$src/audio/$f" "$home/.config/pipewire/pipewire.conf.d/$f"
done
install -o mobian -g mobian -m644 "$src/audio/lmi-krecorder.conf" "$home/.config/krecorder.conf"
install -Dm755 "$src/apps/lmi-flashlight.py" /usr/local/bin/lmi-flashlight
install -Dm644 "$src/apps/lmi-flashlight.desktop" /usr/local/share/applications/lmi-flashlight.desktop
# Use the complete shared fix, including desktop activation and daemon autostart.
LMI_APPS_FILES_DIR="$src/apps" bash "$src/apps/install-chatty-safe.sh"
install -Dm755 "$src/power/lmi-cpu-idle" /usr/local/sbin/lmi-cpu-idle
install -Dm644 "$src/power/lmi-cpu-idle.service" /etc/systemd/system/lmi-cpu-idle.service
install -Dm644 /dev/null /etc/lmi/cpu-idle-opt-in
install -Dm644 /dev/null /etc/upower/lmi-trust-battery-status
install -Dm644 "$src/power/99-lmi-upower-status.rules" /etc/udev/rules.d/99-lmi-upower-status.rules
systemctl enable lmi-cpu-idle.service
# Suspend-only NPU bandwidth policy; no background polling or kernel replacement.
install -Dm755 "$src/power/lmi-npu-suspend" /usr/local/sbin/lmi-npu-suspend
install -Dm755 "$src/power/lmi-npu-suspend-hook" /usr/lib/systemd/system-sleep/90-lmi-npu-suspend
install -Dm644 "$src/power/90-lmi-npu-suspend.conf" /etc/systemd/system/systemd-suspend.service.d/90-lmi-npu-suspend.conf
install -Dm644 /dev/null /etc/lmi/npu-suspend-opt-in
install -Dm644 "$src/power/94_lmi-current-power.gschema.override" \
    /usr/share/glib-2.0/schemas/94_lmi-current-power.gschema.override
glib-compile-schemas --strict /usr/share/glib-2.0/schemas
test "$(env GSETTINGS_BACKEND=memory gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type)" = "'suspend'"
test "$(env GSETTINGS_BACKEND=memory gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type)" = "'nothing'"
test "$(env GSETTINGS_BACKEND=memory gsettings get sm.puri.phosh.notifications wakeup-screen-triggers)" = "@as []"
test -f "/usr/share/zoneinfo/${M1_TIMEZONE:-Europe/Paris}"
ln -sf "/usr/share/zoneinfo/${M1_TIMEZONE:-Europe/Paris}" /etc/localtime
printf '%s\n' "${M1_TIMEZONE:-Europe/Paris}" > /etc/timezone
install -Dm644 "$src/inputs/SHA256SUMS" /usr/share/lmi-current-profile/INPUT-SHA256SUMS
# Initialize a build-time clock floor; never write the hardware RTC.
test ! -e /var/lib/lmi-time-seed
test ! -L /var/lib/lmi-time-seed
install -Dm755 "$src/time-seed/usr/local/libexec/lmi-time-seed" /usr/local/libexec/lmi-time-seed
for unit in lmi-time-seed.service lmi-time-seed-save.service lmi-time-seed-save.timer; do
    install -Dm644 "$src/time-seed/etc/systemd/system/$unit" "/etc/systemd/system/$unit"
done
DERIVED_PROFILE=time-seed DERIVED_BUILD_EPOCH="$(date -u +%s)" \
    /bin/sh "$src/initialize-time-seed.sh"
install -Dm755 "$src/profile/lmi-venus-firmware-prepare" /usr/local/sbin/lmi-venus-firmware-prepare
install -Dm644 "$src/profile/lmi-venus-firmware-prepare.service" /etc/systemd/system/lmi-venus-firmware-prepare.service
systemctl enable lmi-venus-firmware-prepare.service
install -Dm644 "$src/PROFILE.txt" /usr/share/lmi-current-profile/PROFILE.txt
printf 'CURRENT_LMI_PROFILE_INSTALLED\n'
