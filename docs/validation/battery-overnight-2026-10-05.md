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
