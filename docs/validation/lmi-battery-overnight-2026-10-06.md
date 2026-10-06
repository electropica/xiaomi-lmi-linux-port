# Battery overnight observation ? 2026-10-06

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
15?16 seconds, typically spaced approximately eight minutes apart. Deep suspend
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
