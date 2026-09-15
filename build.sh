#!/bin/bash
set -euo pipefail

repo_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
phosh_builder="$repo_dir/phosh/scripts/build-m1-phosh.sh"
output_dir="$repo_dir/output"

if [[ $# -lt 2 || $# -gt 3 ]]; then
    echo "usage: $0 BASE_RAW M0_TREE [NAME]" >&2
    echo "example: INSTALL_OPTIONAL_APPS=1 INSTALL_DEBUG_TOOLS=1 $0 /path/base.img /path/m0-rootfs lmi-test" >&2
    exit 2
fi

base_raw=$1
m0_tree=$2
name=${3:-mobian-lmi}

raw="$output_dir/$name.img"
sparse="$output_dir/$name.img.android-sparse.img"
work="$output_dir/$name-work"

test -f "$base_raw"
test -d "$m0_tree"
test -x "$phosh_builder"

mkdir -p "$output_dir"

if [[ -e "$raw" || -e "$sparse" || -e "$work" ]]; then
    echo "Refusing to overwrite existing output for: $name" >&2
    exit 1
fi

exec unshare \
    --mount \
    --map-users=0:1001:1 \
    --map-users=1:165537:65535 \
    --map-groups=0:1001:1 \
    --map-groups=1:165537:65535 \
    --setuid 0 \
    --setgid 0 \
    --fork \
    "$phosh_builder" \
    "$base_raw" \
    "$m0_tree" \
    "$raw" \
    "$sparse" \
    "$work"
