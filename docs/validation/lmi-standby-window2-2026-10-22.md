# The second standby window: 68.1 % asleep, and a matched figure of 77 mA

## What this window is

The second matched window, collected with collector revision 4 on the
phone, 2026-10-22, unplugged from 19:17:31.7 UTC to 20:07:08.7 UTC.
The operator unplugged the cable, left the phone alone and replugged it
without touching the phone. The three quantities this project cares about
are reported apart below: the **awake durations**, the **counter
variations**, and the **energy actually measured**, which is none.

## The collector and the kernel agree

The corrected collector, revision 4, and the kernel log describe the same
sleeps:

| | collector | kernel frozen gaps |
|---|---|---|
| sleep 1 | 511.696 s | 511.696 s |
| sleep 2 | 763.389 s | 763.390 s |
| sleep 3 | not seen | 753.456 s |

The first two match to the millisecond. That is the first direct
validation of the corrected clock pair on a handset: `CLOCK_BOOTTIME`
minus `CLOCK_MONOTONIC`, compared with the wall-clock distance the
kernel log itself carries. The third sleep is only in the kernel log,
because the collector's one hour bound expired at 19:54:22 while the
phone was asleep; the collector wrote its result and stopped, and the
sleep from 19:54:35 to the reconnection at 20:07:08 was invisible to
it. The bound was too short for the operator's pace and must be
generous next time.

The window, from the kernel log:

| wall time | event |
|---|---|
| 19:17:31.7 | `usbpd`: USB Type-C disconnect, the physical unplug |
| 19:17:31.8 | the display is programmed, the screen was on |
| 19:17:36 | the collector records the USB transition and the counter step |
| 19:17:47.1 | the screen blanks, `DC off`, 15.3 s after the unplug |
| 19:32:48.3 | sleep 1, 511.696 s, woken by IRQ 438 `msoc-delta` |
| 19:41:35.8 | sleep 2, 763.390 s, woken by IRQ 438 `msoc-delta` |
| 19:54:22 | the collector stops on its bound and writes its result |
| 19:54:35.2 | sleep 3, 753.456 s, invisible to the collector |
| 20:07:08.7 | sleep 3 ends: the reconnection, IRQ 502 `typec-cc-state-change` |

**The two `msoc-delta` resumes did not light the screen.** The display
marks show exactly two programmings, one at the unplug and one at the
reconnection, and the panel stayed blank across both sleeps. That is the
quiet-gauge policy doing its job: the reason is recognised, the screen
stays dark, and the device goes back to sleep after the grace timer.

## The awake durations, measured

The unplugged interval is **2976.98 s**, 49 min 37 s. The sleeps total
**2028.542 s**. The awake time is **948.44 s**, and it is fully
accounted for:

| awake block | duration | cause |
|---|---|---|
| 19:17:31.7 to 19:32:48.3 | 916.6 s | of which 15.3 s with the screen lit, and 901.2 s of idle delay after the screen blanked |
| 19:41:20.1 to 19:41:35.8 | 15.7 s | the grace timer after the `msoc-delta` resume |
| 19:54:19.3 to 19:54:35.2 | 15.9 s | the grace timer after the `msoc-delta` resume |

So the duty cycle is **68.1 % asleep and 31.9 % awake**, and the awake
time is dominated by the 900 s inactivity delay, a policy parameter of
the platform. With that delay the interval could reach at most
(2976.98 − 900)/2976.98 = 69.8 % asleep, and the window reaches 68.1 %:
the difference is the 15.3 s of screen-on after the unplug and the two
grace timers, 47.3 s in total.

Against the first window, which was 28.1 % asleep, and against the
Android reference, which is 98.9 % asleep, this window is much closer to
the ceiling its own idle delay allows. The remaining difference to the
reference is the duty cycle itself.

## The counter variations, measured

The collector kept **187 qualified discharge endpoints** out of 477
samples. The 290 rejected samples are the plugged-in ones, every one of
them with the reason `usb_online_present`; **no sample was rejected for
an unknown or a failed read**, so the raw readings were all known.

The counter at the unplug, over the five seconds of the transition:

```
2676998 -> 2533597      -143401 uAh
```

That step is the gauge recomputing itself when the charger went away,
the same logical discontinuity the Android reference had to exclude,
where it was 86 mAh. The phone was at 100 % and charging before the
unplug, and it is at 100 % again now; the gauge reports "full" on the
charging side regardless of the real remaining charge, so the step is a
reporting artefact and not consumption. It is excluded, exactly as the
reference excludes its own.

Over the detached period, with the discontinuity excluded:

| interval | counter | rate |
|---|---|---|
| whole detached period, 2206.2 s | 2533597 -> 2486263, −47334 uAh | **77.2 mA** |
| the two sleeps, 1275.085 s | −20060 uAh | **56.7 mA** |
| the awake block, 912 s | −26925 uAh | **106.3 mA** |

The gauge's own `current_now` agrees: 148 mA at the unplug and 88 mA at
the end, bracketing a sleep rate near 57 mA and an awake rate near
106 mA. The Mobian gauge and the Android gauge report the same full
value, 2677 mAh against 2676 mAh, so their rates are directly comparable
as gauge readings.

**The matched Mobian figure, by the Android method**, that is the
counter drop with the unplug discontinuity excluded, over the detached
interval, is **77.2 mA**, against the Android reference's **13.84 mA**.
The sleep-period rate, which is the part that does not depend on the
duty cycle, is **56.7 mA against roughly 14 mA**. On this evidence the
Mobian phone draws about four times more than the reference while
asleep, and about five and a half times more over the window, which is
not only a duty-cycle difference.

## The energy actually measured: none

No current in mA is computed by the collector, and none is derived here
beyond the counter quotients above, which are gauge readings. The scale
of the Mobian gauge against the design capacity is still not established:
the gauge reports `charge_full` 2677000 against `charge_full_design`
4700000. The two platforms report the same full value, so the rates are
comparable to each other, but neither gauge is an independent sensor and
the reference itself says the histories are "one gauge's rounded software
history". The Android reference also warns that the 86 mAh discontinuity
and the return-boundary effects must be excluded, which was done here.

One more reading, worth keeping: the gauge reports **100 %** while the
counter reads 2504471, that is 93.6 % of `charge_full`. The percentage
is a state estimate and not the counter ratio, so it must never be read
as one.

## Limits

* One window, one build, one state of charge, 37 minutes of detached
  time against 8.5 hours for the reference.
* The counter is a gauge, and the Android reference's own caution about
  rounded software history applies to both sides.
* The scale of the gauge against the design capacity is not established,
  so the absolute figures carry that unresolved factor. The comparison
  between the two platforms is at the same gauge scale, not at an
  established physical one.
* The window includes the unplug and the reconnection, and 15.3 s of
  screen-on after the unplug. The sleep rate is taken over the two
  sleeps the collector saw, so it is not affected by that.
* The collector's bound expired before the reconnection, so the third
  sleep and the reconnection reading are missing from the collector's
  own result and come from the kernel log.

## What this changes

The Mobian side now has a figure by the Android method, and it is
several times the reference. The earlier framing, that the only
difference was a duty-cycle difference, does not hold: normalising for
the duty cycle leaves the sleep rate about four times higher.

That shifts the remaining question. The candidates to look at are the
ones that act while the processor is down: the always-on rails, and the
peripheral states in suspend. The quiet-gauge path itself is now shown
to work as intended during this window.

## Next

The esr-delta acceptance remains a separate decision, and this window
does not make it urgent: the wake did not occur here, and the screen-on
it caused in the first window is a duty-cycle cost, not a sleep-current
cost. The collector's bound must be generous next time.
