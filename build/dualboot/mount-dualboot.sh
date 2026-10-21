mount_subpartitions() {
	# This boot MUST NOT discover, mount or resize Android userdata.
	[ -n "$PMOS_ROOT" ] && [ -n "$PMOS_BOOT" ] && return
	local partition=/dev/disk/by-partlabel/mobian resolved size attempt
	for attempt in $(seq 1 100); do
		lmi_populate_block_devs 2>/dev/null || true
		[ -b "$partition" ] && break
		sleep 0.1
	done
	if [ ! -b "$partition" ]; then
		echo 'DUALBOOT STOP: dedicated mobian partition absent; userdata untouched.'
		while sleep 60; do :; done
	fi
	resolved=$(readlink -f "$partition")
	size=$(cat "/sys/class/block/${resolved##*/}/size")
	if [ "$size" != 33554432 ]; then
		echo 'DUALBOOT STOP: expected a dedicated 16 GiB partition.'
		while sleep 60; do :; done
	fi
	SUBPARTITION_DEV="$partition"
	modprobe loop 2>/dev/null || true
	SUBPARTITION_LOOP=$(losetup --show -Pf --sector-size 4096 --direct-io=on "$partition")
	if [ -z "$SUBPARTITION_LOOP" ]; then
		echo 'DUALBOOT STOP: loop setup failed.'
		while sleep 60; do :; done
	fi
	for attempt in $(seq 1 100); do
		lmi_populate_block_devs 2>/dev/null || true
		[ -b "${SUBPARTITION_LOOP}p2" ] && break
		sleep 0.1
	done
	if [ "$(blkid -s UUID -o value "${SUBPARTITION_LOOP}p1")" != "$boot_uuid" ] ||
	   [ "$(blkid -s UUID -o value "${SUBPARTITION_LOOP}p2")" != "$root_uuid" ]; then
		echo 'DUALBOOT STOP: dedicated image UUID mismatch; no resize or mount.'
		while sleep 60; do :; done
	fi
	PMOS_BOOT="${SUBPARTITION_LOOP}p1"
	PMOS_ROOT="${SUBPARTITION_LOOP}p2"
}
