#!/bin/bash
# Static host validation of the linux7 display1 recipe.
#
# It proves, without producing an image and without touching the handset:
#   1. the three patches apply cleanly to a copy of the pinned tree;
#   2. the merged configuration resolves every required display symbol;
#   3. the patched board DTS compiles with dtc and really carries the lmi
#      panel node, the DSI links and the panel rails;
#   4. the new panel driver compiles against the Linux 7.2 headers.
#
# Usage: bash tools/check-display1-host.sh [--keep]
set -euo pipefail

REPO=/home/linuxagent/xiaomi-lmi-linux-port
EXP=$REPO/kernel/experimental/linux7
FEAS=$REPO/output/minimax-kernel7-feasibility
TREE=$FEAS/linux-v7.2.12-clean
TREE_REV=cc9de5d4b5ab6459f5774946aa3195ad51236fa8
CROSS=aarch64-linux-gnu-
JOBS=$(nproc)
WORK=$FEAS/linux7-display1-check

DTS_NAME=sm8250-xiaomi-lmi-observer.dts
DTS_TREE_REL=arch/arm64/boot/dts/qcom/$DTS_NAME

say() { printf '\n== %s ==\n' "$*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

say "preconditions"
rev=$(git -C "$TREE" rev-parse HEAD 2>/dev/null || echo unknown)
[ "$rev" = "$TREE_REV" ] || fail "tree revision drift: $rev"
echo "tree revision $rev"

say "copy the pinned tree (scratch)"
rm -rf "$WORK"
mkdir -p "$WORK/build"
rsync -a --exclude='.git' "$TREE/" "$WORK/source/"

say "apply the patches"
cp "$EXP/dts/$DTS_NAME" "$WORK/source/$DTS_TREE_REL"
cd "$WORK/source"
for p in "$EXP"/patches/000*.patch; do
	echo "-- $(basename "$p")"
	patch -p1 --forward --batch < "$p" > "$WORK/$(basename "$p").log" || fail "patch failed: $p"
done
echo "all patches applied"

say "merge the configuration"
cp "$EXP/configs/observer-tested.config" "$WORK/build/.config"
"$WORK/source/scripts/kconfig/merge_config.sh" -m -O "$WORK/build" \
	"$WORK/build/.config" "$EXP/configs/display1.fragment" > "$WORK/merge.log" 2>&1
make -s -C "$WORK/source" O="$WORK/build" ARCH=arm64 CROSS_COMPILE=$CROSS olddefconfig
missing=0
for sym in CONFIG_DRM CONFIG_DRM_MSM CONFIG_DRM_MSM_KMS CONFIG_DRM_MSM_DSI \
	   CONFIG_DRM_MSM_DSI_7NM_PHY CONFIG_DRM_PANEL_SAMSUNG_AMS667UU01; do
	if grep -qx "$sym=y" "$WORK/build/.config"; then
		echo "  ok   $sym=y"
	else
		echo "  MISS $sym"; missing=1
	fi
done
[ "$missing" -eq 0 ] || fail "configuration incomplete"

say "compile the board DTB"
cpp -nostdinc -I "$WORK/source/include" -I "$WORK/build/include" -undef -D__DTS__ \
	-x assembler-with-cpp "$WORK/source/$DTS_TREE_REL" > "$WORK/board.dts.tmp"
dtc -I dts -O dtb -o "$WORK/board.dtb" "$WORK/board.dts.tmp" 2> "$WORK/dtc.log"
dtc -I dtb -O dts "$WORK/board.dtb" > "$WORK/board.roundtrip.dts" 2>> "$WORK/dtc.log"
for needle in 'xiaomi,lmi-ams667uu01' 'vddio-supply' 'vci-supply' \
	      'reset-gpios' 'data-lanes' 'qcom,dsi-phy-7nm' 'qcom,pm8150l-rpmh-regulators'; do
	if grep -q -- "$needle" "$WORK/board.roundtrip.dts"; then
		echo "  ok   $needle"
	else
		echo "  MISS $needle"; missing=1
	fi
done
[ "$missing" -eq 0 ] || fail "the compiled DTB does not carry the expected display nodes"
echo "dtb size: $(stat -c %s "$WORK/board.dtb") bytes"

say "compile the panel driver"
make -s -C "$WORK/source" O="$WORK/build" ARCH=arm64 CROSS_COMPILE=$CROSS prepare
make -C "$WORK/source" O="$WORK/build" ARCH=arm64 CROSS_COMPILE=$CROSS \
	drivers/gpu/drm/panel/panel-samsung-ams667uu01.o -j1 2>&1 | tail -20
[ -f "$WORK/build/drivers/gpu/drm/panel/panel-samsung-ams667uu01.o" ] \
	|| fail "the panel driver object was not produced"
echo "panel driver object: $(stat -c %s "$WORK/build/drivers/gpu/drm/panel/panel-samsung-ams667uu01.o") bytes"

say "result"
echo "HOST_VALIDATION_OK"
if [ "${1:-}" != "--keep" ]; then
	rm -rf "$WORK"
	echo "scratch removed (use --keep to retain it)"
fi
