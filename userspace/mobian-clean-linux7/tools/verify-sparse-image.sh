#!/bin/sh
# Offline verification only. No device access and no modification of input.
set -eu
image=${1:?sparse image required}
manifest=${2:?manifest required}
region=${3:?verified boot-region capture required}
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
[ -f "$image" ] && [ -f "$manifest" ] && [ -f "$region" ] || {
    echo 'missing input' >&2; exit 1;
}
command -v simg2img >/dev/null || { echo 'simg2img missing' >&2; exit 1; }
want=$(python3 -c 'import json,sys; x=json.load(open(sys.argv[1])); v=x["sparse_image_sha256"]; assert isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v); print(v)' "$manifest")
got=$(sha256sum "$image" | cut -d' ' -f1)
[ "$got" = "$want" ] || { echo 'sparse image hash mismatch' >&2; exit 1; }
want_region=$(python3 -c 'import json,sys; x=json.load(open(sys.argv[1])); v=x["boot_region_sha256"]; assert isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v); print(v)' "$manifest")
got_region=$(sha256sum "$region" | cut -d' ' -f1)
[ "$got_region" = "$want_region" ] || { echo 'boot region hash mismatch' >&2; exit 1; }
image_dir=$(CDPATH= cd -- "$(dirname -- "$image")" && pwd)
tmp=$(mktemp -d "${LMI_VERIFY_TMPDIR:-$image_dir}/.lmi-verify.XXXXXXXX")
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
simg2img "$image" "$tmp/decoded.img"
sh "$here/verify-partition-image.sh" "$tmp/decoded.img" "$region"
echo SPARSE_IMAGE_VERIFIED_OFFLINE
