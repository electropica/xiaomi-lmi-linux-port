#!/bin/bash
# Build the Linux 7 community kernel with the PM8150B charger candidate.
#
# The kernel of the permanent boot is built from the community tree, not from
# the pinned tree of the observer kit. This script takes that tree, applies
# the charger patch, merges the charger configuration, builds the kernel and
# its device tree, and checks the result.
#
# The default tree is the one that produced the running handset kernel, that
# is the tree that carries the Type-C detach fix of the 2026-11-01 commit
# 1553aee together with the camera, GNSS, audio and MHI work. Nothing of that
# work is touched: the charger candidate only changes
# drivers/power/supply/qcom_pm8150b_charger.c and adds one configuration
# symbol.
#
# It never touches the input tree unless --in-place is given: by default the
# tree is copied to a scratch directory, so the operator can run it again and
# compare two results.
#
# Usage:
#   bash tools/build-community-charger-kernel.sh [--tree DIR] [--build DIR]
#         [--out DIR] [--jobs N] [--prepare-only] [--in-place]
#
# Defaults:
#   --tree  the community tree that produced the running handset kernel
#   --build the configuration directory of that same tree
#   --out   <repo>/output/minimax-kernel7-feasibility/community-charger-kernel
set -euo pipefail

REPO=/home/linuxagent/xiaomi-lmi-linux-port
EXP=$REPO/kernel/experimental/linux7
PATCH=$EXP/patches/0005-lmi-pm8150b-charger-input-current.patch
FRAGMENT=$EXP/configs/charger-smb5.fragment
DRIVER=drivers/power/supply/qcom_pm8150b_charger.c
DTS=sm8250-xiaomi-lmi.dts
DTS_REL=arch/arm64/boot/dts/qcom/$DTS
CROSS=aarch64-linux-gnu-

TREE=/home/linuxagent/xiaomi-lmi-linux-port/output/minimax-kernel7-feasibility/community-typec-irq-thread-20261101/source
BUILD=/home/linuxagent/xiaomi-lmi-linux-port/output/minimax-kernel7-feasibility/community-typec-irq-thread-20261101/build
OUT=$REPO/output/minimax-kernel7-feasibility/community-charger-kernel
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
[ -f "$TREE/$DRIVER" ] || fail "missing charger driver: $TREE/$DRIVER"
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

say "apply the charger patch"
cd "$SRC"
if grep -q 'smb5_get_typec_input_current' "$DRIVER"; then
	echo "the patch is already applied"
else
	cp "$DRIVER" "$DRIVER.pre-charger-patch"
	patch -p1 --forward --batch < "$PATCH" || fail "the patch does not apply"
fi
grep -n 'smb5_get_typec_input_current' "$DRIVER" | head -2

say "merge the charger configuration"
mkdir -p "$OUTBUILD"
cp "$BUILD/.config" "$OUTBUILD/.config"
"$SRC/scripts/kconfig/merge_config.sh" -m -O "$OUTBUILD" \
	"$OUTBUILD/.config" "$FRAGMENT" > "$OUT/merge.log" 2>&1 || { tail -20 "$OUT/merge.log"; fail "the configuration merge failed"; }
make -s -C "$SRC" O="$OUTBUILD" ARCH=arm64 CROSS_COMPILE=$CROSS olddefconfig
missing=0
for sym in CONFIG_CHARGER_QCOM_SMB5 CONFIG_BATTERY_QCOM_FG CONFIG_MFD_SPMI_PMIC \
	   CONFIG_IIO; do
	if grep -qx "$sym=y" "$OUTBUILD/.config"; then
		echo "  ok   $sym=y"
	else
		echo "  MISS $sym"; missing=1
	fi
done
[ "$missing" -eq 0 ] || fail "the charger configuration is incomplete"

if [ "$PREPARE_ONLY" -eq 1 ]; then
	say "result"
	echo "CHARGER_KERNEL_PREPARED_NO_BUILD"
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
dtc -I dtb -O dts "$OUT/sm8250-xiaomi-lmi.dtb" > "$OUT/board.roundtrip.dts" 2>/dev/null
missing=0
for needle in 'qcom,pm8150b-charger' 'monitored-battery' 'usb-plugin' 'usbin_icl'; do
	if grep -q -- "$needle" "$OUT/board.roundtrip.dts"; then
		echo "  ok   $needle"
	else
		echo "  MISS $needle"; missing=1
	fi
done
[ "$missing" -eq 0 ] || fail "the produced device tree does not carry the charger node"
echo "kernel: $(stat -c %s "$OUT/Image") bytes"
echo "device tree: $(stat -c %s "$OUT/sm8250-xiaomi-lmi.dtb") bytes"
sha256sum "$OUT/Image" "$OUT/sm8250-xiaomi-lmi.dtb" | tee "$OUT/SHA256SUMS"

say "result"
echo "CHARGER_KERNEL_BUILT"
echo "artifacts in $OUT"
cat <<'NEXT'
Install the two artifacts as the permanent system5 entry, keep the Mobian 4.19
entry as the fallback, and check after the boot:

  dmesg | grep pm8150b-charger   must carry "input current limit set to"
  ls /sys/class/power_supply     must carry pm8150b-charger
  cat /sys/class/power_supply/pm8150b-charger/current_max
                                 must carry 1500000 (1.5 A, the Rp of the source)
  /sys/class/power_supply/battery/status
                                 must follow the charger state, not the sign of
                                 the current
  the Type-C detach detection must still work: unplugging the cable has to
  drop the USB link and the AC state, as the 2026-11-01 fix established
NEXT
