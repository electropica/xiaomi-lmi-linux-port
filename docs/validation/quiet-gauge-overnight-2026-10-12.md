# Quiet gauge resume: overnight observation, 2026-10-12

## Installed configuration and method

The handset retained Phosh 0.46.0-3+deb13u1+lmigaugewake2 and
gnome-settings-daemon 48.1-1+lmiquietgauge1 with their persistent opt-ins,
without debug environments or the optional shorter-grace setting.
The RPMh diagnostic boot (SHA256
a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50)
and the suspend-only NPU policy were unchanged. Wi-Fi remained enabled.

A passive phone-local observer recorded sleep/return signals, software screen
state, wake reasons and three BMS charge estimates. It did not force suspension,
set a wake alarm, change radio/performance policy or capture media. USB polling
only ran while awake. Departure and return remained in the same boot.

## Results

| Observation | Result |
| --- | --- |
| Actual cable-free interval | 8 h 51 min 37 s |
| Displayed battery level | 100% at departure, 83% at charging return |
| Clock-accounted system suspension | 8 h 27 min 47 s, about 95.52% of the cable-free interval |
| Gauge-only resumes | 32, all recorded as IRQ438 msoc-delta |
| Software screen state | Initial lock/blank; no recorded unblank or WakeUpScreen during gauge-only returns; USB return remained visible |
| Services at retrieval | Both active, zero restarts; expected opt-ins retained |
| Observer cleanup | Finished successfully; no RTC wake alarm or outstanding NPU recovery state |

The initial automatic suspension retained the normal fifteen-minute timeout.
Gauge resumes were followed by roughly fifteen-second awake intervals, then
actual sleep. These intervals were not removed by the installed quiet-screen
fix. The complete clock accounting includes the final sleep ending at USB
return; the charging return is excluded from charge-counter quotients.

## Charge-accounting boundaries

Across eligible adjacent USB-zero endpoints, approximately 8.621 hours were
accounted. Summed charge-counter decreases were 422,523 uAh (49.01 mA by that
accounting); the shadow estimate gave 422,641 uAh (49.03 mA). The raw estimate
gave 752,040 uAh (87.24 mA). All observed learned/nominal capacity scales remained
unchanged. These are differently scaled/modelled estimates, not three independent
ammeters. Do not average them into a purported physical current measurement.

The last charging samples and the final unobserved discharge-to-reconnection
boundary are excluded from those quotients. The displayed 17-point fall is an
observed UI result, not a calibrated charge loss. Counter changes between
samples can still contain internal gauge-model corrections.

## Decision

The screen-wake correction survived a long interval without a reboot or service
restart. Standby drain remains unresolved: extensive actual suspension coexists
with substantial discharge. Shortening the roughly fifteen-second awake grace
cannot be assumed to remove consumption occurring while suspended. Thirty-two
grace periods total only about eight minutes in this observation.

Keep the qualified installed packages and the single current kernel. No new
kernel, shorter-grace package build or repeated identical short trial is
justified by this result alone. Compare future residual-power hypotheses using
the same counter method, radio state and real sleep accounting. Android radio-off
observations are useful historical evidence but not a matched causal comparison
to this Wi-Fi-enabled night. Fresh-image hardware qualification is still pending.

See the [power decision record](../../kernel/diagnostics/power/README.md) and
[source review of the separate grace draft](quiet-gauge-grace-source-review-2026-10-11.md).
Private raw samples, timestamps and device/session identifiers remain outside Git.

## Follow-up transition trace and source-only USB-cycle boundary

A subsequent 20 min 45 s passive cable-free observation did not enter system
suspension: neither PrepareForSleep nor a paired kernel sleep boundary was
recorded. Its trace buffers overflowed during the awake interval. The owned
trace was saved and removed, with no outstanding alarm or collector. This
observation is unqualified for peripheral state during deep sleep; absent
callback/disable events cannot be interpreted as evidence of powered rails.

The battery timeout remained 900 seconds with suspend selected, and no blocking
sleep inhibitor appeared in the return inspection. An automatic-suspend warning
logged a NULL-string assertion; the installed source passes a NULL icon to its
notification helper. That warning alone does not establish why sleep was skipped.

A separate native fixture reproduced a possible state-machine cause in the exact
installed GSD source: an ordinary USB wake from terminal SLEEP on AC temporarily
sets NORMAL, then restores SLEEP, whose AC action is nothing. A later battery
SLEEP request is rejected as an equal idle mode. Actual user activity clears
that state and allows a subsequent sleep request. This ordering is reproduced
in isolated source-function tests, not directly proven as the live handset state
in the inconclusive observation.

The [source-only USB-cycle draft](../../kernel/diagnostics/power/userspace/gsd-usb-cycle-state-draft.patch)
normalizes a non-quiet resume only in an active session with the existing explicit
quiet-resume opt-in. It cancels an older temporary restoration before entering
NORMAL, while leaving the quiet-gauge branch and default opt-out unchanged.
Six native cases pass, including both signal orders, real-activity cancellation,
quiet resuspension, inactive-session fallback and opt-out. GNU patch application
reproduces the exact complete candidate bytes. The draft starts from source
SHA256 154a332b498cb2edce4ee4d8125d9310031b2939b29edb9d2e9b55259e18c3ef
and produces SHA256 31a319b3e9d4542bc6f1287da3c085c4872aa53c224bca0b1e96d32d739510a3.
It is separate from the optional shorter-grace draft. The later incremental
ARM package build and two target USB cycles are documented below.

## Complete transition trace

After the initial overflowed captures, a bounded explicit-suspend observation
used a 2 MiB per-CPU owned trace buffer. It recorded 190.634 seconds of actual
clock-accounted sleep ending at USB return, 5,637 paired device-PM callbacks
without recorded error, and paired regulator enable/disable/voltage operations.
No trace-buffer overrun or unmatched operation was found. The instance and
collector were cleaned up after retrieval.

One complete machine-suspend window contained 26 RPMh messages, including six
sleep-bank BCM messages with no valid nonzero vote. Observed CX/MX sleep requests
were zero. This covers emitted messages only: cached commands, other masters'
votes and physical rail current must not be inferred from missing messages.
Panel, UFS PHY and GPU-domain disable completions were observed. Driver callbacks
and regulator completions are software evidence, not a physical power meter.
The trace clock did not advance between the machine-suspend markers in this
kernel; the separate BOOTTIME-minus-MONOTONIC samples provide the sleep duration.

## Daytime observation: initial protocol error and no automatic return to sleep

The subsequent cable-free interval lasted 11 h 00 min 19 s, with the displayed
level changing from 97% at departure to 59% at charging return. The same boot,
installed package versions, service opt-ins and Wi-Fi-enabled setting were
retained. Both userspace units remained active with zero restarts. The observer
finished successfully; no alarm or pending NPU recovery state remained.

Only one system-suspend interval occurred, lasting 998.686 seconds (16 min 39 s).
The first gauge-only IRQ438 return unblanked the software screen state. It
blanked again five minutes later, but no further system suspension occurred
during the remaining cable-free interval. The kernel journal independently
contains only that one sleep entry and exit.

The initial explicit suspension was requested while the screen was not yet
blank. This was a protocol error: it did not meet the installed filters' required
blank-before-sleep qualification, so their visible-wake fallback was expected.
Do not present this day as a qualified reproduction of the successful quiet
night, or as evidence that the qualifying filters silently regressed.

The absence of later automatic suspension still requires correction or causal
qualification. The source-only USB-cycle ordering reproduced above is a lead,
not a directly inspected live idle-state enum. Its six native boundary cases and
exact patch application pass. The user subsequently completed the incremental
ARM build; the two target cycles and retained package are documented below.

Eligible adjacent USB-zero counter samples cover only approximately 22 minutes
before the long unsampled awake gap. Their roughly 89/90/122 mA method estimates
must not be reported as eleven-hour average current; charging return endpoints
remain excluded. The displayed fall is observable, but no calibrated current or
cell-health conclusion follows.


## USB return and subsequent automatic suspension: two-cycle validation

The user built GSD/common `48.1-1+lmiquietgauge2` from the pinned USB-cycle
candidate source. Only those two packages were changed; Phosh remained
`0.46.0-3+deb13u1+lmigaugewake2`, with the existing kernel and NPU policy.
Verified GSD1 packages and a timed rollback were staged before installation.

Two unplug/replug cycles used a temporary 60-second battery idle timeout.
The screen was verified locked before each observation. Both cycles reached
automatic deep suspension without an explicit Suspend request or wake alarm.
BOOTTIME-minus-MONOTONIC accounting measured 153.455 and 158.037 seconds of
sleep, ending at USB return. Both observations used the same GSD process,
without a service restart between cycles, on the same boot. This verifies
that the second suspension remains reachable after a USB wake.

The GSD2 pair was retained. The normal 900-second idle timeout was restored;
the owned debug override was removed and live debug environment absence
verified. Temporary rollback/timeout timers were stopped after verification;
the verified GSD1 rollback remains available. Phosh, kernel and NPU policy
were unchanged. No pending RTC alarm or NPU recovery state remained.

These are shortened-timeout functional observations, not an autonomy result.
Neither interval contained a qualifying gauge-only wake. The unchanged quiet
branch has source regression coverage, but target gauge-resume behavior and
long natural standby still require observation with the retained GSD2 pair.
The currently built image profile still pins GSD1 until its private package
inputs are updated and a new image is separately built and qualified.
