# The night window: 95 % asleep, and 47 mA by the Android method

## What this window is

One full night, collected with collector revision 4 on the phone,
unplugged 2026-10-22 20:31:25 UTC to 2026-10-23 04:35:53 UTC. The
collector ran from 20:24:50 to 04:35:54, with an eighteen hour bound on
the boot clock, no `--ufs-hardware-snapshot`, no RTC alarm, no setting,
policy or patch changed. The phone was not touched during the night.

The three quantities are reported apart: the **awake durations**, the
**counter variations**, and the **energy actually measured**, which is
none.

## The collector and the kernel agree

The kernel log still holds the tail of the night, with nine
`Resume caused by IRQ 438, msoc-delta` resumes and the reconnection
waking by `IRQ 502, typec-cc-state-change`. The whole-night record is
the collector's own result and its log, one line per event.

The collector saw **30 suspend events**, 27,675.691 s suspended, with
**no log truncation** (32 events total, 30 of them sleeps). The event
log capacity of 512 was never reached, and the USB transitions, one at
each end, are both present.

## The awake durations, measured

| | |
|---|---|
| detached interval, collector window | 29,463.542 s, of which 390 s plugged in |
| detached interval, endpoint set | 28,306.0 s, from 20:31:25 to 04:23:11 |
| suspended inside the endpoint set | 26,917.8 s |
| **awake inside the endpoint set** | **1388.2 s, so 95.1 % asleep** |
| suspended over the collector window | 27,675.691 s, **93.9 % asleep** |

The awake time is fully accounted for:

* **926 s** before the first sleep, that is the 900 s inactivity delay
  after the screen blanked, plus the screen-on after the unplug;
* **29 gaps of 10 s to 15 s** between the sleeps, the grace timers;
* about **145 s** of awake time inside the sleep brackets themselves,
  five seconds each.

The duty cycle by third of the night, on equal time slices:

| third | interval | sleeps | asleep | awake | median slope per sleep |
|---|---|---|---|---|---|
| 1 | 20:31 to 23:18 | 12 | 89.0 % | 1106.6 s | 54.9 mA |
| 2 | 23:18 to 01:48 | 9 | 98.3 % | 156.2 s | 42.5 mA |
| 3 | 01:48 to 04:35 | 9 | 98.7 % | 129.5 s | 37.1 mA |

**The quiet-gauge path worked all night.** Every wake was a
`438 msoc-delta`, the screen never came on, and the device went back to
sleep after the grace timer each time. The kernel log shows the display
programmed only at the reconnection.

## The counter variations, measured

At the unplug the counter stepped **2676999 to 2533925**, that is
−143074 uAh in five seconds: the gauge recomputing itself when the
charger went away, the same logical discontinuity the Android reference
excluded at 86 mAh, and the same value as the day window's −143401 uAh.

With the discontinuity excluded, over the endpoint set:

```
2533925 -> 2164682    -369243 uAh    28306.0 s    47.0 mA
```

The Android reference for the same quantity is 118 mAh over 8.524 h,
that is **13.84 mA**. The ratio is **3.4**.

The per-sleep slope, exact, from the readings that bracket each sleep:
minimum 33.6 mA, median 45.3 mA, maximum 102.1 mA. The bracket of a
sleep carries about five seconds of awake time, that is roughly 147 uAh
at the awake rate of the day window, which is about 1.3 % of a typical
bracket: the correction is small and does not change any conclusion.

**The slope is not constant through the night.** It falls from a median
of 54.9 mA in the first third to 42.5 mA and then 37.1 mA, while the
sleeps get longer, 793 s, 992 s, 1142 s of median. Whatever varies there
is not measured here, and it is a reason not to present a single factor
as an established quantity.

## The energy actually measured: none

No current in mA is computed by the collector, and none is derived here
beyond the counter quotients. The scale of the gauge against the design
capacity is still not established, and the two gauges reporting the same
`charge_full` does not prove that their coulomb scales are identical.
The Android reference's own figures are "one gauge's rounded software
history, not an independent sensor".

## What this changes, and what it does not

The day window was **not representative of the duty cycle**: 68.1 %
asleep there, 95.1 % here. Its net rate of 77.2 mA was inflated by the
900 s idle delay and by the awake rate around it; the night's net rate is
**47.0 mA**.

The difference from the reference therefore persists but is smaller
than the day window suggested: about **3.4 times** on the net rate, and
about three times on the sleep-only rate, 45 mA of median against the
roughly 14 mA the reference night implies.

What this does **not** establish is an electrical measurement. Three
reasons stand in the way, and they are the ones the figures must travel
with:

* the counter is a gauge, and its scale against the design capacity is
  unsettled;
* the same `charge_full` on both platforms does not prove a comparable
  coulomb scale;
* the sleep slope is not constant through the night, so even the gauge
  rate is not a single number.

The next step is unchanged in nature: whatever holds the processor down
is the candidate, and the discriminating verification is the regulator
summary read in the unplugged state on both platforms.

## Limits

* One night, one build, one device, one state of charge at the start.
* The endpoint sequence is bounded to the last 256 detached readings, so
  the whole-night reconstruction comes from the events and the counters,
  and the fine-grained tail from the endpoints.
* The attachment flag lagged at the reconnection: the collector saw it
  between 04:23:11 and 04:35:53, so the detached period is bounded
  between 28,306 s and 29,068 s.
* The Android reference is one night on one device, read from the same
  kind of gauge history.
