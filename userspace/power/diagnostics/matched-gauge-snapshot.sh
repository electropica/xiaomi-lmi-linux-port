#!/bin/sh
# One-shot, explicit sysfs reads only. Not armed, installed or executed remotely.
# Works with Android toybox sh and Mobian sh. No explicit writes by this script.
# These getters perform gauge accesses; use while already awake, not periodically.
set -u
printf 'FORMAT=lmi-matched-gauge-v1\n'
printf 'KERNEL='
uname -r
printf 'UPTIME_START='
cat /proc/uptime
for supply in bms battery usb dc pc_port; do
    base="/sys/class/power_supply/$supply"
    if [ ! -d "$base" ]; then
        printf 'SUPPLY_ABSENT=%s\n' "$supply"
        continue
    fi
    case "$supply" in
        bms) fields='type status capacity charge_counter charge_counter_shadow charge_now_raw charge_full charge_full_design current_now current_avg voltage_now temp' ;;
        battery) fields='type status capacity charge_counter charge_full charge_full_design current_now voltage_now temp' ;;
        *) fields='type online present' ;;
    esac
    for field in $fields; do
        path="$base/$field"
        if [ ! -e "$path" ]; then
            printf 'ABSENT %s\n' "$path"
        elif value=$(cat "$path" 2>/dev/null); then
            printf 'VALUE %s=%s\n' "$path" "$value"
        else
            code=$?
            printf 'READ_ERROR %s rc=%s\n' "$path" "$code"
        fi
    done
done
printf 'UPTIME_END='
cat /proc/uptime
# Endpoints are sequential, not simultaneous. Current signs are retained raw.
# No uevent: that would invoke extra getters, including uncontrolled properties.
# No charge_done, debugfs mount, wake lock, polling or suspend request.
