#!/bin/bash
# Targeted compiler syntax check after a generated build directory exists.
# Overlays only the corrected header in a private mount namespace; no build.
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Run with sudo' >&2; exit 1; }
recipe=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
exec unshare --mount --propagation private bash -s -- "$recipe" <<'INNER'
set -euo pipefail
recipe=$1
root=/home/linuxagent/lmi-boot-menu-build
rootfs=$root/rootfs
mount --bind "$root/source" "$rootfs/source"
mount -o remount,bind,ro "$rootfs/source"
mount --bind "$root/output" "$rootfs/output"
mount -o remount,bind,ro "$rootfs/output"
mount --bind "$recipe" "$rootfs/recipe"
mount -o remount,bind,ro "$rootfs/recipe"
mount --bind "$recipe/chainload/lmi-bundle-loader.h" "$rootfs/source/edk2-msm/GPLDrivers/Library/SimpleInit/src/linux-boot/lmi-bundle-loader.h"
chroot "$rootfs" /usr/bin/make --no-print-directory \
  -C /source/edk2-msm/GPLDrivers/Library/SimpleInit \
  -f /output/workspace/Build/lmi/RELEASE_CLANG38/AARCH64/src/linux-boot/SimpleInitBootLinux/GNUmakefile \
  -f /recipe/chainload/syntax-check.mk lmi-adapter-syntax
echo ARM64_ADAPTER_SYNTAX_PASS_NO_FIRMWARE_BUILD
INNER
