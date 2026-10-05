#!/bin/sh
# Build only a small process-local aarch64 Linux diagnostic library.
# Usage: sh build-snapshot-tuning.sh /path/to/clang /path/to/output.so
set -eu
compiler=${1:?Pass a Clang compiler supporting aarch64 Linux and lld}
output=${2:?Pass the diagnostic shared-library output path}
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
"$compiler" --target=aarch64-linux-gnu -fuse-ld=lld -shared -fPIC -nostdlib   -Wall -Wextra -Werror -Xlinker -soname -Xlinker lmi-snapshot-tuning.so   -o "$output" "$source_dir/lmi-snapshot-tuning.c"
