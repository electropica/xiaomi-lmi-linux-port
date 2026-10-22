#!/bin/sh
# Read-only UFS suspend-policy snapshot, v2.
#
# Emits a line protocol on stdout. Reads only sysfs files; no write, no
# open-for-write, no echo >, no reboot, no root command, no periodic
# collection. One shot, print once.
#
#   INFO   <key> <value>
#   ROOT   <path> PRESENT|ABSENT
#   LIST   <path> OK <name1> <name2> ...      (listing SUCCEEDED)
#   LIST   <path> FAILED <message>            (listing did NOT succeed)
#   ATTR   <path> OK <value>
#   ATTR   <path> DENIED <errno> <message>    (explicit permission failure)
#   ATTR   <path> ABSENT                      (enumerated absent, verified)
#   ATTR   <path> UNKNOWN <message>           (could not be classified)
#   ATTR   <path> ERROR <errno> <message>
#
# Classification rules (fixed after the 2026-10-22 review):
#   * a DIRECTORY LISTING FAILURE never becomes an absence: it is UNKNOWN.
#   * an explicit permission failure is DENIED, whatever the listing says.
#   * ABSENT requires a successful listing that does not contain the name.
#   * a name that the listing contains but that cannot be read is reported as
#     DENIED (or UNKNOWN), never as ABSENT.
# The reader classifies; this script only reports what actually happened.

ROOTS="/sys/bus/platform/devices/1d84000.ufshc
/sys/bus/platform/devices/1d84000.ufshc/host0
/sys/bus/platform/devices/1d84000.ufshc/host0/target0:0:0
/sys/class/scsi_host/host0/device
/sys/class/scsi_host/host0/device/target0:0:0
/sys/class/scsi_host/host1/device"

# leaf attributes read at every root
POLICY="clkscale_enable clk_scaling_enable clkgate_enable clkgate_delay_ms
rpm_lvl spm_lvl auto_hibern8 auto_bkops
rpm_target_link_state rpm_target_dev_state
spm_target_link_state spm_target_dev_state
max_bus_bw"

# directories whose content is enumerated
LISTDIRS="attributes qcom power flags device_descriptor health_descriptor
geometry_descriptor interconnect_descriptor power_descriptor string_descriptors"

read_attr() {
	_p="$1"
	_out=$(cat "$_p" 2>&1)
	_rc=$?
	if [ $_rc -eq 0 ]; then
		echo "ATTR $_p OK $(printf '%s' "$_out" | tr '\n' ' ')"
		return 0
	fi
	case "$_out" in
	*"Permission denied"*|*"Operation not permitted"*)
		echo "ATTR $_p DENIED $_rc $(printf '%s' "$_out" | tr '\n' ' ')" ;;
	*)
		echo "ATTR $_p UNKNOWN $_rc $(printf '%s' "$_out" | tr '\n' ' ')" ;;
	esac
}

echo "INFO collector ufs-suspend-policy-readonly-v2"
echo "INFO collected_at $(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo unknown)"
echo "INFO kernel $(uname -r 2>/dev/null || echo unknown)"
echo "INFO uid $(id -u 2>/dev/null) gid $(id -g 2>/dev/null)"
echo "INFO id $(id 2>/dev/null)"
echo "INFO selinux_context $(cat /proc/self/attr/current 2>/dev/null || echo unknown)"
if command -v getprop >/dev/null 2>&1; then
	echo "INFO ro.lineage.version $(getprop ro.lineage.version 2>/dev/null)"
	echo "INFO ro.product.device $(getprop ro.product.device 2>/dev/null)"
	echo "INFO ro.product.name $(getprop ro.product.name 2>/dev/null)"
	echo "INFO ro.build.fingerprint $(getprop ro.build.fingerprint 2>/dev/null)"
	echo "INFO ro.build.version.release $(getprop ro.build.version.release 2>/dev/null)"
	echo "INFO ro.boot.bootdevice $(getprop ro.boot.bootdevice 2>/dev/null)"
	echo "INFO ro.hardware $(getprop ro.hardware 2>/dev/null)"
fi
echo "INFO usb_online $(cat /sys/class/power_supply/usb/online 2>/dev/null || echo unreadable)"

for _r in $ROOTS; do
	if [ -d "$_r" ]; then
		echo "ROOT $_r PRESENT"
	else
		echo "ROOT $_r ABSENT"
	fi
done

# directory listings: success and failure are reported separately
for _r in $ROOTS; do
	[ -d "$_r" ] || continue
	_names=$(ls -1 "$_r" 2>&1)
	if [ $? -eq 0 ]; then
		echo "LIST $_r OK $(printf '%s' "$_names" | tr '\n' ' ')"
	else
		echo "LIST $_r FAILED $(printf '%s' "$_names" | tr '\n' ' ')"
	fi
	for _d in $LISTDIRS; do
		[ -d "$_r/$_d" ] || continue
		_s=$(ls -1 "$_r/$_d" 2>&1)
		if [ $? -eq 0 ]; then
			echo "LIST $_r/$_d OK $(printf '%s' "$_s" | tr '\n' ' ')"
		else
			echo "LIST $_r/$_d FAILED $(printf '%s' "$_s" | tr '\n' ' ')"
		fi
	done
done

# attribute reads
for _r in $ROOTS; do
	[ -d "$_r" ] || continue
	for _a in $POLICY; do
		read_attr "$_r/$_a"
	done
	for _a in runtime_status control runtime_active_time runtime_suspended_time \
		  autosuspend_delay_ms; do
		read_attr "$_r/power/$_a"
	done
	for _a in psa_state current_power_mode bkops_status active_icc_level; do
		read_attr "$_r/attributes/$_a"
	done
	for _a in clk_status power_mode bus_speed_mode err_count err_state; do
		read_attr "$_r/qcom/$_a"
	done
done

echo "INFO end ufs-suspend-policy-readonly-v2"
