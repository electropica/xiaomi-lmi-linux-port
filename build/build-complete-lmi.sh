#!/bin/bash
# User-run, integrated package + camera + full userdata build. No device access.
set -euo pipefail
[[ $# == 3 && $(id -u) == 0 ]] || { echo 'usage (root/private mount namespace): BASE_RAW M0_EXT4 OUTPUT_NAME' >&2; exit 2; }
[[ $(readlink /proc/self/ns/mnt) != $(readlink /proc/1/ns/mnt) ]] || exit 2
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
: "${M1_CURRENT_LMI_PROFILE_INPUTS:?Validated stable input directory required}"
: "${M1_CAMERA_ANDROID_LIBCXX:?Matching external Android libc++.so required}"
: "${M1_ANDROID_SUPER_REPORTS_DIR:?Current paired partition reports required}"
: "${M1_SSH_PUBLIC_KEY_FILE:?External SSH public key required}"
: "${M1_MOBIAN_PASSWORD:?Set the Mobian password interactively}"
[[ $3 =~ ^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$ ]] || exit 2
for path in "$repo/output/$3.img" "$repo/output/$3.img.android-sparse.img" "$repo/output/$3-work" "$repo/output/$3-m0-input"; do
    [[ ! -e $path && ! -L $path ]] || { echo "Refusing existing output: $path" >&2; exit 1; }
done
exec 7>/run/lmi-complete-build.lock
flock -n 7 || { echo 'Another complete build is running.' >&2; exit 1; }
root=/home/linuxagent/phosh-gauge-wake-build/rootfs
exec 8>/run/lmi-gsd-quiet-build.lock
flock -n 8 || { echo 'GSD build is busy.' >&2; exit 1; }
exec 9>/run/lmi-phosh-gauge-build.lock
flock -n 9 || { echo 'Phosh build is busy.' >&2; exit 1; }
toolchain=${M1_ANDROID_TOOLCHAIN:-/home/linuxagent/android-ndk-r27d/toolchains/llvm/prebuilt/linux-x86_64/bin}
[[ $(chroot "$root" dpkg --print-architecture) == arm64 ]]
test -x "$toolchain/aarch64-linux-android35-clang"
test -f "$M1_CAMERA_ANDROID_LIBCXX"
test "$(df --output=avail -B1 "$repo" | tail -1)" -ge 21474836480
unset M1_COMPLETE_LMI_PROFILE M1_COMPLETE_CAMERA_BUNDLE
python3 "$repo/build/profiles/lmi-current/test-stage.py" "$M1_CURRENT_LMI_PROFILE_INPUTS"
python3 "$repo/build/profiles/lmi-current/test-complete-stage.py" "$M1_CURRENT_LMI_PROFILE_INPUTS"
python3 "$repo/userspace/apps/scripts/check-builder-staging.py"
version=0.46.0-3+deb13u1+lmigaugewake3+homedrag8+esrquiet1+drawerscroll1+irqnames1+drawerpreview1
phosh="$root/build/phosh_${version}_arm64.deb"
common="$root/build/phosh-common_${version}_all.deb"
gsd_version=48.1-1+lmiquietgauge3+esrquiet1+irqnames1
gsd="$root/build/gnome-settings-daemon_${gsd_version}_arm64.deb"
gsd_common="$root/build/gnome-settings-daemon-common_${gsd_version}_all.deb"
for package in "$phosh" "$common" "$gsd" "$gsd_common"; do
    test -f "$package" || { echo "Missing qualified IRQ-name/drawer package: $package" >&2; exit 1; }
done
for package in "$phosh" "$common"; do
    test "$(dpkg-deb -f "$package" Version)" = "$version"
done
for package in "$gsd" "$gsd_common"; do
    test "$(dpkg-deb -f "$package" Version)" = "$gsd_version"
done
test "$(sha256sum "$phosh" | cut -d' ' -f1)" = 41ffc0657495dc250f5b551b6ab505ff5354bc207f0ad2e885efc7953624cd11
test "$(sha256sum "$common" | cut -d' ' -f1)" = 5bbd163f674ccb16fcd37fac3655fc4cee0e7bdab5508d8579486b4db5ba13e0
test "$(sha256sum "$gsd" | cut -d' ' -f1)" = eca42cc04d0f509c93c28e8e37a3ecaf65316fecd92a9438ba62031862889972
test "$(sha256sum "$gsd_common" | cut -d' ' -f1)" = fdc6e4513be1eaf07c61899d9ac86ae55a84744bda4476ecf003e354cb8e2345
phoc="$root/build/phoc_0.46.0-1+lmishelldnd1+thumblinear1+thumbrows1+thumbfbo1_arm64.deb"
test -f "$phoc" || { echo "Build the qualified Phoc private-thumbnail package first." >&2; exit 1; }
test "$(dpkg-deb -f "$phoc" Version)" = 0.46.0-1+lmishelldnd1+thumblinear1+thumbrows1+thumbfbo1
test "$(sha256sum "$phoc" | cut -d' ' -f1)" = b212c98ca155e57bcd10a29be57fe02fabf9b947826ffb1d4900c52648cedbb5
# apt and the ARM compiler run in a real chroot, not an empty /dev/pts tree.
python3 "$repo/userspace/camera/snapshot-bundle/prepare-chroot.py" "$root"
# One private bundle and input directory per named image, outside Git.
export M1_COMPLETE_CAMERA_BUNDLE="/home/linuxagent/$3-camera-bundle"
if [[ ! -e $M1_COMPLETE_CAMERA_BUNDLE/SHA256SUMS ]]; then
    python3 "$repo/userspace/camera/snapshot-bundle/build-bundle.py" \
        --repo "$repo" --root "$root" --output "$M1_COMPLETE_CAMERA_BUNDLE" \
        --libcxx "$M1_CAMERA_ANDROID_LIBCXX" --toolchain "$toolchain"
fi
python3 "$repo/userspace/camera/snapshot-bundle/check-bundle.py" "$M1_COMPLETE_CAMERA_BUNDLE"
inputs="/home/linuxagent/$3-inputs"
python3 - "$M1_CURRENT_LMI_PROFILE_INPUTS" "$inputs" "$phosh" "$common" "$gsd" "$gsd_common" "$phoc" <<'PYINPUT'
from pathlib import Path
import hashlib,shutil,sys
old,new,phosh,common,gsd,gsd_common,phoc=map(Path,sys.argv[1:])
files=[]
for line in (old/'SHA256SUMS').read_text().splitlines():
    digest,name=line.split('  ',1)
    if not name.startswith(('phosh_','phosh-common_','gnome-settings-daemon_','gnome-settings-daemon-common_','phoc_')):files.append(old/name)
files += [phosh,common,gsd,gsd_common,phoc]
assert len(files)==9 and len({p.name for p in files})==9
assert not new.is_symlink()
new.mkdir(exist_ok=True)
for p in files:
    dest=new/p.name
    assert not dest.is_symlink()
    if dest.exists():assert dest.read_bytes()==p.read_bytes(),dest
    else:shutil.copy2(p,dest)
manifest=''.join(hashlib.sha256((new/p.name).read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files)
if (new/'SHA256SUMS').exists():assert (new/'SHA256SUMS').read_text()==manifest
else:(new/'SHA256SUMS').write_text(manifest)
PYINPUT
export M1_CURRENT_LMI_PROFILE_INPUTS="$inputs" M1_COMPLETE_LMI_PROFILE=1
bash "$repo/build/build-current-lmi.sh" "$@"
printf 'COMPLETE_IMAGE_WITH_NATIVE_HOME_AND_SNAPSHOT\n'
