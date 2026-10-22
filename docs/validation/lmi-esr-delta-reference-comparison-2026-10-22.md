# The esr-delta wake on the reference platform: it recurs, and it costs a fraction of a second there

## Why this note

The previous note verified the esr-delta path on the Mobian side: the
installed quiet-gauge gate recognises "438 msoc-delta" and "441
msoc-high" and not "445 esr-delta", so a resume caused by that interrupt
turns the screen on. It left the frequency open: one occurrence in the
kept Mobian evidence, against 995 `msoc-delta` over fifteen quiet
captures.

This note answers the frequency question with the evidence already kept,
without a new run. The answer is on the reference platform, and it
changes the weight of the candidate.

## What the reference platform shows

The LineageOS trace kept for the Android reference
(`lineage-power-trace-20261022-private`, private) contains Android's own
wakeup accounting for the night of 2026-10-07, 02:18 to 03:08, on the
same 4.19 qcom gauge driver:

```
Wakeup reason 323 pm8xxx_rtc_alarm: 2m 4s 743ms (63 times)
Wakeup reason 438 msoc-delta: 2s 173ms (7 times)
Wakeup reason unknown: 850ms (3 times)
Wakeup reason 445 esr-delta: 455ms (2 times)
Wakeup reason 448 batt-temp-delta: 344ms (1 times)
```

The battery-stats timeline in the same file gives the cost of each
wake, from the `+running` to the `-running` marker:

| wake reason | awake time per wake |
|---|---|
| `445 esr-delta` | 0.002 s, 0.326 s, 0.946 s |
| `438 msoc-delta` | 0.302 s to 0.360 s |

So on the reference platform the `esr-delta` interrupt **recurs**: three
episodes in that night, next to eight `msoc-delta` ones, and it is not a
one-off artefact. And it costs the same as a `msoc-delta` wake, a
fraction of a second. The device goes back to idle almost immediately:
**a gauge wake does not turn the screen on there.**

The Mobian window of 2026-10-22 is the opposite: the same interrupt, on
the same driver, programmed the display 0.163 s after the resume and
left the screen lit for 186 s. The difference is not in the hardware. It
is in the userspace reason gate of the quiet-gauge policy, which does
not know this reason and therefore takes the path that lights the
screen.

That is the strongest statement the kept evidence supports: the wake is
recurring, and its cost on Mobian is currently two orders of magnitude
above its cost on the reference platform.

## What cannot be measured retrospectively on Mobian

The Mobian side of the frequency stays open, and the reason is
structural:

* `/sys/kernel/debug/wakeup_reasons` **does not exist on this build**.
  The debugfs is mounted, the directory lists the platform devices, and
  the file is simply not there, so the kernel wakeup accounting the
  reference platform exposes is not available here.
* the kernel ring buffer rotates. It covered t=452 to t=7586 at 17:12
  and t=6332 to t=13535 at 20:44, so the `Resume caused by IRQ` lines of
  the 15:37 to 15:45 window are gone.

A census of the **whole** retained corpus finds exactly one
`Resume caused by IRQ 445, esr-delta` line, the one from the 2026-10-22
window. The Android occurrences are recorded by Android's own accounting,
not by kernel resume lines. The fifteen Mobian quiet captures record the
wake reason at the observer's events, and none of them carries this
reason.

## What follows for the candidate

Nothing in the reference evidence contradicts the candidate: accepting
"445 esr-delta" in the quiet-gauge gate, with the same fresh,
noncritical, discharging guards as "441 msoc-high", would bring the
Mobian behaviour of this interrupt in line with the reference platform,
where it costs a fraction of a second instead of 186 s of screen.

The extension is deliberately **not** wider. `448 batt-temp-delta` also
appears in the reference accounting, once. It is not added: it has never
been observed on this platform, and the policy fails open by design, so
an unknown reason keeps turning the screen on until it is observed and
judged.

## A proposal for the next revision, not implemented here

The Mobian rate could be measured during a window if the collector read
`/sys/kernel/wakeup_reasons/last_resume_reason` at each sample. That is
a passive sysfs read, with no runtime resume and no hardware query, and
it would give the reason sequence of the window next to the suspend
events. It is left out of revision 4 on purpose: the review of
2026-10-22 covered the endpoint qualification and the snapshot, and
changing the instrument again before it is deployed would move the
review target. It is proposed for the next revision.

## Limits

* The two rates are not directly comparable. The reference night woke
  every about 50 s to an RTC alarm, a much shallower sleep than the
  Mobian quiet nights, and a shallower sleep means more load changes.
  The Mobian rate stays unknown.
* The reference episodes come from Android's accounting and its policy.
  Android treating a gauge wake as a wake is a platform behaviour, not a
  property of the interrupt.
* The Mobian captures record the wake reason at the observer's events, so
  an `esr-delta` wake that produced no event would not be counted.
* No causal claim is made about why the ESR delta fires. The handler
  reads the battery resistance, the interrupt is armed with
  `enable_irq_wake`, and it is sensitive to a load change.
* The screen-on cost of 186 s is one observation, in one window.

## Next

Unchanged: the second standby window with the corrected collector, and
separately the build, the installation and a device observation of the
`esr-delta` acceptance. The patch is not to be deployed before the
second window, because that window measures the system as it is now.
