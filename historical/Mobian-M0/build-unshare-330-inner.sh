#!/bin/bash
set -euo pipefail

base=/home/linuxagent/pmos-d-repro-01/Mobian-M0
closure="$base/manifests/m0-minimal-closure.tsv"
repo="$base/local-repo-330"
target="$base/rootfs-final-gpu72"
log="$base/logs/mmdebstrap-unshare-gpu72.log"

test "$(id -u)" -eq 0
test -e /proc/sys/fs/binfmt_misc/qemu-aarch64

if [ -e "$target" ]; then
    echo "Refusing to overwrite existing target: $target" >&2
    exit 1
fi

mkdir -p "$repo" "$base/logs"
find "$repo" -mindepth 1 -maxdepth 1 -type f -delete

while IFS=$'\t' read -r package version arch installed_size download_size sha path; do
    test -f "$path"
    test "$(sha256sum "$path" | awk '{print $1}')" = "$sha"
    ln "$path" "$repo/$(basename "$path")"
done < "$closure"

(
    cd "$repo"
    dpkg-scanpackages . /dev/null > Packages
    gzip -n -9 -c Packages > Packages.gz
)
"$base/generate-local-repo-release.sh" "$repo"

include=$(awk -F '\t' '{printf "%s%s=%s", sep, $1, $2; sep=","}' "$closure")

export PATH="$base/tools/usr/sbin:$base/tools/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export DEBOOTSTRAP_DIR="$base/tools/usr/share/debootstrap"

sources=$(cat <<EOF
deb [trusted=yes] file://$repo ./
EOF
)

"$base/tools/usr/bin/mmdebstrap" \
    --mode=unshare \
    --skip=check/qemu \
    --format=directory \
    --architectures=arm64 \
    --variant=minbase \
    --components=main \
    --aptopt='Apt::Install-Recommends "false"' \
    --aptopt='Acquire::Languages "none"' \
    --aptopt='Binary::apt::APT::Keep-Downloaded-Packages "true"' \
    --aptopt='APT::Keep-Downloaded-Packages "true"' \
    --hook-dir="$base/tools/usr/share/mmdebstrap/hooks/file-mirror-automount" \
    --customize-hook='printf "deb http://deb.debian.org/debian trixie main\ndeb http://security.debian.org/debian-security trixie-security main\n" > "$1/etc/apt/sources.list"' \
    --customize-hook='mkdir -p "$1/etc/apt/sources.list.d" "$1/etc/apt/preferences.d"' \
    --customize-hook='printf "Types: deb\nURIs: https://repo.mobian.org/\nSuites: trixie\nComponents: main\nSigned-By: /usr/share/keyrings/mobian-archive-keyring.gpg\n" > "$1/etc/apt/sources.list.d/mobian.sources"' \
    --customize-hook='printf "Package: *\nPin: release o=Mobian\nPin-Priority: 700\n" > "$1/etc/apt/preferences.d/00-mobian-priority"' \
    --include="$include" \
    trixie "$target" "$sources" \
    > "$log" 2>&1


chroot "$target" /usr/sbin/groupadd -g 1000 mobian
chroot "$target" /usr/sbin/useradd -m -u 1000 -g 1000 -s /bin/bash mobian
chroot "$target" /usr/sbin/usermod -a -G audio,video,plugdev,input,render mobian
echo "mobian_user_created uid=1000 gid=1000 groups=audio,video,plugdev,input,render"

gpu72="/home/linuxagent/pmos-d-repro-01/analysis/gpu71-mobian-gles2-integration"
test -x "$gpu72/INSTALL-IN-ROOTFS.sh"
( cd "$gpu72" && ./INSTALL-IN-ROOTFS.sh "$target" )
printf "gpu72_integration_completed target=%s GPU72_ROOTFS_INTEGRATION=PASS\n" "$target"

printf 'mmdebstrap_completed target=%s\n' "$target"
