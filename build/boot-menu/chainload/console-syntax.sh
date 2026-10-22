#!/bin/bash
# One existing C unit, syntax-only with generated firmware flags.
set -euo pipefail
[[ $EUID == 0 ]] || exit 1
recipe=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -f -- "$tmp/client.c"; rmdir -- "$tmp"' EXIT
python3 -B - "$tmp/client.c" <<'PY'
import subprocess,sys
from pathlib import Path
src='/home/linuxagent/lmi-boot-menu-build/source/edk2-msm/GPLDrivers/Library/SimpleInit'
s=subprocess.check_output(['git','-C',src,'show','HEAD:src/loggerd/client.c'],text=True)
s=s.replace('static char print_buff[16384];','#include "/recipe/chainload/lmi-console-fit.h"\nstatic char print_buff[16384];')
s=s.replace('\t\tAsciiPrint("%a",print_buff);\n\t\tAsciiPrint("\\n");','\t\tlmi_fit_console_line(print_buff);')
s=s.replace('\tif(console_output){','\tif(console_output&&log->level>=LEVEL_NOTICE){')
assert 'lmi_fit_console_line(print_buff)' in s
Path(sys.argv[1]).write_text(s)
PY
unshare --mount --propagation private bash -s -- "$recipe" "$tmp/client.c" <<'INNER'
set -euo pipefail
root=/home/linuxagent/lmi-boot-menu-build;recipe=$1;client=$2;rootfs=$root/rootfs
mount --bind "$root/source" "$rootfs/source"
mount -o remount,bind,ro "$rootfs/source"
mount --bind "$root/output" "$rootfs/output"
mount -o remount,bind,ro "$rootfs/output"
mount --bind "$recipe" "$rootfs/recipe"
mount -o remount,bind,ro "$rootfs/recipe"
mount --bind "$client" "$rootfs/source/edk2-msm/GPLDrivers/Library/SimpleInit/src/loggerd/client.c"
chroot "$rootfs" /usr/bin/make --no-print-directory \
 -C /source/edk2-msm/GPLDrivers/Library/SimpleInit \
 -f /output/workspace/Build/lmi/RELEASE_CLANG38/AARCH64/src/loggerd/SimpleInitLoggerd/GNUmakefile \
 -f /recipe/chainload/diagnostic-syntax.mk \
 LMI_CHECK_SOURCE=/source/edk2-msm/GPLDrivers/Library/SimpleInit/src/loggerd/client.c lmi-diagnostic-syntax
INNER
echo ARM64_SCREEN_CONSOLE_SYNTAX_PASS_NO_BUILD
