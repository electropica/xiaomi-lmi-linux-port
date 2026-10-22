#!/bin/bash
# Five targeted ARM64 syntax checks; no firmware build or cache-source edit.
set -euo pipefail
[[ $EUID == 0 ]] || exit 1
recipe=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
tmp=$(mktemp -d /tmp/lmi-outer-syntax-XXXXXX)
python3 -B - "$recipe" "$tmp" <<'PY'
from pathlib import Path
import importlib.util,sys
recipe=Path(sys.argv[1]);tmp=Path(sys.argv[2])
spec=importlib.util.spec_from_file_location('outer',recipe/'external-mobian/apply-outer.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
root=Path('/home/linuxagent/lmi-boot-menu-build')
edits=m.patchset(root/'source/edk2-msm',recipe,root/'output')
for name,(_,raw) in edits.items():
    p=tmp/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
print('OUTER_CANDIDATE_OVERLAY_GENERATED_WITHOUT_CACHE_EDIT',len(edits))
PY
unshare --mount --propagation private bash -s -- "$recipe" "$tmp" <<'INNER'
set -euo pipefail
root=/home/linuxagent/lmi-boot-menu-build;rootfs=$root/rootfs;recipe=$1;tmp=$2
mkdir -p "$rootfs/check"
mount --bind "$root/source" "$rootfs/source"
mount -o remount,bind,ro "$rootfs/source"
mount --bind "$root/output" "$rootfs/output"
mount -o remount,bind,ro "$rootfs/output"
mount --bind "$recipe" "$rootfs/recipe"
mount -o remount,bind,ro "$rootfs/recipe"
mount --bind "$tmp" "$rootfs/check"
mount -o remount,bind,ro "$rootfs/check"
# Overlay the modified existing FDT helper only; new headers use include paths.
sub=GPLDrivers/Library/SimpleInit/src/linux-boot/lmi-android-fstab.h
mount --bind "$tmp/$sub" "$rootfs/source/edk2-msm/$sub"
base=/source/edk2-msm/GPLDrivers/Library/SimpleInit
flags='-I/recipe/external-mobian -I/output'
chroot "$rootfs" /usr/bin/make --no-print-directory -C "$base" \
 -f /output/workspace/Build/lmi/RELEASE_CLANG38/AARCH64/src/main/SimpleInitMain/GNUmakefile \
 -f /recipe/chainload/diagnostic-syntax.mk \
 "LMI_CHECK_SOURCE=$flags /check/GPLDrivers/Library/SimpleInit/src/main/uefimain.c" lmi-diagnostic-syntax
for file in aboot.c linux.c; do
 chroot "$rootfs" /usr/bin/make --no-print-directory -C "$base" \
  -f /output/workspace/Build/lmi/RELEASE_CLANG38/AARCH64/src/linux-boot/SimpleInitBootLinux/GNUmakefile \
  -f /recipe/chainload/diagnostic-syntax.mk \
  "LMI_CHECK_SOURCE=$flags /check/GPLDrivers/Library/SimpleInit/src/linux-boot/$file" lmi-diagnostic-syntax
done
chroot "$rootfs" /usr/bin/make --no-print-directory -C "$base" \
 -f /output/workspace/Build/lmi/RELEASE_CLANG38/AARCH64/src/boot/SimpleInitBoot/GNUmakefile \
 -f /recipe/chainload/diagnostic-syntax.mk \
 "LMI_CHECK_SOURCE=$flags /check/GPLDrivers/Library/SimpleInit/src/boot/linux.c" lmi-diagnostic-syntax
chroot "$rootfs" /usr/bin/make --no-print-directory -C /source/edk2-msm \
 -f /output/workspace/Build/lmi/RELEASE_CLANG38/AARCH64/Silicon/Qualcomm/QcomPkg/Library/MemoryInitPeiLib/PeiMemoryAllocationLib/GNUmakefile \
 -f /recipe/chainload/diagnostic-syntax.mk \
 "LMI_CHECK_SOURCE=$flags /check/Silicon/Qualcomm/QcomPkg/Library/MemoryInitPeiLib/MemoryInitPeiLib.c" lmi-diagnostic-syntax
INNER
echo EXTERNAL_MOBIAN_FIVE_ARM64_UNITS_SYNTAX_PASS_NO_FIRMWARE_BUILD
