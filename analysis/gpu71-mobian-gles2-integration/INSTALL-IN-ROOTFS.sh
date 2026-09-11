#!/bin/sh
set -eu

ROOTFS=${1:?Usage: INSTALL-IN-ROOTFS.sh ROOTFS}

install -d -m 0755 "$ROOTFS/opt/mobian-gpu/lib"
install -d -m 0755 "$ROOTFS/opt/mobian-gpu/icd.d"
install -d -m 0755 "$ROOTFS/lib/firmware/postmarketos"
install -d -m 0755 "$ROOTFS/etc/udev/rules.d"
install -d -m 0755 "$ROOTFS/etc/systemd/system"
install -d -m 0755 "$ROOTFS/etc/systemd/system/graphical.target.wants"
install -d -m 0755 "$ROOTFS/etc/phosh"

install -o 0 -g 0 -m 0755 runtime/lib/libEGL.so.1.0.0 "$ROOTFS/opt/mobian-gpu/lib/"
install -o 0 -g 0 -m 0755 runtime/lib/libGLESv2.so.2.0.0 "$ROOTFS/opt/mobian-gpu/lib/"
install -o 0 -g 0 -m 0755 runtime/lib/libgallium-25.0.7.so "$ROOTFS/opt/mobian-gpu/lib/"
install -o 0 -g 0 -m 0755 runtime/lib/libvulkan_freedreno.so "$ROOTFS/opt/mobian-gpu/lib/"

ln -sf libEGL.so.1.0.0 "$ROOTFS/opt/mobian-gpu/lib/libEGL.so.1"
ln -sf libEGL.so.1 "$ROOTFS/opt/mobian-gpu/lib/libEGL.so"
ln -sf libGLESv2.so.2.0.0 "$ROOTFS/opt/mobian-gpu/lib/libGLESv2.so.2"
ln -sf libGLESv2.so.2 "$ROOTFS/opt/mobian-gpu/lib/libGLESv2.so"

install -o 0 -g 0 -m 0644 runtime/icd.d/freedreno_icd.aarch64.json "$ROOTFS/opt/mobian-gpu/icd.d/"

install -o 0 -g 0 -m 0644 firmware/a650_sqe.fw "$ROOTFS/lib/firmware/postmarketos/"
install -o 0 -g 0 -m 0644 firmware/a650_gmu.bin "$ROOTFS/lib/firmware/postmarketos/"
install -o 0 -g 0 -m 0644 firmware/a650_zap.mdt "$ROOTFS/lib/firmware/postmarketos/"
install -o 0 -g 0 -m 0644 firmware/a650_zap.b00 "$ROOTFS/lib/firmware/postmarketos/"
install -o 0 -g 0 -m 0644 firmware/a650_zap.b01 "$ROOTFS/lib/firmware/postmarketos/"
install -o 0 -g 0 -m 0644 firmware/a650_zap.b02 "$ROOTFS/lib/firmware/postmarketos/"
install -o 0 -g 0 -m 0644 firmware/a650_zap.elf "$ROOTFS/lib/firmware/postmarketos/"

install -o 0 -g 0 -m 0644 udev/70-kgsl.rules "$ROOTFS/etc/udev/rules.d/"
install -o 0 -g 0 -m 0644 udev/71-ion.rules "$ROOTFS/etc/udev/rules.d/"
install -o 0 -g 0 -m 0644 phoc/phoc.ini "$ROOTFS/etc/phosh/phoc.ini"
install -o 0 -g 0 -m 0644 systemd/phosh-m0.service "$ROOTFS/etc/systemd/system/phosh-m0.service"

if ! grep -q '^render:' "$ROOTFS/etc/group"; then
    echo "ERROR: render group missing from rootfs"
    exit 1
fi

awk -F: 'BEGIN { OFS=":" } $1=="render" { if ($4=="") $4="mobian"; else if (("," $4 ",") !~ ",mobian,") $4=$4 ",mobian" } { print }' "$ROOTFS/etc/group" > "$ROOTFS/etc/group.gpu71"
mv "$ROOTFS/etc/group.gpu71" "$ROOTFS/etc/group"

ln -sf ../phosh-m0.service "$ROOTFS/etc/systemd/system/graphical.target.wants/phosh-m0.service"

echo "GPU71_ROOTFS_INTEGRATION=PASS"
echo "GPU71_RUNTIME=/opt/mobian-gpu"
echo "GPU71_FIRMWARE=/lib/firmware/postmarketos"
echo "GPU71_MOBIAN_RENDER_GROUP=CONFIGURED"
echo "GPU71_PHOSH_SERVICE=ENABLED"
