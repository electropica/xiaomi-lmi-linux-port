#!/system/bin/sh
# Read-only preflight. No mount, partition, radio or power-policy writes.
set -eu

[ "$(id -u)" = 0 ] || { echo 'ERROR: recovery root required' >&2; exit 1; }
case "$(getprop ro.product.device) $(getprop ro.build.product)" in
  *lmi*) ;;
  *) echo 'ERROR: lmi not identified' >&2; exit 1 ;;
esac
pidof recovery >/dev/null 2>&1 || {
  echo 'ERROR: recovery process is not running' >&2
  exit 1
}

emit() {
  printf '%s\t' "$1"
  od -An -v -tx1 | tr -d ' \n'
  printf '\n'
}
read_file() {
  if [ -r "$2" ]; then
    cat "$2" | emit "$1"
  else
    printf 'UNAVAILABLE' | emit "$1"
  fi
}

for prop in ro.bootmode ro.product.device ro.build.version.release ro.lineage.version; do
  getprop "$prop" | emit "property:$prop"
done
read_file kernel /proc/version
read_file boot_id /proc/sys/kernel/random/boot_id
read_file uptime /proc/uptime
read_file power_state /sys/power/state
read_file mem_sleep /sys/power/mem_sleep
read_file sleep_disabled /sys/module/lpm_levels/parameters/sleep_disabled
read_file rtc_name /sys/class/rtc/rtc0/name
read_file rtc_epoch /sys/class/rtc/rtc0/since_epoch
read_file wakealarm /sys/class/rtc/rtc0/wakealarm
read_file last_sleep /sys/kernel/wakeup_reasons/last_suspend_time
read_file last_wake /sys/kernel/wakeup_reasons/last_resume_reason
read_file wake_lock /sys/power/wake_lock
for supply in battery bms usb; do
  for field in online status capacity real_capacity charge_counter charge_counter_shadow charge_now_raw charge_full charge_full_design current_now current_avg voltage_now temp; do
    read_file "supply:$supply:$field" "/sys/class/power_supply/$supply/$field"
  done
done
for node in soc:qcom,npu-npu-llcc-bw soc:qcom,npu-llcc-ddr-bw soc:qcom,npudsp-npu-ddr-bw; do
  for field in governor min_freq max_freq cur_freq available_governors; do
    read_file "npu:$node:$field" "/sys/class/devfreq/$node/$field"
  done
done
for node in /sys/class/rfkill/rfkill*; do
  [ -d "$node" ] || continue
  for field in name type state soft hard; do
    read_file "radio:$(basename "$node"):$field" "$node/$field"
  done
done
for node in /sys/class/backlight/*; do
  [ -d "$node" ] || continue
  for field in brightness actual_brightness bl_power; do
    read_file "backlight:$(basename "$node"):$field" "$node/$field"
  done
done
