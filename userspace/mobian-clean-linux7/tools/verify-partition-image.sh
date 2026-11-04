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
# Read-only loop avoids copying the 16 GiB root into /tmp (a small tmpfs on
# WSL). This check requires root and an available loop device.
loop=$(losetup --find --show --read-only --offset "$ROOT_OFFSET" --sizelimit "$ROOT_BYTES" "$IMG") || fail "cannot create read-only loop"
trap 'losetup -d "$loop"' EXIT HUP INT TERM
e2fsck -fn "$loop" || fail "root filesystem check failed"
dumpe2fs -h "$loop" 2>/dev/null | grep -E 'Filesystem UUID|Filesystem volume name|Filesystem state' || true
losetup -d "$loop"
trap - EXIT HUP INT TERM
ok "root filesystem checked read-only"

echo "== the boot region is preserved byte for byte =="
if [ -n "$REGION" ] && [ -f "$REGION" ]; then
    [ "$(stat -c %s "$REGION")" = "$ROOT_OFFSET" ] || fail "unexpected boot region size"
    cmp -n "$ROOT_OFFSET" "$IMG" "$REGION" || fail "the boot region differs from the capture"
    ok "boot region identical to the device capture"
else
    echo "  --  skipped: no boot region capture given"
fi

echo
echo "IMAGE_CHECK_PASSED"
