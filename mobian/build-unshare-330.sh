#!/bin/bash
set -euo pipefail

base="${MOBIAN_M0_BASE:-$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)}"

exec unshare \
    --map-users=0:1001:1 \
    --map-users=1:165537:65535 \
    --map-groups=0:1001:1 \
    --map-groups=1:165537:65535 \
    --setuid 0 \
    --setgid 0 \
    --fork \
    --mount \
    "$base/enter-private-binfmt.sh"
