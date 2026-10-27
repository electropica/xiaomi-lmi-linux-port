#!/bin/bash
# Operator-run builder for the linux7 kit.
#
# Produces the four components the project's own outer packer consumes:
#   linux7/kernel   -> the ARM64 Image
#   linux7/dtb      -> the board DTB
#   linux7/initrd   -> the initramfs cpio.gz
#   linux7/cmdline  -> the extra command line (single trailing NUL)
#
# It never contacts the handset, never writes to the pinned kernel tree and
# never overwrites an existing output directory.
#
# Usage:
#   bash build/build-linux7-kit.sh --variant display1
#
# The heavy steps (kernel Image) are operator-run by project policy; this
# script is the complete, reproducible recipe for them.
set -euo pipefail

REPO=/home/linuxagent/xiaomi-lmi-linux-port
EXP=$REPO/kernel/experimental/linux7
FEAS=$REPO/output/minimax-kernel7-feasibility
TREE=$FEAS/linux-v7.2.12-clean
TREE_REV=cc9de5d4b5ab6459f5774946aa3195ad51236fa8
CROSS=aarch64-linux-gnu-
JOBS=$(nproc)

variant=""
while [ $# -gt 0 ]; do
	case "$1" in
	--variant) variant="$2"; shift 2 ;;
	*) echo "unknown argument: $1" >&2; exit 2 ;;
	esac
done
[ -n "$variant" ] || { echo "usage: $0 --variant <name>" >&2; exit 2; }

WORK=$FEAS/linux7-$variant
SRC=$WORK/source
BUILD=$WORK/build
KIT=$WORK/kit
DTS_NAME=sm8250-xiaomi-lmi-observer.dts
DTS_TREE_REL=arch/arm64/boot/dts/qcom/$DTS_NAME
DTB_NAME=sm8250-xiaomi-lmi-$variant.dtb

# Accepted observer initramfs tree: busybox (musl aarch64) plus the applet
# symlinks. The display1 variant reuses it and only adds the GPU firmware.
OBSERVER_INITRAMFS=$FEAS/linux7-kit-out/build/initramfs
GPU_FIRMWARE=$REPO/userspace/gpu/files/firmware/a650

say() { printf '\n== %s ==\n' "$*"; }

say "preconditions"
[ -d "$TREE" ] || { echo "missing pinned tree: $TREE" >&2; exit 2; }
rev=$(git -C "$TREE" rev-parse HEAD 2>/dev/null || echo unknown)
[ "$rev" = "$TREE_REV" ] || { echo "tree revision drift: $rev != $TREE_REV" >&2; exit 2; }
echo "tree revision $rev"
[ -d "$OBSERVER_INITRAMFS" ] || { echo "missing accepted observer initramfs" >&2; exit 2; }
[ -d "$GPU_FIRMWARE" ] || { echo "missing GPU firmware: $GPU_FIRMWARE" >&2; exit 2; }
for p in "$EXP/patches/0001-probe-runtime-markers.patch" \
         "$EXP/patches/0002-lmi-dsi-display.patch" \
         "$EXP/patches/0003-add-msm667uu01-panel.patch" \
         "$EXP/configs/observer-tested.config" \
         "$EXP/configs/display1.fragment" \
         "$EXP/initramfs/init"; do
	[ -f "$p" ] || { echo "missing input: $p" >&2; exit 2; }
done
[ ! -e "$WORK" ] || { echo "output exists, refusing to overwrite: $WORK" >&2; exit 2; }

say "copy the pinned tree"
mkdir -p "$WORK" "$BUILD" "$KIT"
rsync -a --exclude='.git' "$TREE/" "$SRC/"
echo "copied to $SRC"

say "place the board DTS and apply the patches"
cp "$EXP/dts/$DTS_NAME" "$SRC/$DTS_TREE_REL"
cd "$SRC"
for p in "$EXP"/patches/000*.patch; do
	echo "-- applying $(basename "$p")"
	patch -p1 --forward --batch < "$p"
done

say "merge the kernel configuration"
cp "$EXP/configs/observer-tested.config" "$BUILD/.config"
"$SRC/scripts/kconfig/merge_config.sh" -m -O "$BUILD" \
	"$BUILD/.config" "$EXP/configs/display1.fragment"
make -s -C "$SRC" O="$BUILD" ARCH=arm64 CROSS_COMPILE=$CROSS olddefconfig

say "verify the required configuration symbols"
missing=0
for sym in CONFIG_DRM CONFIG_DRM_MSM CONFIG_DRM_MSM_KMS CONFIG_DRM_MSM_DSI \
	   CONFIG_DRM_MSM_DSI_7NM_PHY CONFIG_DRM_PANEL_SAMSUNG_AMS667UU01; do
	if grep -qx "$sym=y" "$BUILD/.config"; then
		echo "  ok   $sym=y"
	else
		echo "  MISS $sym"; missing=1
	fi
done
[ "$missing" -eq 0 ] || { echo "configuration incomplete" >&2; exit 3; }

say "build the kernel Image (heavy, operator-run)"
make -C "$SRC" O="$BUILD" ARCH=arm64 CROSS_COMPILE=$CROSS -j"$JOBS" Image

say "build the board DTB"
cpp -nostdinc -I "$SRC/include" -I "$BUILD/include" -undef -D__DTS__ \
	-x assembler-with-cpp "$SRC/$DTS_TREE_REL" > "$WORK/board.dts.tmp"
dtc -I dts -O dtb -o "$KIT/$DTB_NAME" "$WORK/board.dts.tmp" 2> "$WORK/dtc.log"
rm -f "$WORK/board.dts.tmp"
echo "dtc warnings: $(wc -l < "$WORK/dtc.log")"

say "assemble the initramfs"
rm -rf "$BUILD/initramfs"
cp -a "$OBSERVER_INITRAMFS" "$BUILD/initramfs"
install -m 0755 "$EXP/initramfs/init" "$BUILD/initramfs/init"
mkdir -p "$BUILD/initramfs/lib/firmware/qcom"
for f in a650_sqe.fw a650_gmu.bin a650_zap.mdt a650_zap.b00 a650_zap.b01 a650_zap.b02; do
	[ -f "$GPU_FIRMWARE/$f" ] && cp "$GPU_FIRMWARE/$f" "$BUILD/initramfs/lib/firmware/qcom/"
done
ls -la "$BUILD/initramfs/lib/firmware/qcom"
( cd "$BUILD/initramfs" && find . -print0 | cpio --null -o -H newc 2> "$WORK/cpio.log" | gzip -9 ) > "$KIT/initramfs-linux7.cpio.gz"

say "write the command line"
printf 'console=ttyMSM,115200n8 loglevel=8 ignore_loglevel printk.devkmsg=on' > "$WORK/cmdline.txt"
printf '\0' >> "$WORK/cmdline.txt"
tr -d '\n' < "$WORK/cmdline.txt" > "$KIT/linux7-cmdline.bin"

say "collect the kit"
cp "$BUILD/arch/arm64/boot/Image" "$KIT/Image"
cp "$KIT/$DTB_NAME" "$KIT/sm8250-xiaomi-lmi-minimal.dtb"

say "manifest"
{
	echo "linux7 $variant kit manifest"
	echo "generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
	echo "kernel source: $TREE"
	echo "  revision: $TREE_REV"
	echo "  patches: $(cd "$EXP/patches" && ls 000*.patch | tr '\n' ' ')"
	echo "  config: configs/observer-tested.config + configs/display1.fragment"
	printf '%-22s %-18s %10s  %s\n' component bundle bytes sha256
	for entry in "Image linux7/kernel" "$DTB_NAME linux7/dtb" \
		     "initramfs-linux7.cpio.gz linux7/initrd" \
		     "linux7-cmdline.bin linux7/cmdline"; do
		set -- $entry
		f=$1; name=$2
		printf '%-22s %-18s %10s  %s\n' "$f" "$name" \
			"$(stat -c %s "$KIT/$f")" \
			"$(sha256sum "$KIT/$f" | cut -d' ' -f1)"
	done
	echo
	echo "loader limits: kernel <= 67108864, dtb <= 2097152, initrd <= 33554432, cmdline < 4096"
} > "$KIT/MANIFEST.txt"
cat "$KIT/MANIFEST.txt"

say "size limits"
fail=0
check() { # file limit label
	sz=$(stat -c %s "$1")
	if [ "$sz" -gt "$2" ]; then
		echo "  OVER LIMIT $3: $sz > $2"; fail=1
	else
		echo "  ok  $3: $sz <= $2"
	fi
}
check "$KIT/Image" 67108864 "kernel"
check "$KIT/$DTB_NAME" 2097152 "dtb"
check "$KIT/initramfs-linux7.cpio.gz" 33554432 "initrd"
check "$KIT/linux7-cmdline.bin" 4096 "cmdline"
[ "$fail" -eq 0 ] || { echo "size limits exceeded" >&2; exit 3; }

say "done: $KIT"
echo "Next: package the outer menu image with the project's own recipe"
echo "  build/boot-menu/external-mobian (see the README of that recipe)"
