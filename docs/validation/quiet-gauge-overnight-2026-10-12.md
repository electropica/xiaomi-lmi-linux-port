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
