# Planned extended recovery control — 19 October 2026

Status:1800s R3 completed physically on19October2026. One/two-hour variants remain host-only validated.

## Question

Does recovery gauge behavior change with elapsed time after unplug, as the
archived full Android software counter did? The3min recovery result alone
cannot distinguish sustained residual demand from early gauge behavior.

The retained Oct16 Mobian evidence already spans10h. Qualified predominantly
suspended intervals show a stable raw nominal-scaled rate near86mA and filtered
endpoints near49-50mA, while software counter rate falls from92 to37mA across
hour bins. This is descriptive within-session accounting, not causal proof.
The earlier full Android record includes rounded software charge history but
no simultaneous raw/shadow/filtered counter series. Never compare86 raw to
11 Android software as calibrated currents.

## Control

Use the same recovery kernel and temporary policy as R2. Operator boots recovery
and confirms a1h or preferably2h availability; native Windows ADB preflight is
required again. Keep the health service running, no camera/microphone/media.
R3 accepts1800,3600 or7200 seconds only, waits for physical unplug, stabilizes20s,
then records discharging endpoints at each wake and half-hour RTC checkpoints.
The last half-hour windows matter more than the initial transition.

Like R2, it enables idle low-power mode, sets three NPU clients to powersave/zero,
and requests deep suspend. It restores the original governor/sleep settings and
clears only its own RTC alarm on normal/error exit. No firmware/partition/user
storage writes or heavy build. Fixed output is in /dev tmpfs; preserve it before
returning normally to Mobian. Operator must be available to replug at completion.
A shell trap cannot recover a kernel hang or forced process killing; do not
promise an unattended overnight run of this new extended variant.

## Analysis and decision

Record actual uptime and kernel last-suspend duration for every interval,
USBoffline/Discharging at both endpoints, raw/SW/shadow capacities and temperature.
Reject short/awake/USB/charging/clock-invalid intervals, and report coverage.
Separate filtered endpoints from integrated counter slopes. No calibration claim.

- If raw and software both decline in later recovery windows, investigate why
  the equivalent Mobian raw trace stays stable, respecting SOC/temperature.
- If software alone declines while raw remains stable, gauge-state/accounting
  differences become more likely than a proven electrical improvement.
- If all stay near the initial values, recovery still differs from the apparent
  long Android software trend; do not label a missing HAL as proven. The remaining
  decisive gap is the same raw/filtered series under full Android.

Do not repeat three-minute unplug tests or alter calibration/protection settings.
Do not reinstall Android solely because a rounded short counter differs.


## Operator availability update

The operator offers10-30 minutes now. Select1800s as an intermediate trend
control only: it can show the first half-hour raw/software/shadow trajectory
and filter response, but cannot establish the later1-2h Android regime.
Run a fresh recovery preflight first, preserving current SOC and temperature;
never describe this as a fully matched long-duration comparison. No build or
flash is needed. The phone is currently Mobian; recovery boot requires the
operator. Do not arm anything until recovery and the fresh preflight qualify.

The1800s variant uses10min checkpoints; longer variants use30min checkpoints.
