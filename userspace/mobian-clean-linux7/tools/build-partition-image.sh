#!/bin/sh
# Build the Mobian partition image from the clean rootfs, preserving the boot
# region byte for byte.
#
# The handset has a dedicated 16 GiB GPT partition named "mobian" that holds
# two filesystems in one container:
#
#   offset      8388608   ext2   pmOS_boot  UUID 7bd723c2-51d6-4015-b28b-2b38191bf765
#   offset    255852544   ext4   pmOS_root  UUID dba94dfe-0fb9-4f95-970e-22949f4e69dc
#
# The running initramfs looks the root up by that ext4 UUID. The clean image
# is therefore given the SAME UUID, so the installed menu boots it without
# the menu being rebuilt or reflashed, and without touching Android.
#
# The boot region is copied byte for byte from a read-only capture of the
# device, so the menu, the kernel and the DTB stay exactly as they are.
#
# Usage:
#   sh build-partition-image.sh <rootfs.tar.xz> <boot-region.bin> <outdir>
#
# Requires root for mke2fs -d (or an unprivileged user namespace with a
# writable loop). Run inside WSL on Julien's machine.
set -eu

ROOTFS=${1:?rootfs tarball required}
REGION=${2:?boot region capture required}
OUTDIR=${3:?output directory required}

BOOT_UUID=7bd723c2-51d6-4015-b28b-2b38191bf765
ROOT_UUID=dba94dfe-0fb9-4f95-970e-22949f4e69dc
PART_BYTES=17179869184
ROOT_OFFSET=255852544
# The root loop has no size limit, so the ext4 filesystem extends to the end
# of the partition: 17179869184 - 255852544 = 16924016640 bytes.
ROOT_BYTES_KIB=16527360
ROOT_BYTES=$((ROOT_BYTES_KIB * 1024))

echo "== inputs =="
[ -f "$ROOTFS" ] || { echo "missing $ROOTFS" >&2; exit 1; }
[ -f "$REGION" ] || { echo "missing $REGION" >&2; exit 1; }
region_bytes=$(stat -c %s "$REGION")
[ "$region_bytes" = "$ROOT_OFFSET" ] || {
    echo "REFUSED: the boot region capture is $region_bytes bytes, expected $ROOT_OFFSET" >&2
    exit 1
}
mkdir -p "$OUTDIR"
for name in mobian-root.ext4 mobian-partition.img mobian-partition.simg mobian-partition.manifest.json; do
    [ ! -e "$OUTDIR/$name" ] && [ ! -L "$OUTDIR/$name" ] || {
        echo "REFUSED: output already exists: $OUTDIR/$name" >&2; exit 1;
    }
done

STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

echo "== unpacking the rootfs =="
tar --xattrs --acls --numeric-owner -xJf "$ROOTFS" -C "$STAGE"

echo "== provisioning the staged account =="
sh "$(dirname "$0")/provision-staged-account.sh" "$STAGE"

echo "== building the ext4 root filesystem =="
ROOTIMG="$OUTDIR/mobian-root.ext4"
# mke2fs -d populates the image from a directory without mounting it.
mke2fs -q -t ext4 -b 4096 -U "$ROOT_UUID" -L pmOS_root \
    -d "$STAGE" "$ROOTIMG" "${ROOT_BYTES_KIB}k"
e2fsck -fn "$ROOTIMG"
dumpe2fs -h "$ROOTIMG" 2>/dev/null | grep -E 'Filesystem UUID|Filesystem volume name|Block size|Block count' || true

echo "== assembling the 16 GiB partition image =="
PARTIMG="$OUTDIR/mobian-partition.img"
truncate -s "$PART_BYTES" "$PARTIMG"
dd if="$REGION" of="$PARTIMG" bs=1M conv=notrunc status=none
dd if="$ROOTIMG" of="$PARTIMG" bs=1M seek=$((ROOT_OFFSET / 1024 / 1024)) conv=notrunc status=none

echo "== verifying the assembled image =="
# blkid -p probes the image without mounting it. The boot filesystem is at
# offset 8388608 and the root filesystem at offset 255852544.
sh "$(dirname "$0")/verify-partition-image.sh" "$PARTIMG" "$REGION"

echo "== converting to an Android sparse image =="
SPIMG="$OUTDIR/mobian-partition.simg"
if command -v img2simg >/dev/null 2>&1; then
    img2simg "$PARTIMG" "$SPIMG"
else
    echo "NOTE: img2simg is not installed; the raw image is kept as $PARTIMG" >&2
    SPIMG=$PARTIMG
fi

echo "== manifest =="
MANIFEST="$OUTDIR/mobian-partition.manifest.json"
{
    printf '{\n'
    printf '  "generated": "%s",\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '  "partition_bytes": %s,\n' "$PART_BYTES"
    printf '  "boot_offset": 8388608,\n'
    printf '  "root_offset": %s,\n' "$ROOT_OFFSET"
    printf '  "boot_uuid": "%s",\n' "$BOOT_UUID"
    printf '  "root_uuid": "%s",\n' "$ROOT_UUID"
    printf '  "rootfs_tarball_sha256": "%s",\n' "$(sha256sum "$ROOTFS" | cut -d' ' -f1)"
    printf '  "boot_region_sha256": "%s",\n' "$(sha256sum "$REGION" | cut -d' ' -f1)"
    printf '  "partition_image_sha256": "%s",\n' "$(sha256sum "$PARTIMG" | cut -d' ' -f1)"
    if [ -f "$SPIMG" ]; then
        printf '  "sparse_image_sha256": "%s",\n' "$(sha256sum "$SPIMG" | cut -d' ' -f1)"
        printf '  "sparse_image_bytes": %s\n' "$(stat -c %s "$SPIMG")"
    fi
    printf '}\n'
} > "$MANIFEST"

cat "$MANIFEST"
echo "PARTITION_IMAGE_READY"
