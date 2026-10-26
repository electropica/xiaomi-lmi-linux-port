# Quiet natural gauge wakes: overnight validation, 26 October 2026

## Preserved runtime and capture

The operator confirmed USB return before device access. The existing passive
capture was retrieved first: 80 valid records, clean finished marker, unchanged
boot, intended j11sun_4700mah profile and reported full capacity 2637000.
The observer is inactive with success, RTC alarm is empty and the older reference
log is unchanged. Exact raw logs and receipts remain private, outside Git.

Accepted Phosh irqnames1+drawerpreview1, GSD IRQ-name handling and private-target
Phoc remain installed. The already-built combined search candidate remains
uninstalled. No power policy, kernel or image was changed for this analysis.

## Timing and display

The observed unplug/replug marker interval is 35322.359 seconds (9h48m42s).
Paired boottime/monotonic clocks infer 33847.364 suspended seconds, or 95.824%
of that interval. This includes the normal initial idle delay. The displayed
battery changed from 100 to 82 percent; this is 18 percentage points, not a
calibrated energy measurement or a justified linear autonomy extrapolation.

All 35 qualified natural gauge returns have subsequent D-Bus awake gaps between
14.807 and 15.023 seconds, median 14.946. The historical approximately 1201-second
awake dwell did not recur in these observed gaps. The retained filtered kernel
journal covers only a suffix: four suspend entry/exit boundaries and one complete
exit-to-deep-entry gap of 15.697 seconds. Do not describe all 35 cycles as
independently kernel-validated. ScreenSaver state is not physical panel power.

The first sampled USB-present row precedes the replug marker by 1.061 seconds;
that final charging-contaminated counter bracket is excluded.

## Predeclared early/late channel comparison

The offline analyzer fixed its bands before retrieval: brackets wholly within
the first two hours, versus brackets beginning after four hours. There are
eight early and eighteen late qualified brackets.

| Reported channel, median units per elapsed second | Early | Late | Change |
| --- | ---: | ---: | ---: |
| charge_now_raw | 24.9021 | 24.7202 | -0.730% |
| charge_counter | 15.6606 | 10.4737 | -33.120% |
| charge_counter_shadow | 15.6058 | 10.4863 | -32.805% |
| cc_soc | 0.0529340 | 0.0524621 | -0.891% |

Median suspended bracket duration increases from 739.083 to 1100.199 seconds.
Median shadow drop per selected bracket remains approximately 11539 versus
11543 reported units. Samples are triggered by SOC-delta wakes: similar model
increments are selected, so these are not independent current measurements.
Median resume temperature also changes, 24.5 to 20.6 degrees C; time, SOC and
temperature co-vary, so temperature causality is not established.

## Source interpretation and decision

The inspected FG getters use different state: CC_SOC times nominal capacity
for raw, CC_SOC_SW times learned capacity for software, BATT_SOC times learned
capacity for shadow. The status-work capacity-learning path can re-prime
CC_SOC_SW during discharge; the getter itself does not perform that write.
During detached samples software minus shadow ranges from -257 to +597 units.
This is compatible with SOC anchoring, but does not prove an actual prime write.

The sustained rapid return to suspend is accepted. A physical current reduction
late in the night is NOT established: the software/model channels slow while
the raw channel is nearly stable. Neither an absolute mA conversion nor a
universal learned/design scale correction is adopted.

The existing Android overnight comparison is rounded software-counter history
with a charging/unplug discontinuity. It has no matching continuous raw-channel
sequence for this comparison. It cannot decide whether this night's raw/model
divergence also occurs under Android. A useful future paired observation would
preserve the same raw/software/shadow channels and clocks on Android; a further
identical Mobian-only overnight run would not resolve that missing comparison.
No new run, OS switch or build has been started.

## Wi-Fi follow-up after preservation

The prepared cached GET could not run because iw is absent. Read-only
NetworkManager queries return the active profile's powersave field as default;
no explicit powersave entry was found in its printed global configuration.
This is not evidence of firmware PS being on or off, nor a reconstruction of
overnight state. No scan, reconnect, package install or policy change occurred.

References: the existing
[gauge source review](lmi-offline-gauge-recheck-2026-10-25.md),
[Wi-Fi policy review](lmi-wifi-sta-powersave-source-review-2026-10-25.md), and
[current research checkpoint](../status/BATTERY-RESEARCH-CURRENT.md).
