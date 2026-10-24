# Old-kernel profile window and RTC follow-up - October 24, 2026

The temporary October 7 Image with the DT-order-only diagnostic still publishes j11sun_4700mah/design 4700000. The installed qualified fallback image remains unchanged. These are temporary runtime results, not a permanent battery fix.

The first passive counter window had one 14.451573-second suspension, interrupted by IRQ 362 pm8xxx_rtc_alarm and a screen wake. It is not accepted for the intended comparison with reference long-suspend brackets. Original bytes were preserved; the observer completed and services remained active.

A separate 20-minute alarm-owner diagnostic kept the normal 900-second idle delay. Its unplug/replug markers span 1212.533185 seconds. One deep suspension lasted 295.868715303 seconds; the kernel journal identifies IRQ 473 typec-cc-state-change at cable replug. The RTC wake did not recur. The alarmtimer trace recorded zero entries with no reported buffer loss. The private instance was removed and global tracing controls were unchanged. This diagnostic did not sample battery counters and cannot supply the missing consumption rate.

A separate 100ms CLOCK_BOOTTIME_ALARM timerfd control, USB connected and awake after preserving the window, captured scheduling through do_timerfd_settime, firing with matching pointer/expiry and cancellation. The offline parser matched its programming stack. No suspend was requested; before/after sysfs wakealarm remained empty. The control instance was cleaned. This validates the event mechanism under control conditions, not historical attribution for IRQ 362.

The retained alarmtimer_suspend path selects the earliest kernel alarm and schedules an RTC timer during suspend. The RTC handler clears the alarm-enable bit on firing. An empty wakealarm snapshot before/after does not exclude a transient kernel alarm. Current system timers WakeSystem=no and no current alarm timerfd/RTC descriptor do not identify a past actor.

The driver-published-profile old-kernel quiet counter-rate case is still missing: 14 seconds is too short for the intended comparison, and the dedicated RTC follow-up recorded no counter endpoints. Corrected reference remains 79 detached/discharging brackets, median 45.607360385 reported units/s; the earlier old-kernel PROFILE_MISSING case had one 300.731523-second bracket at 24.097906116 reported units/s. These are estimator progressions, not calibrated electrical current. No causal kernel/profile verdict follows yet.

Next: the planned overnight passive observation on the same temporary kernel/profile, after finishing UI work and recording any changed packages. A usable bracket needs both endpoints detached/discharging; USB-return/recharge intervals are rejected. No new kernel build, forced RTC wake or permanent diagnostic installation is justified.
