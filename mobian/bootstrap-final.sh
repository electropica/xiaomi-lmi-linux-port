#!/bin/bash
set -euo pipefail

base="${MOBIAN_M0_BASE:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"
rm -rf "$base/rootfs" "$base/fakeroot-first.state"
mkdir -p "$base/rootfs"

export PATH="$base/tools/usr/sbin:$base/tools/usr/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export DEBOOTSTRAP_DIR="$base/tools/usr/share/debootstrap"
export LD_LIBRARY_PATH="$base/tools/usr/lib/x86_64-linux-gnu/libfakeroot:$base/tools/usr/lib/x86_64-linux-gnu"
fakeroot-sysv -s "$base/fakeroot-first.state" -- \
  debootstrap --foreign --arch=arm64 --variant=minbase trixie \
  "$base/rootfs" http://deb.debian.org/debian \
  >"$base/logs/debootstrap-first-final.log" 2>&1

export LD_LIBRARY_PATH="$base/tools/usr/lib/x86_64-linux-gnu"
export PROOT_NO_SECCOMP=1
unset DEBOOTSTRAP_DIR
proot -0 -q /usr/bin/qemu-aarch64 -r "$base/rootfs" \
  -b /proc -b /sys -b /dev -w / \
  /debootstrap/debootstrap --second-stage \
  >"$base/logs/debootstrap-second-final.log" 2>&1
