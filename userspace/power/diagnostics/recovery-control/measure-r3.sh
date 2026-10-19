#!/system/bin/sh
# Temporary recovery control; no partition, firmware or user-data access.
set -eu
TOTAL_SECONDS=${1:-7200}
case "$TOTAL_SECONDS" in 1800|3600|7200) ;; *) echo 'Duration must be1800,3600 or7200 seconds' >&2; exit 2;; esac
CHECKPOINT_SECONDS=1800
[ "$TOTAL_SECONDS" != 1800 ] || CHECKPOINT_SECONDS=600
ROOT=/dev/lmi-recovery-power-control-r3-$TOTAL_SECONDS
[ "$(id -u)" = 0 ]
pidof recovery >/dev/null
[ "$(cat /sys/class/power_supply/usb/online)" = 1 ]
[ "$(cat /sys/power/mem_sleep)" = 's2idle [deep]' ]
[ -z "$(cat /sys/class/rtc/rtc0/wakealarm)" ]
[ ! -e "$ROOT" ]
mkdir "$ROOT"
LOG=$ROOT/result.txt
SLEEP=/sys/module/lpm_levels/parameters/sleep_disabled
RTC=/sys/class/rtc/rtc0
NODES='soc:qcom,npu-npu-llcc-bw soc:qcom,npu-llcc-ddr-bw soc:qcom,npudsp-npu-ddr-bw'
cat "$SLEEP" > "$ROOT/sleep-original"
for n in $NODES; do
  d=/sys/class/devfreq/$n
  [ "$(cat "$d/governor")" = performance ]
  [ "$(cat "$d/min_freq")" = 0 ]
  grep -qw powersave "$d/available_governors"
  cat "$d/governor" > "$ROOT/$n.governor"
done
restored=0
owned_alarm=0
restore() {
  set +e
  if [ "$owned_alarm" = 1 ]; then
    alarm=$(cat "$RTC/wakealarm")
    if [ -z "$alarm" ] || [ "$alarm" = "$target" ]; then
      echo 0 > "$RTC/wakealarm"
    else
      echo RTC_CHANGED_EXTERNALLY >> "$LOG"
    fi
  fi
  for n in $NODES; do
    [ ! -r "$ROOT/$n.governor" ] || cat "$ROOT/$n.governor" > /sys/class/devfreq/$n/governor
  done
  cat "$ROOT/sleep-original" > "$SLEEP"
  echo RESTORATION >> "$LOG"
  cat "$SLEEP" >> "$LOG"
  for n in $NODES; do cat /sys/class/devfreq/$n/governor >> "$LOG"; done
  cat "$RTC/wakealarm" >> "$LOG"
  restored=1
}
finish() { [ "$restored" = 1 ] || restore; }
trap finish EXIT
trap 'exit 2' HUP INT TERM
snapshot() {
  echo "SNAPSHOT:$1" >> "$LOG"
  cat /proc/uptime >> "$LOG"
  for s in battery bms usb; do
    for f in status online capacity charge_counter charge_counter_shadow charge_now_raw charge_full charge_full_design current_now current_avg voltage_now temp; do
      p=/sys/class/power_supply/$s/$f
      if [ -r "$p" ]; then printf '%s:%s=' "$s" "$f" >> "$LOG"; cat "$p" >> "$LOG"; fi
    done
  done
  echo LAST_SUSPEND >> "$LOG"
  cat /sys/kernel/wakeup_reasons/last_suspend_time >> "$LOG"
  cat /sys/kernel/wakeup_reasons/last_resume_reason >> "$LOG"
  printf "\n" >> "$LOG"
}
echo WAITING_FOR_UNPLUG > "$LOG"
# Bounded waiting period for the operator; no changes before unplug.
i=0
while [ "$(cat /sys/class/power_supply/usb/online)" = 1 ]; do
  i=$((i+1)); [ "$i" -lt 600 ] || { echo NO_UNPLUG >> "$LOG"; exit 1; }
  sleep 1
done
sleep 20
[ "$(cat /sys/class/power_supply/usb/online)" = 0 ]
[ "$(cat /sys/class/power_supply/battery/status)" = Discharging ]
echo N > "$SLEEP"
for n in $NODES; do
  echo powersave > /sys/class/devfreq/$n/governor
  [ "$(cat /sys/class/devfreq/$n/cur_freq)" = 0 ]
done
sleep 2
snapshot BEFORE
read uptime rest < /proc/uptime
start_seconds=${uptime%%.*}
deadline=$((start_seconds+TOTAL_SECONDS))
echo "MEASUREMENT_SECONDS:$TOTAL_SECONDS" >> "$LOG"
wake_count=0
while :; do
  read uptime rest < /proc/uptime
  remaining=$((deadline-${uptime%%.*}))
  [ "$remaining" -gt 0 ] || break
  [ "$(cat /sys/class/power_supply/usb/online)" = 0 ] || { echo EARLY_USB >> "$LOG"; exit 1; }
  for n in $NODES; do
    [ "$(cat /sys/class/devfreq/$n/governor)" = powersave ]
    [ "$(cat /sys/class/devfreq/$n/cur_freq)" = 0 ]
  done
  if [ "$owned_alarm" = 1 ]; then
    alarm=$(cat "$RTC/wakealarm")
    [ -z "$alarm" ] || [ "$alarm" = "$target" ] || { echo EXTERNAL_RTC_CHANGE >> "$LOG"; exit 1; }
    echo 0 > "$RTC/wakealarm"
  fi
  [ -z "$(cat "$RTC/wakealarm")" ]
  now=$(cat "$RTC/since_epoch")
  # Separate scheduled checkpoints from natural health-service wakes.
  next_checkpoint=$((start_seconds+((${uptime%%.*}-start_seconds)/CHECKPOINT_SECONDS+1)*CHECKPOINT_SECONDS))
  [ "$next_checkpoint" -le "$deadline" ] || next_checkpoint=$deadline
  alarm_delay=$((next_checkpoint-${uptime%%.*}))
  [ "$alarm_delay" -ge 1 ] || alarm_delay=1
  target=$((now+alarm_delay))
  owned_alarm=1
  echo "$target" > "$RTC/wakealarm"
  [ "$(cat "$RTC/wakealarm")" = "$target" ]
  echo "RTC_REQUEST:$now:$target:$remaining:$alarm_delay" >> "$LOG"
  echo SUSPEND_REQUEST >> "$LOG"
  echo mem > /sys/power/state
  wake_count=$((wake_count+1))
  snapshot "WAKE_$wake_count"
  # Bound repeated failures; enough allowance for a60s health timer over2h.
  [ "$wake_count" -le 256 ] || { echo TOO_MANY_WAKES >> "$LOG"; exit 1; }
done
snapshot AFTER
echo SUSPEND_RETURNED >> "$LOG"
restore
echo FINISHED >> "$LOG"
