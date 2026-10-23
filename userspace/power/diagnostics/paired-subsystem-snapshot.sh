#!/bin/sh
# One snapshot on Mobian or rooted LineageOS. No radio/IRQ/GPIO/power writes.
set -u
printf 'IDENTITY\n'
uname -r
cat /proc/uptime
printf '\nDEBUGFS_MOUNTS\n'
awk '$3 == "debugfs" {print $2, $4}' /proc/mounts
printf '\nUSB_ONLINE\n'
for p in /sys/class/power_supply/*/online; do
 [ -r "$p" ] && { printf '%s=' "$p"; cat "$p"; }
done
printf '\nSUBSYSTEMS\n'
for d in /sys/bus/msm_subsys/devices/*; do
 [ -d "$d" ] || continue
 printf '%s ' "$d"
 for n in name state; do [ -r "$d/$n" ] && { printf '%s=' "$n"; tr '\n' ' ' < "$d/$n"; printf ' '; }; done
 printf '\n'
done
printf '\nESOC_IDENTITY\n'
for p in /sys/bus/esoc/devices/*/esoc_name /sys/bus/esoc/devices/*/esoc_link; do
 [ -r "$p" ] && { printf '%s=' "$p"; cat "$p"; }
done
printf '\nGPIO_HANDSHAKE\n'
if [ -r /sys/kernel/debug/gpio ]; then
 # The retained lmi DT maps modem handshakes to TLMM1,3,56,57.
 # Keep complete TLMM block so local numbering and levels remain interpretable.
 awk '/^gpiochip/ {wanted=($0 ~ /f000000/)} wanted {print}' /sys/kernel/debug/gpio
else printf 'UNAVAILABLE: gpio debugfs not readable\n'; fi
printf '\nMASTER_STATS\n'
for p in /sys/kernel/debug/rpm_master_stats /sys/kernel/debug/rpmh_stats/master_stats /sys/power/rpmh/master_stats; do
 if [ -r "$p" ]; then printf '%s\n' "$p"; cat "$p"; fi
done
printf '\nNPU_POWER\n'
if [ -r /sys/devices/virtual/npu/msm_npu/pwr ]; then cat /sys/devices/virtual/npu/msm_npu/pwr; else printf 'UNAVAILABLE\n'; fi
printf '\nEND\n'
