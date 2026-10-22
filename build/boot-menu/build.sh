#!/bin/bash
# Operator-run isolated build. Does not install or boot anything on the phone.
set -euo pipefail
recipe=$(cd -- "$(dirname -- "$0")" && pwd -P)
build_root=/home/linuxagent/lmi-boot-menu-build
if [[ ${1:-} != --build ]]; then
  echo "Recipe: $recipe"
  echo "Isolated Debian bookworm build: $build_root"
  echo 'Operator command: sudo bash build.sh --build'
  echo 'Builds only a temporary menu probe; does not yet launch Android.'
  exit 0
fi
lineage=0;dual=0
if [[ ${2:-} == --with-lineage && $# == 2 ]]; then lineage=1
elif [[ ${2:-} == --with-dual && $# == 2 ]]; then lineage=1;dual=1
elif [[ $# != 1 ]]; then echo 'Use --build [--with-lineage|--with-dual]' >&2; exit 1; fi
[[ $EUID == 0 ]] || { echo 'Use sudo bash build.sh --build' >&2; exit 1; }
command -v mmdebstrap >/dev/null
command -v unshare >/dev/null
[[ ! -L $build_root ]] || { echo 'Refusing symlink build root' >&2; exit 1; }
mkdir -p "$build_root"
[[ $(realpath -- "$build_root") == /home/linuxagent/lmi-boot-menu-build ]] || exit 1
rootfs=$build_root/rootfs
if [[ ! -f $rootfs/.lmi-bootstrap-complete ]]; then
  if [[ -e $rootfs ]]; then
    echo 'Incomplete rootfs exists. Preserve its log and inspect it before retry.' >&2
    exit 1
  fi
  export DEBIAN_FRONTEND=noninteractive
  mmdebstrap --architectures=amd64 --variant=minbase \
    --include=ca-certificates,git,build-essential,gcc-aarch64-linux-gnu,binutils-aarch64-linux-gnu,clang,lld,llvm,python3,python3-distutils,python3-setuptools,uuid-dev,acpica-tools,gettext,nasm,device-tree-compiler,unzip,xz-utils,pkg-config \
    bookworm "$rootfs" https://deb.debian.org/debian
  touch "$rootfs/.lmi-bootstrap-complete"
fi
mkdir -p "$build_root/source" "$build_root/output"
if [[ $lineage == 1 ]]; then
  for input in android.img android-dtbo.img; do
    [[ -f $build_root/inputs/$input ]] || { echo "Missing qualified input: $input" >&2; exit 1; }
  done
  if [[ $dual == 1 ]]; then [[ -f $build_root/inputs/mobian.img ]] || { echo 'Missing pinned mobian.img' >&2; exit 1; }; fi
fi
exec unshare --mount --propagation private bash -s -- "$rootfs" "$recipe" "$build_root" "$lineage" "$dual" <<'INNER'
set -euo pipefail
rootfs=$1;recipe=$2;build_root=$3;lineage=$4;dual=$5
mkdir -p "$rootfs"/{recipe,source,output,proc,sys,dev}
mount --bind "$recipe" "$rootfs/recipe"
mount -o remount,bind,ro "$rootfs/recipe"
mount --bind "$build_root/source" "$rootfs/source"
mount --bind "$build_root/output" "$rootfs/output"
mount -t proc proc "$rootfs/proc"
mount --rbind /dev "$rootfs/dev"
mount --make-rslave "$rootfs/dev"
mount -t sysfs -o ro sysfs "$rootfs/sys"
if [[ $lineage == 1 ]]; then
  mkdir -p "$rootfs/inputs"
  mount --bind "$build_root/inputs" "$rootfs/inputs"
  mount -o remount,bind,ro "$rootfs/inputs"
fi
# Mount namespace cleanup is automatic when the process exits, including failure.
chroot "$rootfs" /usr/bin/env LMI_MENU_LINEAGE="$lineage" LMI_MENU_DUAL="$dual" /bin/bash /recipe/build-inside.sh 2>&1 | tee "$build_root/output/build.log"
INNER
