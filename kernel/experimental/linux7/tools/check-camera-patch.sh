#!/bin/bash
# Static host validation of the linux7 camera sensor patch.
#
# It proves, without producing an image and without touching the handset:
#   1. the camera patch applies cleanly to a copy of the pinned tree and, when
#      the community tree is present, to that tree as well;
#   2. the patched driver carries the OF match table and compiles as an object
#      with the camera configuration;
#   3. the merged configuration resolves the whole camera path;
#   4. the community board device tree already describes the rear sensor the
#      way the driver requires, so no device tree change is needed.
#
# Usage: bash tools/check-camera-patch.sh [--keep]
set -euo pipefail

REPO=/home/linuxagent/xiaomi-lmi-linux-port
EXP=$REPO/kernel/experimental/linux7
FEAS=$REPO/output/minimax-kernel7-feasibility
TREE=$FEAS/linux-v7.2.12-clean
TREE_REV=cc9de5d4b5ab6459f5774946aa3195ad51236fa8
COMMUNITY=/home/linuxagent/lmi-modem-trial/source
CROSS=aarch64-linux-gnu-
JOBS=$(nproc)
WORK=$FEAS/linux7-camera-check
PATCH=$EXP/patches/0004-lmi-ov13b10-of-match.patch
DRIVER=drivers/media/i2c/ov13b10.c

say() { printf '\n== %s ==\n' "$*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

say "preconditions"
[ -d "$TREE" ] || fail "missing pinned tree: $TREE"
rev=$(git -c safe.directory="$TREE" -C "$TREE" rev-parse HEAD 2>/dev/null || echo unknown)
[ "$rev" = "$TREE_REV" ] || fail "tree revision drift: $rev"
echo "tree revision $rev"
[ -f "$PATCH" ] || fail "missing patch: $PATCH"
command -v ${CROSS}gcc >/dev/null || fail "missing cross compiler: ${CROSS}gcc"
command -v dtc >/dev/null || fail "missing dtc"
echo "cross compiler: $(${CROSS}gcc --version | head -1)"

say "copy the pinned tree (scratch)"
rm -rf "$WORK"
mkdir -p "$WORK/build"
rsync -a --exclude='.git' "$TREE/" "$WORK/source/"

say "apply the patch series"
# The display patch series rewrites the board device tree of the project, which
# is not part of the pristine tree: it has to be placed first, exactly as the
# display check does it.
DTS_NAME=sm8250-xiaomi-lmi-observer.dts
DTS_TREE_REL=arch/arm64/boot/dts/qcom/$DTS_NAME
cp "$EXP/dts/$DTS_NAME" "$WORK/source/$DTS_TREE_REL"
cd "$WORK/source"
for p in "$EXP"/patches/000*.patch; do
	echo "-- $(basename "$p")"
	patch -p1 --forward --batch < "$p" > "$WORK/$(basename "$p").log" || fail "patch failed: $p"
done
echo "all patches applied"

say "the patched driver carries the OF match table"
grep -q 'ovti,ov13b10' "$DRIVER" || fail "the compatible string is missing"
grep -q 'MODULE_DEVICE_TABLE(of, ov13b10_of_match)' "$DRIVER" || fail "the OF device table is missing"
grep -q '\.of_match_table = ov13b10_of_match' "$DRIVER" || fail "the driver does not declare the OF table"
grep -q 'ACPI_PTR(ov13b10_acpi_ids)' "$DRIVER" || fail "the ACPI table was lost"
echo "  ok   the OF table is present and the ACPI table is intact"

say "merge the camera configuration"
cp "$EXP/configs/observer-tested.config" "$WORK/build/.config"
"$WORK/source/scripts/kconfig/merge_config.sh" -m -O "$WORK/build" \
	"$WORK/build/.config" "$EXP/configs/camera.fragment" > "$WORK/merge.log" 2>&1
make -s -C "$WORK/source" O="$WORK/build" ARCH=arm64 CROSS_COMPILE=$CROSS olddefconfig
missing=0
for sym in CONFIG_MEDIA_SUPPORT CONFIG_MEDIA_CAMERA_SUPPORT CONFIG_MEDIA_PLATFORM_SUPPORT \
	   CONFIG_MEDIA_CONTROLLER CONFIG_VIDEO_DEV CONFIG_V4L_PLATFORM_DRIVERS \
	   CONFIG_V4L2_ASYNC CONFIG_V4L2_FWNODE CONFIG_VIDEO_V4L2_SUBDEV_API \
	   CONFIG_VIDEOBUF2_DMA_SG CONFIG_VIDEO_CAMERA_SENSOR \
	   CONFIG_VIDEO_OV13B10 CONFIG_VIDEO_QCOM_CAMSS CONFIG_FUSE_FS; do
	if grep -qx "$sym=y" "$WORK/build/.config"; then
		echo "  ok   $sym=y"
	else
		echo "  MISS $sym"; missing=1
	fi
done
[ "$missing" -eq 0 ] || fail "the camera configuration is incomplete"

say "compile the patched sensor driver"
make -s -C "$WORK/source" O="$WORK/build" ARCH=arm64 CROSS_COMPILE=$CROSS prepare
make -C "$WORK/source" O="$WORK/build" ARCH=arm64 CROSS_COMPILE=$CROSS \
	"${DRIVER%.c}.o" -j"$JOBS" 2>&1 | tail -20
[ -f "$WORK/build/${DRIVER%.c}.o" ] || fail "the sensor driver object was not produced"
echo "sensor driver object: $(stat -c %s "$WORK/build/${DRIVER%.c}.o") bytes"

say "the community tree takes the same patch"
if [ -d "$COMMUNITY" ]; then
	cd "$COMMUNITY"
	patch -p1 --dry-run --batch < "$PATCH" || fail "the patch does not apply to the community tree"
	echo "  ok   the patch applies to the community tree"
else
	echo "  the community tree is absent, the community half is skipped"
fi

say "the community board device tree already satisfies the driver"
if [ -d "$COMMUNITY" ]; then
	DTS=$COMMUNITY/arch/arm64/boot/dts/qcom/sm8250-xiaomi-lmi.dts
	[ -f "$DTS" ] || fail "missing board device tree: $DTS"
	for needle in 'compatible = "ovti,ov13b10"' 'assigned-clock-rates = <19200000>' \
		      'data-lanes = <1 2 3 4>' 'link-frequencies = /bits/ 64 <560000000>' \
		      'avdd-supply' 'dovdd-supply' 'dvdd-supply' 'reset-gpios'; do
		if grep -q -- "$needle" "$DTS"; then
			echo "  ok   $needle"
		else
			echo "  MISS $needle"; missing=1
		fi
	done
	[ "$missing" -eq 0 ] || fail "the board device tree does not satisfy the driver"
	echo "  ok   no device tree change is needed"
fi

say "result"
echo "HOST_VALIDATION_OK"
if [ "${1:-}" != "--keep" ]; then
	rm -rf "$WORK"
	echo "scratch removed (use --keep to retain it)"
fi
