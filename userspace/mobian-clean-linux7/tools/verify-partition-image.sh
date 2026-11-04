#!/bin/sh
# Off-device verification of the produced Mobian partition image.
#
# Run this on the build host, after build-partition-image.sh. It proves, on
# the host and without touching the phone, that the image has the layout the
# installed initramfs expects.
#
# Usage:  sh verify-partition-image.sh <partition.img> [boot-region.bin]
set -eu

IMG=${1:?partition image required}
REGION=${2:-}

BOOT_UUID=7bd723c2-51d6-4015-b28b-2b38191bf765
ROOT_UUID=dba94dfe-0fb9-4f95-970e-22949f4e69dc
BOOT_OFFSET=8388608
ROOT_OFFSET=255852544
PART_BYTES=17179869184
ROOT_BYTES=16924016640

fail() { echo "IMAGE_CHECK_FAILED: $*" >&2; exit 1; }
ok()   { echo "  ok  $*"; }

[ -f "$IMG" ] || fail "missing $IMG"

echo "== size =="
size=$(stat -c %s "$IMG")
[ "$size" = "$PART_BYTES" ] || fail "the image is $size bytes, expected exactly $PART_BYTES"
ok "size is exactly 16 GiB"

echo "== boot filesystem at offset $BOOT_OFFSET =="
b=$(blkid -p -o full -O "$BOOT_OFFSET" "$IMG" 2>/dev/null || true)
printf '%s\n' "$b" | grep -Fq "UUID=\"$BOOT_UUID\"" || fail "the boot UUID is not $BOOT_UUID ($b)"
printf '%s\n' "$b" | grep -Fq 'TYPE="ext2"' || fail "the boot filesystem is not ext2 ($b)"
ok "boot ext2 $BOOT_UUID"

echo "== root filesystem at offset $ROOT_OFFSET =="
r=$(blkid -p -o full -O "$ROOT_OFFSET" "$IMG" 2>/dev/null || true)
printf '%s\n' "$r" | grep -Fq "UUID=\"$ROOT_UUID\"" || fail "the root UUID is not $ROOT_UUID ($r)"
printf '%s\n' "$r" | grep -Fq 'TYPE="ext4"' || fail "the root filesystem is not ext4 ($r)"
ok "root ext4 $ROOT_UUID"

echo "== the root filesystem is consistent =="
# Extract the root region and check it on its own.
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
dd if="$IMG" of="$TMP/root.ext4" bs=4096 skip=$((ROOT_OFFSET / 4096)) count=$((ROOT_BYTES / 4096)) conv=notrunc status=none
e2fsck -fn "$TMP/root.ext4" || fail "root filesystem check failed"
dumpe2fs -h "$TMP/root.ext4" 2>/dev/null | grep -E 'Filesystem UUID|Filesystem volume name|Filesystem state' || true
ok "root filesystem inspected"

echo "== the boot region is preserved byte for byte =="
if [ -n "$REGION" ] && [ -f "$REGION" ]; then
    dd if="$IMG" of="$TMP/region.bin" bs=1M count=$((ROOT_OFFSET / 1024 / 1024)) conv=notrunc status=none
    a=$(sha256sum "$TMP/region.bin" | cut -d' ' -f1)
    b2=$(sha256sum "$REGION" | cut -d' ' -f1)
    [ "$a" = "$b2" ] || fail "the boot region differs from the capture"
    ok "boot region identical to the device capture"
else
    echo "  --  skipped: no boot region capture given"
fi

echo
echo "IMAGE_CHECK_PASSED"
