#!/bin/bash
# Read-only source/output overlays; only the patched C file is substituted.
set -euo pipefail
[[ $EUID == 0 ]] || exit 1
recipe=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -f -- "$tmp/FwVol.c"; rmdir -- "$tmp"' EXIT
python3 -B - "$recipe" "$tmp/FwVol.c" <<'PY'
from pathlib import Path
import importlib.util,sys
p=Path(sys.argv[1])/'chainload/patch-prepi.py'
s=importlib.util.spec_from_file_location('prepi',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
base=Path('/home/linuxagent/lmi-boot-menu-build/source/edk2-msm/Common/edk2')
Path(sys.argv[2]).write_bytes(m.patch((base/m.PATH).read_bytes()))
PY
unshare --mount --propagation private bash -s -- "$recipe" "$tmp/FwVol.c" <<'INNER'
set -euo pipefail
root=/home/linuxagent/lmi-boot-menu-build
mount --bind "$root/source" "$root/rootfs/source"
mount -o remount,bind,ro "$root/rootfs/source"
mount --bind "$root/output" "$root/rootfs/output"
mount -o remount,bind,ro "$root/rootfs/output"
mount --bind "$1" "$root/rootfs/recipe"
mount -o remount,bind,ro "$root/rootfs/recipe"
mount --bind "$2" "$root/rootfs/source/edk2-msm/Common/edk2/EmbeddedPkg/Library/PrePiLib/FwVol.c"
mount -o remount,bind,ro "$root/rootfs/source/edk2-msm/Common/edk2/EmbeddedPkg/Library/PrePiLib/FwVol.c"
chroot "$root/rootfs" /usr/bin/make --no-print-directory \
  -C /source/edk2-msm/Common/edk2/EmbeddedPkg/Library/PrePiLib \
  -f /output/workspace/Build/lmi/RELEASE_CLANG38/AARCH64/EmbeddedPkg/Library/PrePiLib/PrePiLib/GNUmakefile \
  -f /recipe/chainload/prepi-syntax.mk lmi-prepi-syntax
INNER
echo ARM64_PREPI_SYNTAX_PASS_NO_FIRMWARE_BUILD
