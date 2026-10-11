# Quiet gauge resume: bounded grace investigation — 2026-10-11

## Findings and scope

Trial40 qualifies quiet display handling and prompt kernel sleep entry with
the retained Phosh v2/GSD v1 pair. It still records 14.8867 and 15.3851 seconds
between a gauge resume and the next PrepareForSleep. These are awake gaps,
separate from the approximately 0.63-second PM boundary overhead.

GNOME 48.1 defines POWER_UP_TIME_ON_AC as 15 seconds, originally for temporary
undimming after connection to AC. set_temporary_unidle_on_ac stores the previous
idle mode, enters NORMAL and schedules its restoration with that constant.
Our quiet-resume companion intentionally reuses this restoration mechanism;
this explains the remaining interval without requiring a new kernel hypothesis.

Sources:
- https://raw.githubusercontent.com/GNOME/gnome-settings-daemon/48.1/plugins/power/gsd-power-constants.h
- https://raw.githubusercontent.com/GNOME/gnome-settings-daemon/48.1/plugins/power/gsd-power-manager.c
- https://docs.gtk.org/glib/func.timeout_add_seconds_full.html
- https://bugzilla.gnome.org/show_bug.cgi?id=726056

The original WakeUpScreen change deliberately avoided resetting global idle
time, so automatic suspend would remain independent. That design supports
preserving the temporary previous-mode restoration rather than resetting all
idle watches or treating every gauge event as physical user input.

GLib seconds timers can round their first interval by up to one second and
run late when the main context is busy. Therefore a proposed two-second timer
is a requested grace interval, not a measured two-second target guarantee.

## Source-only proposal

The incremental proposal accepts LMI_GSD_QUIET_GAUGE_GRACE_SECONDS only during
the already-qualified quiet-gauge transition. Allowed values are decimal
integers from 2 through 15; absent, malformed or out-of-range values preserve
15 seconds. Ordinary wake/AC paths always preserve their existing 15 seconds.
The global constant, gauge IRQ and existing qualification gate remain unchanged.

Native checks compile the actual edited state functions with isolated GLib
dependencies. They cover duration parsing, ordinary wake preservation, existing
five state scenarios and thirteen qualification cases. GNU patch dry-run passes
against the pinned GSD quiet v1 source. This is not a full ARM package build,
target asynchronous timing test, input/call qualification or autonomy result.
No new package version, installation or device setting was created.

The stable paired fix should remain installed for the planned night observation.
Only request an incremental user-run build if long-duration evidence justifies
this optimization. Removing about thirteen seconds per gauge event cannot be
assumed to remove consumption occurring during actual suspended intervals.

## Fuel-gauge interpretation

The preserved kernel source has SHA256
0f5676829cb2a40daa191a456998c700d744afe8346e07dd3c7af2a7e8685957
for drivers/power/supply/qcom/qpnp-fg-gen4.c. Its msoc-delta IRQ is wakeable.
The handler also updates temperature-dependent coefficients, capacity learning,
charge/full and ESR state, then notifies the battery power supply. Do not disable
this IRQ as an assumed equivalent of fixing desktop wake handling.

Its three exposed charge estimates are not independent physical meters:
- charge_counter: CC_SOC_SW multiplied by learned capacity, divided by 2^30-1.
- charge_counter_shadow: BATT_SOC multiplied by learned capacity, divided by 2^32-1.
- charge_now_raw: CC_SOC multiplied by nominal capacity, divided by 2^30-1.

The preserved driver defines the denominators as GENMASK(29, 0) and
GENMASK(31, 0), respectively. Learned-capacity changes can alter
two estimates without representing matching electrical consumption. Missing
readings, counter discontinuities and charge-contaminated USB return endpoints
must remain explicitly unqualified. The forthcoming collector records all three
methods alongside capacity scales and both suspend-aware and awake-only clocks.

Public downstream corroboration, not proof of byte identity with our kernel:
https://android.googlesource.com/kernel/msm/+/d57a1dd3479a3060ada2fa862b8bfab1c1d33288/drivers/power/supply/qcom/qpnp-fg-gen4.c
The search excerpt exposes the wakeable IRQ and battery notification; direct
page retrieval timed out. Local preserved source is the authoritative inspection.
