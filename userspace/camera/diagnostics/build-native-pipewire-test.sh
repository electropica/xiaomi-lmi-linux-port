#!/bin/sh
# Compile a small ARM64 Linux PipeWire diagnostic; no device access.
set -eu
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 INPUT.c INCLUDE_ROOT MATCHED_LIBPIPEWIRE OUTPUT" >&2
    exit 2
fi
"${CC:-aarch64-linux-gnu-gcc}" -O2 -Wall -Wextra -Werror \
    -I"$2/pipewire-0.3" -I"$2/spa-0.2" "$1" "$3" \
    -Xlinker --allow-shlib-undefined -o "$4"
