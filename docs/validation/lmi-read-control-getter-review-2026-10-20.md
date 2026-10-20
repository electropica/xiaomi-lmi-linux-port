# Read-control getter review — October 20, 2026

## Decision and experimental contrast

The source review does not demonstrate a persistent charger or gauge mutation
from the listed getters on their ordinary path. The bounded natural-resume
read-order experiment can proceed with qualifications. It is not a battery
fix, an electrical calibration, or a direct measurement during suspension.

Both arms read filtered current before and after the middle burst. Both also
read battery status three times. The contrast is **three additional counter
getters versus three direct-current getters**, not SRAM access versus none.
Counter getters may perform multiple underlying transfers; three logical
getters do not mean three bus transactions.

## Verified source paths

- `bms/current_now` uses the direct current-register read and matching-copy
  retry path in `fg_get_battery_current`. No SRAM access or charging setter was
  found in that getter. It still uses the same gauge as the other estimates.
- `bms/current_avg` and the counter getters use the previously reviewed SRAM
  access path, including temporary awake voting and memory arbitration.
  Successful cleanup does not prove that every transfer is free of overhead
  or that an error could never leave incomplete cleanup.
- `battery/status` is computed. Its battery-health helper can read BMS
  temperature from SRAM when external-FG support or the 480 warm-threshold
  branch applies. The retained `lmi-sm8250.dtsi` specifies
  `qcom,chg-warm-th = <480>`; this textual source finding is not a fresh
  verification of the effective running DTB.
- The observer reads the supply named `usb`, dispatched through
  `smb5_usb_get_prop` and `smblib_get_usb_online`. The distinct USB-port
  descriptor is named `pc_port` in this source; its dispatch must not be
  substituted for the actual `usb/online` path.
- `last_resume_reason_show` in `kernel/power/wakeup_reason.c` formats the
  stored reasons under a spinlock and does not clear them. The separate PM
  notifier clears reasons during `PM_SUSPEND_PREPARE`. This getter is not
  read-to-clear in the reviewed source.

## Conditional behavior, not observed causes

The independent capacity path can set `report_input_absent` when capacity is
zero, input is present, normal boot is active and voltage is below its cutoff
condition. The USB getter can then report offline while input remains present;
battery status can agree by reporting Discharging. Its USB helper also returns
an uninitialized local return code in that branch. These are source-level edge
cases, not an established explanation for the earlier non-empty-battery runs.
The observer's reported-USB stability guard is not a universal proof of physical
cable absence under that low-battery condition.

The battery-status getter can clear `fake_dc_on` under its wireless-BQ,
fake-DC and cold/overheat branch. Activation of that branch on this handset has
not been established. Neither conditional finding justifies changing charging
protections, calibration or the kernel before the planned observation.

The inspected status chain does not call `charge_done`. Concurrent capacity
handling, IRQs, uevents and work are distinct from actions caused by the listed
getters. A synthetic observer backend demonstrates consequences of reported
USB values only; it does not reproduce or validate the C driver on hardware.

The next observation remains unarmed pending the operator's departure signal.
No phone settings, build, flash, audio or video capture was performed for this
offline review. Match wake reasons and timing contexts when interpreting the
read-order data, and retain incomplete attempts as inconclusive evidence.
