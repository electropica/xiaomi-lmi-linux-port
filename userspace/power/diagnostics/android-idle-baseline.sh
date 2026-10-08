#!/system/bin/sh
# Finite one-shot baseline. No periodic logger remains after unplug.
set -eu
base=${1:?trial directory required}
plane=${2:?original airplane state required}
wifi=${3:?original Wi-Fi state required}
bluetooth=${4:?original Bluetooth state required}
case "$base" in /data/local/tmp/lmi-android-idle-*) ;; *) exit 2 ;; esac
suffix=${base#/data/local/tmp/lmi-android-idle-}
case "$suffix" in ''|*[!A-Za-z0-9_-]*) exit 2 ;; esac
case "$plane:$wifi:$bluetooth" in [01]:[01]:[01]) ;; *) exit 2 ;; esac
saved=0
restore_original() {
 if [ "$saved" = 0 ]; then
  if [ "$plane" = 1 ]; then cmd connectivity airplane-mode enable; else cmd connectivity airplane-mode disable; fi
  if [ "$wifi" = 1 ]; then cmd wifi set-wifi-enabled enabled; else cmd wifi set-wifi-enabled disabled; fi
  if [ "$bluetooth" = 1 ]; then cmd bluetooth_manager enable; else cmd bluetooth_manager disable; fi
  echo BASELINE_FAILED_RADIO_RESTORATION_REQUESTED_CHECK_ON_RETURN
 fi
}
trap restore_original EXIT
test ! -e "$base/before.txt"
offline() {
 grep -q 'AC powered: false' "$1" && grep -q 'USB powered: false' "$1" &&
 grep -q 'Wireless powered: false' "$1" && grep -q 'Dock powered: false' "$1" &&
 grep -q 'status: 3' "$1"
}
tries=0
while :; do
 dumpsys battery > "$base/waiting.txt"
 if offline "$base/waiting.txt"; then break; fi
 tries=$((tries+1))
 test "$tries" -lt 180 || { echo NO_UNPLUG_WITHIN_15_MINUTES; exit 1; }
 sleep 5
done
sleep 10
dumpsys battery > "$base/battery.tmp"
offline "$base/battery.tmp" || { echo RECONNECTED_TOO_EARLY; exit 1; }
{
 echo BOOT_ID; cat /proc/sys/kernel/random/boot_id
 echo BOOT_UPTIME; cat /proc/uptime
 echo DEVICE_CLOCK; date -Iseconds
 echo BATTERY; cat "$base/battery.tmp"
 echo RADIO
 settings get global airplane_mode_on
 settings get global wifi_on
 settings get global bluetooth_on
} > "$base/before.tmp"
test "$(sed -n '/^RADIO$/{n;p;}' "$base/before.tmp")" = 1
test "$(tail -n 2 "$base/before.tmp" | head -n 1)" = 0
test "$(tail -n 1 "$base/before.tmp")" = 0
mv "$base/before.tmp" "$base/before.txt"
input keyevent 223
saved=1
echo START_SAVED_SCREEN_OFF_COLLECTOR_EXITING
