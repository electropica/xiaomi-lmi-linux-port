#!/bin/sh
# Install the lmi hardware and session layer into the clean image.
#
# What this does, and why each part is needed:
#
#  * The GPU stack in /opt/mobian-gpu (Mesa gallium, EGL, GLESv2 and the
#    freedreno Vulkan ICD) is not provided by any Debian or Mobian package.
#    The live phosh-m0.service points LD_LIBRARY_PATH at it and
#    VK_ICD_FILENAMES at its ICD file. Without it the graphical session has
#    no GLES2 renderer and no Vulkan driver.
#
#  * phosh-m0.service is likewise not packaged: upstream mobian-phosh ships
#    phosh.service. The live unit carries the GPU-68 environment, the
#    French locale and the seat0/VT handling. It is provided here verbatim
#    together with its two reviewed drop-ins.
#
#  * The Linux 7 device services are enabled: ADSP (speaker route), the
#    Wi-Fi reprobe and the GeoClue BSS reseed. The 4.19 era services are
#    deliberately NOT re-enabled: lmi-cpu-idle, lmi-adsp-btfm,
#    lmi-wlan-on, lmi-cnss-daemon and lmi-pd-mapper are either guarded to
#    an older kernel or superseded by the ath11k path.
#
#  * The units are enabled offline with systemctl --root, because a chroot
#    has no running systemd.
set -eu

USER_NAME=${1:-mobian}

echo "== GPU stack =="
[ -d /opt/mobian-gpu/lib ] || { echo 'missing /opt/mobian-gpu/lib' >&2; exit 1; }
[ -f /opt/mobian-gpu/icd.d/freedreno_icd.aarch64.json ] || { echo 'missing Vulkan ICD' >&2; exit 1; }
chown -R root:root /opt/mobian-gpu
find /opt/mobian-gpu -type d -exec chmod 0755 {} +
find /opt/mobian-gpu -type f -exec chmod 0644 {} +

echo "== helper permissions =="
chmod 0755 /usr/local/libexec/lmi-clean-adsp-start
chmod 0755 /usr/local/libexec/lmi-linux7-wifi-reprobe
chmod 0755 /usr/local/sbin/lmi-geoclue-bss-reseed
chmod 0755 /usr/local/sbin/provision-account-target.sh
chmod 0755 /usr/local/sbin/install-flatpaks-target.sh
chmod 0755 /usr/local/bin/lmi-snapshot
chmod 0644 /usr/local/share/applications/org.gnome.Snapshot.desktop
chmod 0644 /usr/local/share/applications/gnome-location-panel.desktop
chmod 0644 /etc/udev/rules.d/70-lmi-dma-heap.rules
chmod 0644 /usr/share/glib-2.0/schemas/95_lmi-home-drawer.gschema.override
glib-compile-schemas --strict /usr/share/glib-2.0/schemas
chmod 0644 /etc/systemd/system/lmi-clean-adsp.service
chmod 0644 /etc/systemd/system/lmi-linux7-wifi-reprobe.service
chmod 0644 /etc/systemd/system/lmi-geoclue-bss-reseed.service
chmod 0644 /etc/systemd/system/phosh-m0.service
chmod 0644 /etc/phosh/phoc.ini
chmod 0644 /etc/systemd/system/phosh-m0.service.d/50-lmi-seat-vtnr.conf
chmod 0644 /etc/systemd/system/phosh-m0.service.d/51-lmi-restart-guard.conf

echo "== enabling units offline =="
# systemctl --root works without a running systemd and creates the same
# [Install] symlinks a live enable would.
systemctl --root=/ enable lmi-clean-adsp.service
systemctl --root=/ enable lmi-linux7-wifi-reprobe.service
systemctl --root=/ enable lmi-geoclue-bss-reseed.service
systemctl --root=/ enable phosh-m0.service
systemctl --root=/ enable ssh.service

# Current lmi kernel does not provide CONFIG_ZRAM. Prevent generated swap
# dependencies and the separate zramswap service from delaying boot.
install -m 0644 /dev/null /etc/systemd/zram-generator.conf
systemctl --root=/ mask zramswap.service
# phosh-m0 is the intended session; do not start a second GDM greeter.
systemctl --root=/ mask gdm.service

echo "== 4.19 era units =="
# The old install carried these units. None of them is packaged and none of
# them is copied into the clean image, so there is nothing to disable: the
# verification step asserts that no such unit exists. Masking a unit that was
# never installed would only create a misleading /dev/null symlink.
for u in lmi-cpu-idle.service lmi-adsp-btfm.service lmi-wlan-on.service \
         lmi-cnss-daemon.service lmi-cnss-fs-ready.service lmi-pd-mapper.service \
         lmi-wlan-firmware-prepare.service lmi-adsp-boot-mainline.service \
         lmi-adsp-firmware-prepare.service lmi-android-wifi-mounts.service \
         lmi-splash-release.service lmi-venus-firmware-prepare.service \
         lmi-time-seed.service lmi-time-seed-save.service lmi-time-seed-save.timer \
         lmi-rtc-time-restore.service lmi-camera-preview.service; do
    if [ -e "/etc/systemd/system/$u" ] || [ -e "/usr/lib/systemd/system/$u" ]; then
        echo "unexpected 4.19 era unit present in the clean image: $u" >&2
        exit 1
    fi
done

echo "== user session prerequisites =="
install -d -m 0700 -o "$USER_NAME" -g "$USER_NAME" "/home/$USER_NAME/.config"
install -d -m 0700 -o "$USER_NAME" -g "$USER_NAME" "/home/$USER_NAME/.config/pipewire"
install -d -m 0700 -o "$USER_NAME" -g "$USER_NAME" "/home/$USER_NAME/.config/pipewire/pipewire.conf.d"
install -d -m 0755 -o "$USER_NAME" -g "$USER_NAME" "/home/$USER_NAME/.local"
install -d -m 0700 -o "$USER_NAME" -g "$USER_NAME" "/home/$USER_NAME/.local/share"

echo "LMI_HARDWARE_INSTALLED user=$USER_NAME"
