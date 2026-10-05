# Battery overnight observation — 2026-10-05

Read-only inspection after the user reconnected the phone. No camera test,
radio setting, charge policy or power policy was changed.

UPower charge history records 99% at 2026-10-04 19:57:38 CEST and 61% at
2026-10-05 06:18:58 CEST: 38 percentage points in 10.356 hours, approximately
3.67 points/hour. The later 86% to 61% interval (23:27:43 to 06:18:58) spans
6.854 hours and gives 3.65 points/hour. These are history sample boundaries,
not exact user unplug/replug times. Rates assume recorded wall timestamps
are consistent; no monotonic fuel-gauge collector covered this interval.

In the later interval, kernel journal entry/exit pairs include 52 deep
suspends totaling 23,732.45 wall-clock seconds, approximately 96.2% of that
interval. Paired monotonic time totals only 9.64 seconds, consistent with
CLOCK_MONOTONIC stopping during suspend. This supports real system suspend,
not proof of every hardware power domain reaching its minimum-power state.
Periodic wakes, typically separated by roughly 7-8 minutes, remain visible.
Suspend counters at inspection were 88 successful / 0 failed for the boot;
the CPU-idle service was active and sleep_disabled was N.

At the first live snapshot the battery was 61%, Charging, 23.7 degrees C,
with current_now -1,165,526 uA (negative while charging in this driver).
Later snapshots rose to 63% then 64%, Charging. The phone had not rebooted
since the prior day. Current rfkill state indicated Wi-Fi enabled and
Bluetooth blocked. Overnight Wi-Fi association/state is not established;
this observation must not be treated as a repeat of a Wi-Fi-disabled test.

The gauge reports charge_full 2,845,000 uAh versus design 4,700,000 uAh,
approximately 60.5%. This is a reported learned capacity, not an independent
battery-health measurement; prior gauge/profile inconsistencies require
care before attributing the drain solely to physical battery aging.

Conclusion: charging and system deep suspend work, but approximately
3.7 percentage points/hour overnight drain remains excessive for a usable
idle-phone target. Battery consumption is not fixed. Remaining questions
include periodic wake source, residual hardware power and gauge consistency.
No personally identifying battery fields or raw private logs are published.

## Matched Wi-Fi radio comparison — 2026-10-05

The user performed two unplug/replug cycles. Both phases used the same boot,
CPU-idle setting N, screen off, no music/torch and a 300-second RTC-requested
deep suspend. USB online was 0 at both measurement endpoints. No Wi-Fi AP
was connected; this compares the enabled but unassociated radio with the
radio disabled, not Android connected-network/background-traffic behavior.

| Phase | Endpoint elapsed | Counter loss | Derived mean | CPU-awake monotonic delta | Deep suspends / failures |
|---|---:|---:|---:|---:|---:|
| Wi-Fi enabled | 302.058 s | 8,059 uAh | 96.05 mA | 0.539 s | 1 / 0 |
| Wi-Fi disabled | 301.297 s | 7,839 uAh | 93.66 mA | 0.524 s | 1 / 0 |

The difference is 2.39 mA, about 2.5%, for one sequential pair. Temperature
fell from 26.0 to 25.2 C in phase A and 25.2 to 24.7 C in phase B. Percentage
stayed 71 in both phases, illustrating why the counter was used instead.
The wake IRQ was 323 pm8xxx_rtc_alarm in both cases. Rates are fuel-gauge
reported counter differences, not measurements with an external power meter.
This short pair does not establish a statistically significant Wi-Fi effect,
and the residual approximately 94 mA is not explained by radio enablement.

The kernel night log repeatedly identifies IRQ 438 msoc-delta and WLAN logs
explicitly say Non-WLAN triggered wakeup. In the inspected qpnp-fg-gen4.c,
fg_delta_msoc_irq_handler services fuel-gauge capacity changes; the default
DELTA_SOC threshold is 5 (0.5%). Such wakes can follow discharge and do not
by themselves prove its root cause. Their additional power cost is unresolved.

Phase A completed and restored its radio state. Phase B finished measurement
but nmcli radio wifi on timed out after ten seconds during restoration;
the service exited 1. Follow-up verified enabled radio, disconnected Wi-Fi,
charging and no active collection/alarm. This restoration failure does not
invalidate already-completed endpoint samples; it prevents claiming a clean
phase-B service completion. The preserved collector increases only that
restoration timeout to 45 seconds; that revision is syntax-checked, not a
repeated A/B trial. Raw private logs stay outside Git. Phone settings are
restored; no charge, thermal, gauge-learning or regulator setting was changed.
