#!/bin/bash
# Host check of the lmi PM8150B charger candidate.
#
# It checks, on the host and without building anything, that:
#
#   - the patch applies to the community tree that produced the running
#     handset kernel (the tree that carries the Type-C detach fix of the
#     2026-11-01 commit 1553aee, with the camera, GNSS, audio and MHI work);
#   - the configuration fragment resolves to CONFIG_CHARGER_QCOM_SMB5=y;
#   - the corrected driver keeps the properties the port depends on: it
#     leaves the Type-C block alone, it keeps the re-charge threshold driven
#     by the battery voltage, it does not write the float voltage with the
#     wrong scale, and it asks for the interrupt name of this board.
#
# It deliberately does NOT compile: the build is the operator's step.
#
# Usage:
#   bash tools/check-charger-patch.sh [--tree DIR] [--build DIR]
#
# Defaults:
#   --tree  the community tree that produced the running handset kernel
#   --build the configuration directory of that same tree
set -euo pipefail

REPO=/home/linuxagent/xiaomi-lmi-linux-port
EXP=$REPO/kernel/experimental/linux7
PATCH=$EXP/patches/0005-lmi-pm8150b-charger-input-current.patch
FRAGMENT=$EXP/configs/charger-smb5.fragment
DRIVER=drivers/power/supply/qcom_pm8150b_charger.c

TREE=/home/linuxagent/xiaomi-lmi-linux-port/output/minimax-kernel7-feasibility/community-typec-irq-thread-20261101/source
BUILD=/home/linuxagent/xiaomi-lmi-linux-port/output/minimax-kernel7-feasibility/community-typec-irq-thread-20261101/build
WORK=/tmp/lmi-charger-check

while [ $# -gt 0 ]; do
	case "$1" in
	--tree) TREE=$2; shift 2 ;;
	--build) BUILD=$2; shift 2 ;;
	*) echo "unknown argument: $1" >&2; exit 2 ;;
	esac
done

say() { printf '\n== %s ==\n' "$*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

say "preconditions"
[ -d "$TREE" ] || fail "missing community tree: $TREE"
[ -f "$BUILD/.config" ] || fail "missing configuration: $BUILD/.config"
[ -f "$PATCH" ] || fail "missing patch: $PATCH"
[ -f "$FRAGMENT" ] || fail "missing fragment: $FRAGMENT"
[ -f "$TREE/$DRIVER" ] || fail "missing driver: $TREE/$DRIVER"
echo "tree: $TREE"
echo "configuration: $BUILD/.config"

say "the patch applies"
rm -rf "$WORK"
mkdir -p "$WORK"
cp "$TREE/$DRIVER" "$WORK/driver.orig"
mkdir -p "$WORK/tree/$(dirname "$DRIVER")"
cp "$TREE/$DRIVER" "$WORK/tree/$DRIVER"
( cd "$WORK/tree" && patch -p1 --forward < "$PATCH" ) || fail "the patch does not apply"

say "the configuration resolves"
mkdir -p "$WORK/build"
cp "$BUILD/.config" "$WORK/build/.config"
"$TREE/scripts/kconfig/merge_config.sh" -m -O "$WORK/build" \
	"$WORK/build/.config" "$FRAGMENT" > "$WORK/merge.log" 2>&1 \
	|| { tail -20 "$WORK/merge.log"; fail "the configuration merge failed"; }
make -s -C "$TREE" O="$WORK/build" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- \
	olddefconfig > "$WORK/olddefconfig.log" 2>&1 \
	|| { tail -20 "$WORK/olddefconfig.log"; fail "olddefconfig failed"; }
grep -qx 'CONFIG_CHARGER_QCOM_SMB5=y' "$WORK/build/.config" \
	|| fail "CONFIG_CHARGER_QCOM_SMB5 does not resolve to =y"
echo "  ok   CONFIG_CHARGER_QCOM_SMB5=y"
for sym in CONFIG_BATTERY_QCOM_FG CONFIG_MFD_SPMI_PMIC CONFIG_IIO; do
	grep -qx "$sym=y" "$WORK/build/.config" || fail "$sym is not =y"
	echo "  ok   $sym=y"
done

say "the corrected driver keeps the expected behaviour"
F=$WORK/tree/$DRIVER
check_absent() {
	if grep -q "$1" "$F"; then
		fail "$2"
	fi
	echo "  ok   absent: $2"
}
check_present() {
	grep -q "$1" "$F" || fail "$2"
	echo "  ok   present: $2"
}
# The float voltage is not programmed any more: the upstream formula used the
# 7.5 mV scale of another PMIC and would have commanded 4.90 V.
check_absent '3487500' 'no 7.5 mV float scale'
check_absent 'chip->base + FLOAT_VOLTAGE_CFG' 'no float voltage write'
# The Type-C block belongs to the qcom,pm8150b-typec driver of this board.
for reg in TYPE_C_MODE_CFG TYPEC_TYPE_C_VCONN_CONTROL DEBUG_ACCESS_SRC_CFG \
	   TYPE_C_EXIT_STATE_CFG TYPE_C_CFG TYPE_C_DEBUG_ACCESS_SINK OTG_CFG \
	   USBIN_OPTIONS_1_CFG USBIN_ICL_OPTIONS; do
	check_absent "\.addr = $reg," "no write of $reg in the init sequence"
done
# The re-charge stays driven by the battery voltage: the fuel gauge of this
# board never publishes its SOC to the charger.
check_present '\.val = AUTO_RECHG_BIT }' 're-charge driven by the battery voltage'
# The interrupt of this board is named "usb-plugin".
check_present '"usb-plugin"' 'the usb-plugin interrupt of the board'
# The input current limit follows the source capability on CC.
check_present 'smb5_get_typec_input_current' 'the input limit follows the Rp'
check_present 'USB_ICL_MAX_UA' 'the input limit is capped at the board value'
# The input is never suspended on a collapse: the handset is only reachable
# over USB. The bit stays in the mask, so it is cleared, but it must not be
# in the value that is written.
if grep -A 6 'USBIN_AICL_OPTIONS_CFG,' "$F" | sed -n '/\.val/,/},/p' \
		| grep -q 'SUSPEND_ON_COLLAPSE_USBIN_BIT'; then
	fail "the input is suspended on a collapse"
fi
echo "  ok   present: the input is not suspended on a collapse"

say "result"
echo "CHARGER_CANDIDATE_HOST_CHECK_OK"
echo "(nothing was compiled and nothing was flashed)"
