#!/bin/bash
set -euo pipefail

mount --make-rprivate /
mount -t binfmt_misc binfmt_misc /proc/sys/fs/binfmt_misc
sed -n '1p' /usr/lib/binfmt.d/qemu-aarch64.conf > /proc/sys/fs/binfmt_misc/register
test -e /proc/sys/fs/binfmt_misc/qemu-aarch64

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec "$script_dir/build-unshare-330-inner.sh"
