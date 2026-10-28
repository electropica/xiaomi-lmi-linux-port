#!/bin/bash
# Build the Linux 7 community kernel with the rear camera sensor bound.
#
# The kernel of the permanent boot is built from the community tree, not from
# the pinned tree of the observer kit. This script takes that tree, applies
# the camera patch, merges the camera configuration, builds the kernel and its
# device tree, and checks the result.
#
# It never touches the input tree unless --in-place is given: by default the
# tree is copied to a scratch directory, so the operator can run it again and
# compare two results.
#
# Usage:
#   bash tools/build-community-camera-kernel.sh [--tree DIR] [--build DIR]
#         [--out DIR] [--jobs N] [--prepare-only] [--in-place]
#
# Defaults:
#   --tree  /home/linuxagent/lmi-modem-trial/source
#   --build /home/linuxagent/lmi-modem-trial/build
#   --out   <repo>/output/minimax-kernel7-feasibility/community-camera-kernel
set -euo pipefail

REPO=/home/linuxagent/xiaomi-lmi-linux-port
EXP=$REPO/kernel/experimental/linux7
PATCH=$EXP/patches/0004-lmi-ov13b10-of-match.patch
FRAGMENT=$EXP/configs/camera.fragment
DTS=sm8250-xiaomi-lmi.dts
DTS_REL=arch/arm64/boot/dts/qcom/$DTS
CROSS=aarch64-linux-gnu-

TREE=/home/linuxagent/lmi-modem-trial/source
BUILD=/home/linuxagent/lmi-modem-trial/build
OUT=$REPO/output/minimax-kernel7-feasibility/community-camera-kernel
JOBS=$(nproc)
PREPARE_ONLY=0
IN_PLACE=0

while [ $# -gt 0 ]; do
	case "$1" in
	--tree) TREE=$2; shift 2 ;;
	--build) BUILD=$2; shift 2 ;;
	--out) OUT=$2; shift 2 ;;
	--jobs) JOBS=$2; shift 2 ;;
	--prepare-only) PREPARE_ONLY=1; shift ;;
	--in-place) IN_PLACE=1; shift ;;
	*) echo "unknown argument: $1" >&2; exit 2 ;;
	esac
done

say() { printf '\n== %s ==\n' "$*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

say "preconditions"
[ -d "$TREE" ] || fail "missing community tree: $TREE"
[ -f "$BUILD/.config" ] || fail "missing community configuration: $BUILD/.config"
[ -f "$PATCH" ] || fail "missing patch: $PATCH"
[ -f "$FRAGMENT" ] || fail "missing fragment: $FRAGMENT"
[ -f "$TREE/$DTS_REL" ] || fail "missing board device tree: $TREE/$DTS_REL"
for tool in rsync patch make dtc; do command -v $tool >/dev/null || fail "missing $tool"; done
command -v ${CROSS}gcc >/dev/null || fail "missing cross compiler"
echo "tree: $TREE"
echo "configuration: $BUILD/.config"
echo "output: $OUT"

say "the working tree"
if [ "$IN_PLACE" -eq 1 ]; then
	SRC=$TREE
	OUTBUILD=$BUILD
else
	SRC=$OUT/source
	OUTBUILD=$OUT/build
	rm -rf "$OUT"
	mkdir -p "$OUT"
	rsync -a --exclude='.git' "$TREE/" "$SRC/"
	echo "copied to $SRC"
fi

say "apply the camera patch"
cd "$SRC"
if grep -q 'of_match_table = ov13b10_of_match' drivers/media/i2c/ov13b10.c; then
	echo "the patch is already applied"
else
	cp drivers/media/i2c/ov13b10.c drivers/media/i2c/ov13b10.c.pre-camera-patch
	patch -p1 --forward --batch < "$PATCH" || fail "the patch does not apply"
fi
grep -n 'of_match_table = ov13b10_of_match' drivers/media/i2c/ov13b10.c

say "merge the camera configuration"
mkdir -p "$OUTBUILD"
cp "$BUILD/.config" "$OUTBUILD/.config"
"$SRC/scripts/kconfig/merge_config.sh" -m -O "$OUTBUILD" \
	"$OUTBUILD/.config" "$FRAGMENT" > "$OUT/merge.log" 2>&1 || { tail -20 "$OUT/merge.log"; fail "the configuration merge failed"; }
make -s -C "$SRC" O="$OUTBUILD" ARCH=arm64 CROSS_COMPILE=$CROSS olddefconfig
missing=0
for sym in CONFIG_MEDIA_SUPPORT CONFIG_MEDIA_CAMERA_SUPPORT CONFIG_MEDIA_PLATFORM_SUPPORT \
	   CONFIG_MEDIA_CONTROLLER CONFIG_VIDEO_DEV CONFIG_V4L_PLATFORM_DRIVERS \
	   CONFIG_V4L2_ASYNC CONFIG_V4L2_FWNODE CONFIG_VIDEO_V4L2_SUBDEV_API \
	   CONFIG_VIDEOBUF2_DMA_SG CONFIG_VIDEO_CAMERA_SENSOR \
	   CONFIG_VIDEO_OV13B10 CONFIG_VIDEO_QCOM_CAMSS CONFIG_FUSE_FS; do
	if grep -qx "$sym=y" "$OUTBUILD/.config"; then
		echo "  ok   $sym=y"
	else
		echo "  MISS $sym"; missing=1
	fi
done
[ "$missing" -eq 0 ] || fail "the camera configuration is incomplete"

if [ "$PREPARE_ONLY" -eq 1 ]; then
	say "result"
	echo "CAMERA_KERNEL_PREPARED_NO_BUILD"
	exit 0
fi

say "build the kernel and the device tree"
make -s -C "$SRC" O="$OUTBUILD" ARCH=arm64 CROSS_COMPILE=$CROSS prepare
make -C "$SRC" O="$OUTBUILD" ARCH=arm64 CROSS_COMPILE=$CROSS -j"$JOBS" Image dtbs 2>&1 | tail -15
[ -f "$OUTBUILD/arch/arm64/boot/Image" ] || fail "the kernel image was not produced"
DTB=$(find "$OUTBUILD/arch/arm64/boot/dts/qcom" -name 'sm8250-xiaomi-lmi.dtb' | head -1)
[ -n "$DTB" ] || fail "the board device tree was not produced"
cp "$OUTBUILD/arch/arm64/boot/Image" "$OUT/Image"
cp "$DTB" "$OUT/sm8250-xiaomi-lmi.dtb"
cp "$OUTBUILD/.config" "$OUT/config"

say "check the produced device tree"
dtc -I dtb -O dts "$OUT/sm8250-xiaomi-lmi.dtb" > "$OUT/board.roundtrip.dts" 2>/dev/null
missing=0
for needle in 'ovti,ov13b10' 'camera@10' 'data-lanes' 'link-frequencies' 'reset-gpios' \
	      'avdd-supply' 'dovdd-supply' 'dvdd-supply' 'remote-endpoint'; do
	if grep -q -- "$needle" "$OUT/board.roundtrip.dts"; then
		echo "  ok   $needle"
	else
		echo "  MISS $needle"; missing=1
	fi
done
[ "$missing" -eq 0 ] || fail "the produced device tree does not carry the rear sensor"
echo "kernel: $(stat -c %s "$OUT/Image") bytes"
echo "device tree: $(stat -c %s "$OUT/sm8250-xiaomi-lmi.dtb") bytes"
sha256sum "$OUT/Image" "$OUT/sm8250-xiaomi-lmi.dtb" | tee "$OUT/SHA256SUMS"

say "result"
echo "CAMERA_KERNEL_BUILT"
echo "artifacts in $OUT"
cat <<'NEXT'
Install the two artifacts as the permanent system5 entry, keep the Mobian 4.19
entry as the fallback, and check after the boot:

  /sys/bus/i2c/devices/21-0010/driver      must exist
  /dev/v4l-subdev*                          must appear
  dmesg                                    must carry the sensor identification
  /usr/local/lib/lmi-camera/native-pipewire-v4l2-source /dev/video0
                                           must print V4L2_SOURCE_READY
NEXT
