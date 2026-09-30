#!/bin/bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
base="${MOBIAN_M0_BASE:-$(CDPATH= cd -- "$script_dir/../files" && pwd)}"
export MOBIAN_M0_BASE="$base"

exec unshare \
    --map-users=0:1001:1 \
    --map-users=1:165537:65535 \
    --map-groups=0:1001:1 \
    --map-groups=1:165537:65535 \
    --setuid 0 \
    --setgid 0 \
    --fork \
    --mount \
    "$script_dir/enter-private-binfmt.sh"
