#!/bin/bash
set -euo pipefail

base="${MOBIAN_M0_BASE:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"
closure="$base/manifests/m0-minimal-closure.tsv"
repo="$base/local-repo-330"
target="$base/rootfs-final-330"
log="$base/logs/mmdebstrap-unshare-330.log"
keyrings="$base/keyrings-330"

test "$(id -u)" -eq 0
test -e /proc/sys/fs/binfmt_misc/qemu-aarch64

if [ -e "$target" ]; then
    echo "Refusing to overwrite existing target: $target" >&2
    exit 1
fi

mkdir -p "$repo" "$keyrings" "$base/logs"
find "$repo" -mindepth 1 -maxdepth 1 -type f -delete

while IFS=$'\t' read -r package version arch installed_size download_size sha path; do
    test -f "$path"
    test "$(sha256sum "$path" | awk '{print $1}')" = "$sha"
    ln "$path" "$repo/$(basename "$path")"
done < "$closure"

dpkg-scanpackages "$repo" /dev/null > "$repo/Packages"
gzip -n -9 -c "$repo/Packages" > "$repo/Packages.gz"

debian_keyring_deb=$(awk -F '\t' '$1 == "debian-archive-keyring" {print $7}' "$closure")
dpkg-deb --fsys-tarfile "$debian_keyring_deb" \
    | tar -xOf - ./usr/share/keyrings/debian-archive-keyring.pgp \
    > "$keyrings/debian-archive-keyring.gpg"
dpkg-deb --fsys-tarfile "$base/downloads/mobian-archive-keyring_20251117.0_all.deb" \
    | tar -xOf - ./usr/share/keyrings/mobian-archive-keyring.gpg \
    > "$keyrings/mobian-archive-keyring.gpg"

include=$(awk -F '\t' '{printf "%s%s=%s", sep, $1, $2; sep=","}' "$closure")

export PATH="$base/tools/usr/sbin:$base/tools/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export DEBOOTSTRAP_DIR="$base/tools/usr/share/debootstrap"

sources=$(cat <<EOF
deb [trusted=yes] file://$repo ./
deb http://deb.debian.org/debian trixie main
deb http://security.debian.org/debian-security trixie-security main
deb https://repo.mobian.org/ trixie main
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
    --keyring="$keyrings" \
    --hook-dir="$base/tools/usr/share/mmdebstrap/hooks/file-mirror-automount" \
    --setup-hook='mkdir -p "$1/etc/apt/preferences.d"' \
    --setup-hook='printf "Package: *\nPin: release o=Mobian\nPin-Priority: 700\n" > "$1/etc/apt/preferences.d/00-mobian-priority"' \
    --include="$include" \
    trixie "$target" "$sources" \
    > "$log" 2>&1

printf 'mmdebstrap_completed target=%s\n' "$target"
