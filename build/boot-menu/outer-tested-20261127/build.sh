#!/bin/bash
# Operator-only temporary firmware build. No device tools, no kernel rebuild.
set -euo pipefail
recipe=$(cd -- "$(dirname -- "$0")" && pwd -P)
if [[ ${1:-} != --build || $# != 1 ]]; then
  echo 'Set LMI_MENU_BUILD_ROOT, LMI_MENU_TOOLCHAIN_ROOT, LMI_MENU_BUNDLE_DIR and LMI_MENU_BUNDLE_SHA256, then run --build as root.'
  exit 0
fi
[[ $EUID == 0 ]] || { echo 'Run the firmware build with sudo.' >&2; exit 2; }
: "${LMI_MENU_BUILD_ROOT:?Set an absolute disposable build root}"
: "${LMI_MENU_TOOLCHAIN_ROOT:?Set the existing menu toolchain root}"
: "${LMI_MENU_BUNDLE_DIR:?Set the verified component bundle directory}"
: "${LMI_MENU_BUNDLE_SHA256:?Set the expected bundle SHA-256}"
[[ $LMI_MENU_BUILD_ROOT == /* && $LMI_MENU_TOOLCHAIN_ROOT == /* && $LMI_MENU_BUNDLE_DIR == /* ]] || exit 2
[[ $LMI_MENU_BUNDLE_SHA256 =~ ^[0-9a-f]{64}$ ]] || exit 2
expected=$LMI_MENU_BUILD_ROOT
old=$LMI_MENU_TOOLCHAIN_ROOT
bundle=$LMI_MENU_BUNDLE_DIR
[[ ! -L $expected && ! -L $old && ! -L $bundle ]] || exit 2
mkdir -p "$expected"
exec 9>/run/lmi-linux7-menu-build.lock
flock -n 9 || { echo 'Candidate firmware build already running.' >&2; exit 2; }
rootfs=$old/rootfs
out=$expected/output
[[ -f $rootfs/.lmi-bootstrap-complete && ! -L $rootfs ]] || { echo 'Qualified compiler rootfs unavailable.' >&2; exit 2; }
[[ ! -e $out && ! -L $out ]] || { echo 'Output exists: inspect it; no overwrite.' >&2; exit 2; }
python3 -B "$recipe/preflight.py"
python3 - "$expected" <<'HOSTSPACE'
import shutil,sys
assert shutil.disk_usage(sys.argv[1]).free > 3*1024**3, 'Build location needs at least 3 GiB free'
HOSTSPACE
export LMI_MENU_BUILD_ROOT="$expected" LMI_MENU_BASE_SOURCE="$old/source/edk2-msm"
python3 -B "$recipe/prepare-sources.py"
mkdir "$out"
exec unshare --mount --propagation private bash -s -- "$rootfs" "$recipe" "$expected/source" "$out" "$old" "$bundle" "$LMI_MENU_BUNDLE_SHA256" <<'INNER'
set -euo pipefail
rootfs=$1;recipe=$2;source=$3;out=$4;old=$5;bundle=$6;bundle_sha=$7
mkdir -p "$rootfs"/{recipe,source,output,inputs,linux7-bundle,proc,sys,dev}
# Shared compiler rootfs, but completely separate sources and build outputs.
mount --bind "$recipe" "$rootfs/recipe"
mount -o remount,bind,ro "$rootfs/recipe"
mount --bind "$source" "$rootfs/source"
mount --bind "$out" "$rootfs/output"
mount --bind "$old/inputs" "$rootfs/inputs"
mount -o remount,bind,ro "$rootfs/inputs"
mount --bind "$bundle" "$rootfs/linux7-bundle"
mount -o remount,bind,ro "$rootfs/linux7-bundle"
# Git --shared object references require their exact absolute paths in chroot.
mkdir -p "$rootfs$old/source"
mount --bind "$old/source" "$rootfs$old/source"
mount -o remount,bind,ro "$rootfs$old/source"
mount -t proc proc "$rootfs/proc"
mount --rbind /dev "$rootfs/dev"
mount --make-rslave "$rootfs/dev"
mount -t sysfs -o ro sysfs "$rootfs/sys"
chroot "$rootfs" /usr/bin/env LMI_MENU_LINEAGE=1 LMI_EXPECTED_BUNDLE_SHA256="$bundle_sha" /bin/bash /recipe/build-inside.sh 2>&1 | tee "$out/build.log"
INNER
