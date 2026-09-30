#!/bin/sh
set -eu

ROOTFS=${1:?Usage: INSTALL-IN-ROOTFS.sh ROOTFS}
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
GPU72_LIB="$REPO_ROOT/userspace/gpu/files/gpu72/lib"
GPU72_ICD="$REPO_ROOT/userspace/gpu/files/gpu72/icd.d"
A650_FIRMWARE="$REPO_ROOT/userspace/gpu/files/firmware/a650"
PHOC_CONFIG="$REPO_ROOT/userspace/phosh/files/phoc.ini"

install -d -m 0755 "$ROOTFS/opt/mobian-gpu/lib"
install -d -m 0755 "$ROOTFS/opt/mobian-gpu/icd.d"
install -d -m 0755 "$ROOTFS/lib/firmware/postmarketos"
install -d -m 0755 "$ROOTFS/etc/udev/rules.d"
install -d -m 0755 "$ROOTFS/etc/systemd/system"
install -d -m 0755 "$ROOTFS/etc/systemd/system/graphical.target.wants"
install -d -m 0755 "$ROOTFS/etc/phosh"

install -o 0 -g 0 -m 0755 "$GPU72_LIB/libEGL.so.1.0.0" "$ROOTFS/opt/mobian-gpu/lib/"
install -o 0 -g 0 -m 0755 "$GPU72_LIB/libGLESv2.so.2.0.0" "$ROOTFS/opt/mobian-gpu/lib/"
install -o 0 -g 0 -m 0755 "$GPU72_LIB/libgallium-25.0.7.so" "$ROOTFS/opt/mobian-gpu/lib/"
install -o 0 -g 0 -m 0755 "$GPU72_LIB/libvulkan_freedreno.so" "$ROOTFS/opt/mobian-gpu/lib/"

ln -sf libEGL.so.1.0.0 "$ROOTFS/opt/mobian-gpu/lib/libEGL.so.1"
ln -sf libEGL.so.1 "$ROOTFS/opt/mobian-gpu/lib/libEGL.so"
ln -sf libGLESv2.so.2.0.0 "$ROOTFS/opt/mobian-gpu/lib/libGLESv2.so.2"
ln -sf libGLESv2.so.2 "$ROOTFS/opt/mobian-gpu/lib/libGLESv2.so"

install -o 0 -g 0 -m 0644 "$GPU72_ICD/freedreno_icd.aarch64.json" "$ROOTFS/opt/mobian-gpu/icd.d/"

install -o 0 -g 0 -m 0644 "$A650_FIRMWARE/a650_sqe.fw" "$ROOTFS/lib/firmware/postmarketos/"
install -o 0 -g 0 -m 0644 "$A650_FIRMWARE/a650_gmu.bin" "$ROOTFS/lib/firmware/postmarketos/"
install -o 0 -g 0 -m 0644 "$A650_FIRMWARE/a650_zap.mdt" "$ROOTFS/lib/firmware/postmarketos/"
install -o 0 -g 0 -m 0644 "$A650_FIRMWARE/a650_zap.b00" "$ROOTFS/lib/firmware/postmarketos/"
install -o 0 -g 0 -m 0644 "$A650_FIRMWARE/a650_zap.b01" "$ROOTFS/lib/firmware/postmarketos/"
install -o 0 -g 0 -m 0644 "$A650_FIRMWARE/a650_zap.b02" "$ROOTFS/lib/firmware/postmarketos/"
install -o 0 -g 0 -m 0644 "$A650_FIRMWARE/a650_zap.elf" "$ROOTFS/lib/firmware/postmarketos/"

install -o 0 -g 0 -m 0644 "$SCRIPT_DIR/udev/70-kgsl.rules" "$ROOTFS/etc/udev/rules.d/"
install -o 0 -g 0 -m 0644 "$SCRIPT_DIR/udev/71-ion.rules" "$ROOTFS/etc/udev/rules.d/"
install -o 0 -g 0 -m 0644 "$PHOC_CONFIG" "$ROOTFS/etc/phosh/phoc.ini"
install -o 0 -g 0 -m 0644 "$SCRIPT_DIR/systemd/phosh-m0.service" "$ROOTFS/etc/systemd/system/phosh-m0.service"

if ! grep -q '^render:' "$ROOTFS/etc/group"; then
    echo "ERROR: render group missing from rootfs"
    exit 1
fi

awk -F: 'BEGIN { OFS=":" } $1=="render" { if ($4=="") $4="mobian"; else if (("," $4 ",") !~ ",mobian,") $4=$4 ",mobian" } { print }' "$ROOTFS/etc/group" > "$ROOTFS/etc/group.gpu72"
mv "$ROOTFS/etc/group.gpu72" "$ROOTFS/etc/group"

ln -sf ../phosh-m0.service "$ROOTFS/etc/systemd/system/graphical.target.wants/phosh-m0.service"

echo "GPU72_ROOTFS_INTEGRATION=PASS"
echo "GPU72_RUNTIME=/opt/mobian-gpu"
echo "GPU72_FIRMWARE=/lib/firmware/postmarketos"
echo "GPU72_MOBIAN_RENDER_GROUP=CONFIGURED"
echo "GPU72_PHOSH_SERVICE=ENABLED"
