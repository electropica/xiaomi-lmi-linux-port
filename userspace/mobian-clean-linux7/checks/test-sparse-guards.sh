#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
truncate -s 1048576 "$tmp/raw"
printf 'test' > "$tmp/region"
img2simg "$tmp/raw" "$tmp/test.simg"
image_hash=$(sha256sum "$tmp/test.simg" | cut -d' ' -f1)
region_hash=$(sha256sum "$tmp/region" | cut -d' ' -f1)
printf '{"sparse_image_sha256":"%s","boot_region_sha256":"%s"}\n' "$image_hash" "$region_hash" > "$tmp/manifest"
if sh "$here/../tools/verify-sparse-image.sh" "$tmp/test.simg" "$tmp/manifest" "$tmp/region" > "$tmp/out" 2>&1; then
    echo 'unexpected acceptance of undersized image' >&2; exit 1
fi
grep -q 'expected exactly 17179869184' "$tmp/out"
printf 'changed' >> "$tmp/region"
if sh "$here/../tools/verify-sparse-image.sh" "$tmp/test.simg" "$tmp/manifest" "$tmp/region" > "$tmp/out" 2>&1; then
    echo 'unexpected acceptance of changed boot region' >&2; exit 1
fi
grep -q 'boot region hash mismatch' "$tmp/out"
printf 'changed' >> "$tmp/test.simg"
if sh "$here/../tools/verify-sparse-image.sh" "$tmp/test.simg" "$tmp/manifest" "$tmp/region" > "$tmp/out" 2>&1; then
    echo 'unexpected acceptance of changed sparse image' >&2; exit 1
fi
grep -q 'sparse image hash mismatch' "$tmp/out"
echo SPARSE_NEGATIVE_GUARDS_PASS
