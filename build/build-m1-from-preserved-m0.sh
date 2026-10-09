#!/bin/bash
# Operator-run image build using a preserved M0 ext4 as a read-only source.
set -euo pipefail
[[ $# == 3 ]] || { echo 'usage: BASE_RAW M0_EXT4 OUTPUT_NAME' >&2; exit 2; }
[[ $(id -u) == 0 ]] || { echo 'Run through sudo unshare --mount --propagation private.' >&2; exit 2; }
[[ $(readlink /proc/self/ns/mnt) != $(readlink /proc/1/ns/mnt) ]] || {
    echo 'A private mount namespace is required.' >&2; exit 2;
}
base=$(realpath -e -- "$1")
source_ext4=$(realpath -e -- "$2")
name=$3
[[ $name =~ ^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$ ]] || exit 2
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo=$(CDPATH= cd -- "$script_dir/../.." && pwd)
out="$repo/output"
input_work="$out/$name-m0-input"
source_mount="$input_work/rootfs"
work="$out/$name-work"
raw="$out/$name.img"
sparse="$out/$name.img.android-sparse.img"
[[ -f $base && -f $source_ext4 && ! -L $source_ext4 ]]
[[ $(stat -c %s "$base") == 1490026496 ]]
[[ $(stat -c %s "$source_ext4") == 1233125376 ]]
[[ $(blkid -p -s TYPE -o value "$source_ext4") == ext4 ]]
[[ $(blkid -p -s UUID -o value "$source_ext4") == dba94dfe-0fb9-4f95-970e-22949f4e69dc ]]
: "${M1_MOBIAN_PASSWORD:?Set the Mobian password interactively before invoking this script}"
: "${M1_SSH_PUBLIC_KEY_FILE:?Supply an external public key for development access}"
: "${M1_ANDROID_SUPER_REPORTS_DIR:?Supply paired current Android partition reports}"
for path in "$input_work" "$work" "$raw" "$sparse"; do
    [[ ! -e $path && ! -L $path ]] || { echo "Refusing existing output: $path" >&2; exit 1; }
done
mount --make-rprivate /
mkdir -p "$out"
mkdir "$input_work"
mkdir "$source_mount"
mounted=0
cleanup() {
    local result=$?
    trap - EXIT
    if [[ $mounted == 1 ]]; then
        # Only detach the private mount that was verified below.
        if ! umount -- "$source_mount"; then
            echo "ERROR: source mount cleanup failed: $source_mount" >&2
            result=1
        fi
    fi
    exit "$result"
}
trap cleanup EXIT
mount -t ext4 -o ro,noload,loop,nodev,nosuid -- "$source_ext4" "$source_mount"
mounted=1
loop=$(findmnt -nro SOURCE --target "$source_mount")
[[ $loop =~ ^/dev/loop[0-9]+$ ]]
backing=$(cat "/sys/block/${loop##*/}/loop/backing_file")
[[ $backing == /* ]] || backing="/$backing"
[[ $(realpath -e -- "$backing") == "$source_ext4" ]]
findmnt -nro OPTIONS --target "$source_mount" | tr ',' '\n' | grep -qx ro
[[ $(cat "/sys/block/${loop##*/}/loop/offset") == 0 ]]
[[ $(cat "/sys/block/${loop##*/}/ro") == 1 ]]
test -f "$source_mount/etc/os-release"
test -x "$source_mount/bin/bash"
printf 'M0 source mounted read-only: %s\n' "$source_ext4"
# The builder copies this tree before any package/configuration changes.
bash "$repo/userspace/phosh/scripts/build-m1-phosh.sh" \
    "$base" "$source_mount" "$raw" "$sparse" "$work"
# Let the invoking operator read/copy the completed images; rootfs ownership
# remains untouched inside the working tree and image.
if [[ ${SUDO_UID:-} =~ ^[0-9]+$ && ${SUDO_GID:-} =~ ^[0-9]+$ ]]; then
    chown "$SUDO_UID:$SUDO_GID" "$raw" "$sparse"
fi
chmod 0600 "$raw" "$sparse"
printf 'BUILD_COMPLETE\nRAW=%s\nSPARSE=%s\n' "$raw" "$sparse"
