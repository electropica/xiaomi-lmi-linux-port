#!/bin/bash
set -euo pipefail

base="${MOBIAN_M0_BASE:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"
cache="$base/rootfs/var/cache/apt/archives"
tmp="$base/staging/closure-measure"
rm -rf "$tmp"
mkdir -p "$tmp"

{
  find "$cache" -maxdepth 1 -type f -name '*.deb' -print0
  printf '%s\0' "$base/downloads/mobian-archive-keyring_20251117.0_all.deb"
} | sort -zu | xargs -0 sha256sum >"$base/manifests/m0-minimal-debs.sha256"

{
  find "$cache" -maxdepth 1 -type f -name '*.deb' -print0
  printf '%s\0' "$base/downloads/mobian-archive-keyring_20251117.0_all.deb"
} | sort -zu | while IFS= read -r -d '' deb; do
  package=$(dpkg-deb -f "$deb" Package)
  version=$(dpkg-deb -f "$deb" Version)
  arch=$(dpkg-deb -f "$deb" Architecture)
  installed=$(dpkg-deb -f "$deb" Installed-Size)
  size=$(stat -c %s "$deb")
  sha=$(sha256sum "$deb" | awk '{print $1}')
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$package" "$version" "$arch" "$installed" "$size" "$sha" "$deb"
done | sort -t $'\t' -k1,1 -k2,2V >"$tmp/all.tsv"

# The archive may contain an older base version and its security update.
# Keep the last (highest version-sort) entry for each package.
awk -F '\t' '{row[$1]=$0} END {for (p in row) print row[p]}' "$tmp/all.tsv" |
  sort -t $'\t' -k1,1 >"$base/manifests/m0-minimal-closure.tsv"

awk -F '\t' 'BEGIN{s=0;d=0;n=0} {s+=$4;d+=$5;n++} END {
  printf "packages=%d\ninstalled_size_kib=%d\ninstalled_size_bytes=%d\ndownload_size_bytes=%d\n", n,s,s*1024,d
}' "$base/manifests/m0-minimal-closure.tsv" >"$base/manifests/m0-minimal-totals.txt"

sort -t $'\t' -k4,4nr "$base/manifests/m0-minimal-closure.tsv" | head -30 \
  >"$base/manifests/m0-minimal-top30.tsv"
