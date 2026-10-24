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
toolchain=${M1_ANDROID_TOOLCHAIN:-/home/linuxagent/android-ndk-r27d/toolchains/llvm/prebuilt/linux-x86_64/bin}
[[ $(chroot "$root" dpkg --print-architecture) == arm64 ]]
test -x "$toolchain/aarch64-linux-android35-clang"
test -f "$M1_CAMERA_ANDROID_LIBCXX"
test "$(df --output=avail -B1 "$repo" | tail -1)" -ge 21474836480
unset M1_COMPLETE_LMI_PROFILE M1_COMPLETE_CAMERA_BUNDLE
python3 "$repo/build/profiles/lmi-current/test-stage.py" "$M1_CURRENT_LMI_PROFILE_INPUTS"
python3 "$repo/build/profiles/lmi-current/test-complete-stage.py" "$M1_CURRENT_LMI_PROFILE_INPUTS"
python3 "$repo/userspace/apps/scripts/check-builder-staging.py"
version=0.46.0-3+deb13u1+lmigaugewake3+homedrag8
phosh="$root/build/phosh_${version}_arm64.deb"
common="$root/build/phosh-common_${version}_all.deb"
if [[ ! -f $phosh || ! -f $common ]]; then
    bash "$repo/userspace/phosh/home-drag-candidate/build-arm64.sh"
fi
for package in "$phosh" "$common"; do
    test "$(dpkg-deb -f "$package" Version)" = "$version"
done
phoc="$root/build/phoc_0.46.0-1+lmishelldnd1+thumblinear1+thumbrows1+thumbfbo1_arm64.deb"
test -f "$phoc" || { echo "Build the qualified Phoc private-thumbnail package first." >&2; exit 1; }
test "$(dpkg-deb -f "$phoc" Version)" = 0.46.0-1+lmishelldnd1+thumblinear1+thumbrows1+thumbfbo1
test "$(sha256sum "$phoc" | cut -d' ' -f1)" = b212c98ca155e57bcd10a29be57fe02fabf9b947826ffb1d4900c52648cedbb5
# Serialize later use of the shared ARM build root as well.
exec 9>/run/lmi-phosh-gauge-build.lock
flock -n 9 || { echo 'Shared ARM build root is busy.' >&2; exit 1; }
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
python3 - "$M1_CURRENT_LMI_PROFILE_INPUTS" "$inputs" "$phosh" "$common" "$phoc" <<'PYINPUT'
from pathlib import Path
import hashlib,shutil,sys
old,new,phosh,common,phoc=map(Path,sys.argv[1:])
files=[]
for line in (old/'SHA256SUMS').read_text().splitlines():
    digest,name=line.split('  ',1)
    if not name.startswith(('phosh_','phosh-common_','phoc_')):files.append(old/name)
files += [phosh,common,phoc]
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
