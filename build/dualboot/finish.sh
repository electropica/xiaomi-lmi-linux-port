#!/bin/bash
# Finalize an already completed image; never rebuild or contact a device.
set -euo pipefail
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=/home/linuxagent/xiaomi-lmi-linux-port
name=mobian-lmi-dualboot-20261021
# Retained external input; override when restoring it elsewhere.
boot=${DUALBOOT_SOURCE_BOOT:-/mnt/d/Mobian/BuildInputs/current-mobian/kernel-rpmh-source-boot.img}
[[ -r $boot ]] || { echo "Missing source boot input: $boot" >&2; exit 1; }
printf '%s  %s\n' a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50 "$boot" | sha256sum -c - >/dev/null
layout=/mnt/c/Users/julien/Documents/ChatGPT/Mobian/work/dualboot-layout-20261021-private.json
test -s "$repo/output/$name.img"
test -s "$repo/output/$name.img.android-sparse.img"
test ! -e "$repo/output/$name-boot"
python3 "$here/check-image.py" "$repo/output/$name.img"
# The full-image builder intentionally owns output/ as root. Elevate only
# this artifact finalizer; do not chmod/chown the output tree or rebuild.
if [[ $(id -u) == 0 ]]; then
    python3 "$here/prepare.py" --boot "$boot" --layout "$layout" --output "$repo/output/$name-boot"
else
    sudo python3 "$here/prepare.py" --boot "$boot" --layout "$layout" --output "$repo/output/$name-boot"
fi
printf 'DUALBOOT_ARTIFACTS_BUILT_NOT_INSTALLED\nROOTFS_SPARSE=%s\nBOOT=%s\n' \
    "$repo/output/$name.img.android-sparse.img" "$repo/output/$name-boot/mobian-dualboot-boot.img"
printf 'Do NOT flash this rootfs to userdata. Dedicated mobian partition installation is a separate step.\n'
