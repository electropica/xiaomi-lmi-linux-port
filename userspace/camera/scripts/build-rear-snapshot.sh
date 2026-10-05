#!/bin/bash
# Small userspace diagnostics only; never builds a kernel/rootfs or copies OEM firmware.
set -euo pipefail
if [[ $# != 3 ]]; then
    echo 'Usage: build-rear-snapshot.sh NDK_TOOLCHAIN_BIN MATCHING_ANDROID_LIBCXX OUTPUT_DIR' >&2
    exit 2
fi
toolchain=$(realpath -- "$1")
libcxx=$(realpath -- "$2")
output=$(realpath -m -- "$3")
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
camera_dir=$(cd -- "$script_dir/.." && pwd)
test -x "$toolchain/aarch64-linux-android35-clang"
test -x "$toolchain/aarch64-linux-android35-clang++"
test -f "$libcxx"
# A fresh output directory avoids mixing stale binaries with changed sources.
test ! -e "$output"
mkdir -m 0700 -- "$output"
cp -- "$camera_dir"/files/lmi-camera.py \
    "$camera_dir"/files/lmi-camera-capture-service.py \
    "$camera_dir"/files/lmi-camera-capture.service \
    "$camera_dir"/files/lmi-camera.desktop \
    "$script_dir/install-rear-snapshot.py" \
    "$camera_dir"/diagnostics/camera-test-capture.py \
    "$camera_dir"/diagnostics/camera-test-rear-preview.py \
    "$camera_dir"/diagnostics/inspect-system-ext-metadata.py "$output/"
"$toolchain/aarch64-linux-android35-clang++" -shared -fPIC -O2 \
    -D_LIBCPP_ABI_NAMESPACE=__1 -Wall -Wextra -Werror -nostdlib++ \
    "$camera_dir/diagnostics/camera-qti-bridge.cpp" "$libcxx" -ldl \
    -Wl,-soname,liblmi_qti_bridge.so -o "$output/liblmi_qti_bridge.so"
"$toolchain/aarch64-linux-android35-clang" -Wall -Wextra -Werror \
    "$camera_dir/diagnostics/camera-module-capture.c" -L"$output" \
    -llmi_qti_bridge -ldl -o "$output/camera-module-capture"
"$toolchain/aarch64-linux-android35-clang" -shared -fPIC -O2 \
    -Wall -Wextra -Werror "$camera_dir/diagnostics/private-context-test.c" \
    -ldl -o "$output/lmi-camera-private-context-test.so"
echo 'REAR_SNAPSHOT_SOURCE_BUNDLE_READY_NO_OEM_FIRMWARE_INCLUDED'
