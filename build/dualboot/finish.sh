#!/bin/bash
# Finalize an already completed image; never rebuild or contact a device.
set -euo pipefail
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=/home/linuxagent/xiaomi-lmi-linux-port
name=mobian-lmi-dualboot-20261021
boot=/mnt/c/Users/julien/Downloads/D-repro-01-power-rpmh-votes-diagnostic-boot.img
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
