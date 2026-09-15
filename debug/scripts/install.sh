#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get install -y --no-install-recommends gdb systemd-coredump strace ltrace gstreamer1.0-tools powertop linux-perf valgrind

audit=$(dpkg --audit)
if [[ -n $audit ]]; then
    printf "%s\n" "$audit" >&2
    exit 1
fi
