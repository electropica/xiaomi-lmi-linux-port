#!/bin/bash
# Targeted syntax only, with transient overlays of the three affected C units.
set -euo pipefail
[[ $EUID == 0 ]] || exit 1
recipe=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -f -- "$tmp/entry.c" "$tmp/prepare.c" "$tmp/aboot.c" "$tmp/dtbo.c"; rmdir -- "$tmp"' EXIT
python3 -B - "$recipe" "$tmp" <<'PY'
from pathlib import Path
import importlib.util,sys,subprocess,json,hashlib
recipe=Path(sys.argv[1]);tmp=Path(sys.argv[2])
root=Path('/home/linuxagent/lmi-boot-menu-build');src=root/'source/edk2-msm/GPLDrivers/Library/SimpleInit'
manifest=json.loads((root/'output/chainload-source-manifest.json').read_text())
s=importlib.util.spec_from_file_location('diag',recipe/'chainload/patch-diagnostic.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
for path in ['src/boot/linux.c','src/linux-boot/aboot.c']:
 assert hashlib.sha256((src/path).read_bytes()).hexdigest()==manifest[path]['after']
entry=(src/'src/boot/linux.c').read_text()
tmp.joinpath('entry.c').write_text(entry if 'lmi_boot_failed();' in entry else m.patch_entry(entry))
raw=subprocess.check_output(['git','-C',str(src),'show','HEAD:src/linux-boot/linux.c'],text=True)
tmp.joinpath('prepare.c').write_text(m.patch_prepare(raw))
text=(src/'src/linux-boot/aboot.c').read_text()
tmp.joinpath('aboot.c').write_text(text if '#include "lmi-boot-diagnostic.h"' in text else text.replace('#include "lmi-bundle-loader.h"','#include "lmi-boot-diagnostic.h"\n#include "lmi-bundle-loader.h"'))
s=importlib.util.spec_from_file_location('dtbo',recipe/'chainload/patch-dtbo.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
raw=subprocess.check_output(['git','-C',str(src),'show','HEAD:src/linux-boot/dtbo.c'],text=True)
tmp.joinpath('dtbo.c').write_text(d.patch(raw))
PY
unshare --mount --propagation private bash -s -- "$recipe" "$tmp" <<'INNER'
set -euo pipefail
root=/home/linuxagent/lmi-boot-menu-build;rootfs=$root/rootfs;recipe=$1;tmp=$2
mount --bind "$root/source" "$rootfs/source"
mount -o remount,bind,ro "$rootfs/source"
mount --bind "$root/output" "$rootfs/output"
mount -o remount,bind,ro "$rootfs/output"
mount --bind "$recipe" "$rootfs/recipe"
mount -o remount,bind,ro "$rootfs/recipe"
base=$rootfs/source/edk2-msm/GPLDrivers/Library/SimpleInit
mount --bind "$tmp/entry.c" "$base/src/boot/linux.c"
mount --bind "$tmp/prepare.c" "$base/src/linux-boot/linux.c"
mount --bind "$tmp/aboot.c" "$base/src/linux-boot/aboot.c"
mount --bind "$tmp/dtbo.c" "$base/src/linux-boot/dtbo.c"
mount --bind "$recipe/chainload/lmi-bundle-loader.h" "$base/src/linux-boot/lmi-bundle-loader.h"
# The new header is found through the recipe include path; no file is created
# in the real source tree.
for file in aboot.c linux.c dtbo.c; do
 chroot "$rootfs" /usr/bin/make --no-print-directory \
  -C /source/edk2-msm/GPLDrivers/Library/SimpleInit \
  -f /output/workspace/Build/lmi/RELEASE_CLANG38/AARCH64/src/linux-boot/SimpleInitBootLinux/GNUmakefile \
  -f /recipe/chainload/diagnostic-syntax.mk \
  "LMI_CHECK_SOURCE=-I/recipe/chainload /source/edk2-msm/GPLDrivers/Library/SimpleInit/src/linux-boot/$file" lmi-diagnostic-syntax
done
chroot "$rootfs" /usr/bin/make --no-print-directory \
 -C /source/edk2-msm/GPLDrivers/Library/SimpleInit \
 -f /output/workspace/Build/lmi/RELEASE_CLANG38/AARCH64/src/boot/SimpleInitBoot/GNUmakefile \
 -f /recipe/chainload/diagnostic-syntax.mk \
 LMI_CHECK_SOURCE=/source/edk2-msm/GPLDrivers/Library/SimpleInit/src/boot/linux.c lmi-diagnostic-syntax
INNER
echo ARM64_FOUR_UNIT_DTBO_DIAGNOSTIC_SYNTAX_PASS_NO_BUILD
