#!/usr/bin/env bash
# Preflight and rebuild an already reconstructed tree; never access a device.
set -euo pipefail
[[ $# == 4 && ( $1 == --plan || $1 == --execute ) ]] || {
  echo 'Usage: bash build-kernel.sh --plan|--execute SOURCE NEW_OUTPUT TESTED_DTB' >&2; exit 2;
}
mode=$1; src=$(realpath -e "$2"); out=$3; dtb=$(realpath -e "$4")
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cross=${CROSS_COMPILE:-aarch64-linux-gnu-}
test -f "$src/Makefile"
test ! -e "$out" || { echo 'Output exists; refusing overwrite' >&2; exit 2; }
for c in make python3 sha256sum "${cross}gcc"; do command -v "$c" >/dev/null; done
check() { printf '%s  %s\n' "$1" "$2" | sha256sum -c -; }
check 0e84300dd95e26cb1b32378c9802925efde86be286ecb2f3d5b9f40f21666c48 "$here/config-tested"
check 1fc0316ac94754dac33c34cb8ab57b76ba4dc10b074f64c93d03f99beeec310b "$dtb"
check d6f8516bac58ca9b5530f0d72c5fff09b04075f4e3cf93bba0a7aad3877b30be "$src/drivers/power/supply/qcom_fg.c"
check d2254446726b12d6ad06b11dc324b73fa9bc34a52eb6bfd921511f929e0245ad "$src/drivers/power/supply/qcom_pm8150b_charger.c"
check 201b2c0eb87eafd3539028baf70531cb97e0f70e1b578114b538257ea6e01140 "$src/drivers/media/i2c/ov13b10.c"
check a5d1d67834c36485f74729672c1ae879a7087566f8a067d1b3e45987c743522a "$src/sound/soc/codecs/tfa98xx/src/tfa98xx.c"
check 0e5468aabdda9969711047ba922ad0713c776dab4186794bbb191df682f7bed8 "$src/sound/soc/codecs/tfa98xx/src/tfa_dsp.c"
check f11cf3f6fbf5d7db21bb449a2b6b712920f5794e74cb7ec5d6dcf44d28c63e94 "$src/sound/soc/codecs/tfa98xx/src/tfa_init.c"
check b6aab2e5f8fd5690cfd2882ed6d4b7d3024b66a2f418b5a5ce794beb56e43aef "$src/sound/soc/codecs/tfa98xx/inc/config.h"
echo "Compiler: $("${cross}gcc" --version | head -1)"
echo 'PREPARED_SOURCE_CHECKS_PASS (not a complete source identity proof)'
[[ $mode == --execute ]] || exit 0
mkdir "$out"
out=$(realpath -e "$out")
cp "$here/config-tested" "$out/.config"
make -C "$src" O="$out" ARCH=arm64 CROSS_COMPILE="$cross" olddefconfig
python3 "$src/scripts/diffconfig" "$here/config-tested" "$out/.config" > "$out/config-differences.txt"
if [[ -s "$out/config-differences.txt" ]]; then
  cat "$out/config-differences.txt" >&2; echo 'Configuration changed; build stopped' >&2; exit 2
fi
make -C "$src" O="$out" ARCH=arm64 CROSS_COMPILE="$cross" -j"${LMI_BUILD_JOBS:-4}" Image 2>&1 | tee "$out/build.log"
cp "$dtb" "$out/previously-tested.dtb"
sha256sum "$out/arch/arm64/boot/Image" "$out/previously-tested.dtb" "$out/.config"
if grep -nEi '(^|[[:space:]])(warning|error):' "$out/build.log"; then
  echo 'Compiler messages found; inspect before using this output' >&2; exit 2
fi
echo 'RECONSTRUCTED_KERNEL_BUILT_NOT_FLASHABLE'
