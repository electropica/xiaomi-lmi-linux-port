#!/bin/bash
# Operator-run full image plus existing-kernel initramfs adaptation. No device I/O.
set -euo pipefail
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=/home/linuxagent/xiaomi-lmi-linux-port
name=mobian-lmi-dualboot-20261021
boot=/mnt/c/Users/julien/Downloads/D-repro-01-power-rpmh-votes-diagnostic-boot.img
layout=/mnt/c/Users/julien/Documents/ChatGPT/Mobian/work/dualboot-layout-20261021-private.json
export M1_CURRENT_LMI_PROFILE_INPUTS=/home/linuxagent/mobian-current-profile-inputs
export M1_CAMERA_ANDROID_LIBCXX=/mnt/c/Users/julien/Documents/ChatGPT/Mobian/work/complete-camera/libcxx-private.so
export M1_ANDROID_SUPER_REPORTS_DIR=/mnt/c/Users/julien/Documents/Codex/2026-09-30/ou-x20/work/android-super-build-inputs-20261009
export M1_SSH_PUBLIC_KEY_FILE=/home/linuxagent/.ssh/id_ed25519_codex_lmi.pub
export M1_TIMEZONE=Europe/Paris
log=/mnt/c/Users/julien/Documents/ChatGPT/Mobian/work/build-dualboot-20261021.log
for suffix in .img .img.android-sparse.img -work -m0-input -boot; do
    [[ ! -e $repo/output/$name$suffix && ! -L $repo/output/$name$suffix ]] || { echo "Output exists: $name$suffix" >&2; exit 1; }
done
python3 "$here/test_prepare.py" --boot "$boot" --layout "$layout"
printf '%s  %s\n' dd327fb7c8d4abcb0fbb5bb839a946d365102af120466b956637e3559f4353e8 "$M1_CAMERA_ANDROID_LIBCXX" | sha256sum -c -
read -rsp 'Mot de passe à utiliser dans Mobian : ' M1_MOBIAN_PASSWORD
printf '\n'; [[ -n $M1_MOBIAN_PASSWORD ]] || exit 1
export M1_MOBIAN_PASSWORD
trap 'unset M1_MOBIAN_PASSWORD' EXIT
set +e
sudo --preserve-env=M1_CURRENT_LMI_PROFILE_INPUTS,M1_CAMERA_ANDROID_LIBCXX,M1_ANDROID_SUPER_REPORTS_DIR,M1_SSH_PUBLIC_KEY_FILE,M1_MOBIAN_PASSWORD,M1_TIMEZONE \
    unshare --mount --propagation private bash "$repo/build/build-complete-lmi.sh" \
    /home/linuxagent/D-repro-01-userdata-rootfs-ssh-key-weston-post-clear-v2.img \
    /home/linuxagent/Mobian-M0-DISPLAY-pmOS_root.ext4 "$name" 2>&1 | tee "$log"
result=${PIPESTATUS[0]}; set -e
printf 'BUILD_EXIT=%s\n' "$result"; ((result==0)) || exit "$result"
python3 "$here/check-image.py" "$repo/output/$name.img"
python3 "$here/prepare.py" --boot "$boot" --layout "$layout" --output "$repo/output/$name-boot"
printf 'DUALBOOT_ARTIFACTS_BUILT_NOT_INSTALLED\nROOTFS_SPARSE=%s\nBOOT=%s\n' \
    "$repo/output/$name.img.android-sparse.img" "$repo/output/$name-boot/mobian-dualboot-boot.img"
printf 'Do NOT flash this rootfs to userdata. Dedicated mobian partition installation is a separate step.\n'
