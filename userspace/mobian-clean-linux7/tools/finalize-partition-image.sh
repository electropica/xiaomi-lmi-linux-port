#!/bin/sh
# Finalize already assembled files; does not contact a phone or flash anything.
set -eu
dir=${1:?assembled image directory required}
region=${2:?verified boot region required}
rootfs=${3:?source rootfs archive required}
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
raw="$dir/mobian-partition.img"
sparse="$dir/mobian-partition.simg"
manifest="$dir/mobian-partition.manifest.json"
sp_tmp="$sparse.partial"
man_tmp="$manifest.partial"
[ -f "$raw" ] && [ -f "$region" ] && [ -f "$rootfs" ] || { echo 'missing input' >&2; exit 1; }
for f in "$sparse" "$manifest" "$sp_tmp" "$man_tmp"; do
    [ ! -e "$f" ] && [ ! -L "$f" ] || { echo "REFUSED: output exists: $f" >&2; exit 1; }
done
command -v img2simg >/dev/null || { echo 'img2simg missing' >&2; exit 1; }
command -v simg2img >/dev/null || { echo 'simg2img missing' >&2; exit 1; }
sh "$here/verify-partition-image.sh" "$raw" "$region"
img2simg "$raw" "$sp_tmp"
raw_hash=$(sha256sum "$raw" | cut -d' ' -f1)
sparse_hash=$(sha256sum "$sp_tmp" | cut -d' ' -f1)
boot_hash=$(sha256sum "$region" | cut -d' ' -f1)
rootfs_hash=$(sha256sum "$rootfs" | cut -d' ' -f1)
printf '{\n  "partition_image_sha256": "%s",\n  "sparse_image_sha256": "%s",\n  "boot_region_sha256": "%s",\n  "rootfs_tarball_sha256": "%s",\n  "partition_bytes": 17179869184\n}\n' \
    "$raw_hash" "$sparse_hash" "$boot_hash" "$rootfs_hash" > "$man_tmp"
sh "$here/verify-sparse-image.sh" "$sp_tmp" "$man_tmp" "$region"
mv "$sp_tmp" "$sparse"
mv "$man_tmp" "$manifest"
echo "PARTITION_IMAGE_FINALIZED sha256=$sparse_hash"
