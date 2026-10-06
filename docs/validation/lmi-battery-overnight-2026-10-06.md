# Battery overnight observation - 2026-10-06

The operator reconnected the phone after a night unplugged. Read-only SSH
inspection found 67% charging at approximately 05:21 CEST, increasing to
68% at 05:22. Uptime was about 45 hours 47 minutes; no reboot occurred overnight.

Persisted UPower history records 99% discharging at 20:05:51 CEST on October 5
and 69% at 04:13:54 on October 6. That persisted interval loses 30 percentage
points over 8 hours 8 minutes (about 3.69 points/hour). Combining the first
historical sample with the current 67% reading gives roughly 32 points over
9 hours 15 minutes; the exact unplug/replug timestamps and charge at those
instants were not recorded by this inspection. Charging had already resumed,
so this is an approximate observed overnight loss, not a controlled idle test.

Kernel logs show recurring deep suspend between short wake intervals of about
15-16 seconds, typically spaced approximately eight minutes apart. Deep suspend
therefore occurs, but the wake source and remaining consumption are unresolved.
Wi-Fi state during the night was not established; this must not be merged with
the earlier controlled Wi-Fi-on/off tests.

The fuel gauge reports charge_full=2,845,000 uAh against a design value of
4,700,000 uAh (about 60.5%). This is a reported estimate, not an independent
battery-health measurement. Current charging status agrees between sysfs and
UPower. No settings were changed and no camera or microphone was started.

## Wake-source correlation

Read-only follow-up again identifies IRQ 438, msoc-delta, for the repeated
night wakes; the final 05:17 wake instead names the power-button IRQ. An
inspected wake interval shows WLAN resume and a scan after the gauge wake,
then suspend approximately 16 seconds later. Notification screen-wake triggers
remain an empty list. This is consistent with the source review in the
[previous night's record](battery-overnight-2026-10-05.md): the gauge delta
interrupt can follow consumption and is not proof of its root cause. No gauge
interrupt, thermal control or charge protection was disabled.

The persisted 3.69 points/hour interval is similar to the previous night's
approximately 3.67 points/hour. Conditions were not controlled closely enough
to quantify a small change, and no autonomy improvement is established. The
earlier approximately 94 mA Wi-Fi-disabled deep-suspend result remains the
reference for investigating residual hardware power, separately from wake cost.


## Daytime unplugged interval - read-only inspection at 18:04 CEST

The operator reported reconnection after approximately ten hours unplugged.
Persisted UPower charge-history endpoints are 97% discharging at 06:54:53 and
55% discharging at 17:53:15 CEST on October 6: 42 percentage points over
10.9728 hours, or approximately 3.8277 points/hour. These are history sample
boundaries, not exact physical unplug/replug timestamps. The next persisted
charging sample is 56% at 17:59:00. At the first live inspection at 18:04:48,
the phone was already charging at 61%, USB online, current_now -1,218,749 uA
and temperature 26.5 C. Later live readings reached 63%; they must not replace
the last unplugged 55% endpoint.

The boot identity is unchanged and uptime was about 58 hours 30 minutes;
no reboot occurred during this interval. Journal entry/exit pairs inspected
from 06:50 show 95 completed deep-suspend pairs. Clipping their wall-clock
intervals to the discharge-history window gives about 95.87% suspend occupancy.
The complete inspected pairs total 38,154.343 wall seconds and only 17.479
paired monotonic seconds, consistent with CLOCK_MONOTONIC pausing in suspend.
This confirms system deep sleep, not minimum power in every hardware domain.
Latest repeated pre-replug wake records identify IRQ 438 msoc-delta roughly
7-8 minutes apart; one final record also names IRQ 454 dma-grant. The idle
parameter remains sleep_disabled=N. No interrupt or power protection was changed.

Current Wi-Fi radio state was enabled, but association and continuous radio
state over the unplugged interval were not established. This is another
uncontrolled long observation, not a repeat of the controlled Wi-Fi comparison.
The gauge reported learned capacity 2,822,000 uAh versus design 4,700,000 uAh;
that estimate is not an independent physical battery-health measurement.

The approximately 3.83 points/hour result is similar in scale to the previous
3.67-3.69 points/hour observations. Conditions do not support attributing a
small difference to a particular setting. No autonomy improvement is established.
The bounded morning gauge re-suspend diagnostic was not permanently deployed;
this interval must not be described as its long-run validation. Residual deep
sleep consumption remains unresolved. No camera, microphone, test collector,
radio change or new power policy was started by this inspection.
