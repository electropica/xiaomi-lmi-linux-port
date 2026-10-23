# Standby window collector: clock correction and window qualification, 2026-10-22

## The blocking defect

`userspace/power/diagnostics/collect-matched-standby-window.py` read
`/proc/uptime` and returned its two fields as `boottime` and `monotonic`.

The first field of `/proc/uptime` is the uptime since boot. The second is the
**aggregate CPU idle time**, summed over every CPU, not `CLOCK_MONOTONIC`.
Every value derived from that pair was wrong:

* `suspended_accumulated` was `uptime - aggregate_idle`, a quantity that has
  no physical meaning. On the host used for the offline tests it read
  `-592314.6`, and on the phone it read `-8827.16` at the first sample.
* `suspended_accumulated` grew *downwards* while the device was awake and
  idle, so the collector's suspend detection could not fire on the real
  suspends.
* The suspend intervals and every derived duration in the output file were
  invalid.

The defect was invisible in the output: the file looked complete and the
numbers looked plausible. The independent review of 2026-10-22 identified it
before any handset run could be based on it.

## The correction

Revision 2 of the collector:

* reads the clocks with `time.clock_gettime(time.CLOCK_BOOTTIME)` and
  `time.clock_gettime(time.CLOCK_MONOTONIC)`, and **refuses to collect**,
  with exit code 2, when either clock is unavailable;
* detects a suspend as the **growth of the difference between two readings**,
  never as an absolute difference. The monotonic clock is slewed by the
  timekeeping layer and the boot clock is not, so the two drift apart slowly
  and an absolute difference would drift with them;
* takes the wall-clock deadline on `CLOCK_BOOTTIME`, which keeps counting
  across a suspend. The previous `--max-seconds` used `time.monotonic()`,
  which stops during a suspend, so it did not bound the real duration of the
  window. A userspace deadline still cannot be enforced while the processor
  is down: the check happens at the next resume. No RTC wake alarm is added,
  because a periodic wake would be a new wake source on a device whose wake
  sources are exactly what is under study;
* keeps the **sequence** of suspend events instead of only the first one, so
  a window with several suspends is reported event by event;
* validates `--poll` and `--max-seconds`: a non-positive or non-finite value
  is refused;
* records every USB transition with the counter on both sides, so the
  discontinuity observed around the unplug is **preserved rather than
  explained away**;
* no longer states that the counter "does not move while the processor is
  down". That was an assertion about the gauge, not a measurement, and it
  justified a certainty the readings do not support.

## Offline tests

`userspace/power/diagnostics/test-collect-matched-standby-window.py` drives
the collector with synthetic samples. No phone is contacted.

```
python3 userspace/power/diagnostics/test-collect-matched-standby-window.py
```

18 tests pass. They cover the awake passage (no false suspend), a synthetic
suspend gap of a known duration, the resume that follows it, several
suspends kept as a sequence, the USB transitions, the bounded event list,
the wall-clock deadline, the refusal of a missing clock, the refusal of
non-positive and non-finite sampling arguments, the preservation of the
counter jump across the unplug, the reporting of the suspended fraction,
the absence of any claim of a calibrated current, and the clock slew.

The same suite run against the previous implementation, taken from
`HEAD:userspace/power/diagnostics/collect-matched-standby-window.py`, fails
immediately: the previous revision has no `suspend_gap`, no `Window`, no
`build_result`, and its `clocks()` returned the aggregate idle time as the
monotonic clock. The tests fail against the code that has the defect and
pass against the corrected code, which is what makes them useful as a
regression barrier.

The other repository test, `test-ufs-policy-reader.py`, still passes with 10
tests.

## What the 15:21-15:47 window actually was

The window that was collected with the defective collector carries no
suspended-time information. Its own clock is invalid. What it does carry is
the raw kernel log, and that log was analysed separately.

The device **did** suspend during the unplugged window. Two deep suspends
are visible in `dmesg`, and the wall-clock and monotonic anchors bracket
them:

| | wall interval (UTC) | duration | resume cause |
|---|---|---|---|
| suspend 1 | 15:37:05 to 15:43:24 | 379.217 s | IRQ 438, `msoc-delta` |
| suspend 2 | 15:43:40 to 15:44:37 | 57.005 s | IRQ 445, `esr-delta` |

Total suspended time: **436.222 s**. The same value, 436.222 s, is obtained
independently from `CLOCK_BOOTTIME - CLOCK_MONOTONIC` measured on the phone
while it was awake and reconnected. The two methods agree to within a
millisecond, which is the first direct confirmation that the corrected clock
pair measures the right thing on this device.

The unplug is at 15:21:49 (`USB Type-C disconnect`) and the reconnection at
15:47:43. The unplugged interval is therefore **1554.1 s**, of which 436.2 s
were spent suspended. **The phone was awake for about 72 % of its own
unplugged window.**

This is the substantive result of the window, and it is not the result the
collector was built to produce. The phone does not stay asleep while
unplugged: it suspends for a few minutes, wakes, and spends most of the
interval awake. The `upower` charge history confirms the same shape from the
userspace side: the last `100% fully-charged` entry is at 14:52:18, the
`99% discharging` entry is at 15:44:52, and `100% charging` resumes at
15:48:06, twenty-three seconds after the reconnection.

### The screen wake at 17:44:37 local

The display was blanked by the kernel at 15:22:04 UTC, fifteen seconds after
the unplug (`DC off`), and stayed off. It was programmed again at
15:44:37.345 UTC, **0.16 s after the second resume**, with
`dsi_display_set_mode` and the panel ESD interrupt re-enabled. It was
blanked again at 15:49:37 UTC.

So the screen came back on by itself, immediately after a resume, with no
operator action, and the operator observed it at about 17:45 local. The
first resume, at 15:43:24, did not program the display. The second resume,
caused by `esr-delta`, is the one the display followed.

### The counter

`charge_counter` read 2676998 before the unplug, at `Full` and 100 %, which
is equal to `charge_full` (2677000). It read 2508679 at 15:54, while the
device was charging, and 2676993 at 18:29, again `Full`. On this platform
the counter therefore behaves like **remaining** charge and it moves back
towards `charge_full` when the device is plugged in. The raw difference
between the reading taken before the unplug and the reading taken at 15:54
is 168.3 mAh.

That 168.3 mAh is **not a consumption figure for the window**. It is a raw
counter difference, and it spans the unplug *and* the recharge that
followed it: the counter was sampled before the unplug and then again
while the device was charging after the reconnection, with nothing in
between, and on this platform the counter moves back up towards
`charge_full` while charging. The two effects are mixed in the same
difference, so the figure cannot be presented as the charge consumed during
the unplugged window. The `upower` history records percentages rather than
the counter, so it does not fill the gap either. The Android reference had
to exclude an 86 mAh discontinuity that appeared at its own unplug
timestamp. The corrected collector exists to make the same exclusion
possible here, by reading the counter on both sides of the unplug.

## Limitations

* The suspend intervals above come from the kernel log, not from the
  collector. They are a separate, independent measurement and are not
  evidence that the corrected collector works; only a run of the corrected
  collector can show that.
* The window is a single occurrence, on one build, in one state of charge.
* The counter discontinuity at the unplug is present but not yet attributed.
  The gauge scale relative to the design capacity is not established either.
* Nothing here measures a current. The figure that would be compared with
  13.84 mA is a gauge slope, and the collector deliberately does not compute
  one.
* The absolute screen state is still not directly readable on this platform.

## Next decision

The comparison method is still the open question, but it is now a **different**
question. The previous framing was "produce the Mobian number by the Android
method". The window shows that the Mobian device does not spend an unplugged
window asleep, so a like-for-like number needs the sleep duty cycle to be
equalised, or the comparison has to be stated as a duty-cycle difference
rather than a current difference.

The single next measurement is therefore a **second matched window with the
corrected collector**, whose purpose is to confirm the suspend intervals and
the awake fraction with the instrument that is now correct, and to measure
the counter discontinuity at the unplug with the counter read on both sides
of it. That is a re-run of a window already agreed in principle, with a
corrected instrument, and it needs the operator's unplug and replug. It
produces the Mobian window figure and the unplug discontinuity; it does not
produce a calibrated current and it does not by itself explain the standby
difference.
