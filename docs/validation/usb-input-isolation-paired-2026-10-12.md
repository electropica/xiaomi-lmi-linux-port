# USB input isolation versus physical unplug: five-minute comparison

## Question and protocol

Can a connected data cable with charger input disabled replace a physical
unplug during standby diagnosis? Two matched five-minute observations kept
the installed RPMh kernel, suspend-only NPU policy, Phosh v2, GSD2, radio
settings and normal 900-second automatic-suspend timeout unchanged. No battery
viewer or background viewer recorder was running.

After power-state detection and 20 seconds of settling, each collector locked
the screen and verified it blank, Discharging, sufficient battery level and
no blocking sleep inhibitor. Each requested one initial suspension. The same
five-minute WakeSystem timer sampled final counters before recharging; its
one-second accuracy avoids the default broad timer-coalescing window. No
trace buffer, media capture, repeated forced suspension or new build was used.
The cable-connected case additionally armed a bounded input-restoration fallback.

## Results

| Observation | Physically unplugged | Connected data cable, input disabled |
| --- | --- | --- |
| Sample span | 301.468 s | 300.559 s |
| Actual clock-accounted sleep | 300.891 s (99.81%) | 0 s |
| USB online / present | 0 / 0 | 0 / 1 |
| input_suspend | 0 | 1 |
| USB controller runtime state at both endpoints | suspended | active |
| Software-counter estimate | 50.13 mA | 160.14 mA |
| Shadow-counter estimate | 74.89 mA | 160.15 mA |
| Raw-counter estimate | 84.25 mA | 269.13 mA |

Both endpoint pairs remained on the same boot, on battery, with unchanged
capacity scales; final samples preceded charge restoration. These are short
gauge-derived estimates, not independently calibrated electrical measurements.
The physical case's shadow result differs from its software result, so the
three methods must remain separate. The connected result is an awake-system
observation, not a second standby-current measurement or an amplifier/USB-only
power attribution.

## Why the connected case did not suspend

The kernel reports `msm-dwc3 a600000.ssusb: Abort PM suspend!! (USB is outside LPM)`
and error `-16` for that controller. Deep and subsequent s2idle attempts both
aborted. The preserved driver's system-suspend callback returns `-EBUSY` when
the controller's `in_lpm` flag is false in this device-mode path. This matches
the observed active runtime state and failed system suspension.

The first screen relight followed the failed suspension, with a recorded
WakeUpScreen signal. The end-of-test screen transitions clustered around the
input-restoration event. There was no gauge-only resume in this connected
window; do not classify these transitions as a regression of the separately
qualified quiet gauge filter.

## Decision and cleanup

Input isolation preserves a usable data path on this handset, as demonstrated
by the preceding fresh-SSH probe. It does not currently produce cable-free
standby while that USB data path remains configured. The additional whole-phone
load is associated with remaining awake; this pair cannot locate the residual
approximately 50 mA software estimate present during physical deep sleep.

The owned end and fallback timers were stopped after retrieval. Both collectors
finished; RTC state was clear, no pending NPU restoration remained, and
`input_suspend=0` plus Charging were independently verified. Existing services
remained active without restart, and no persistent power setting was changed.

An automated fixture would need to detach or suspend the data path as well,
then safely restore it. That is an unqualified future fixture, not a justification
to bypass the USB driver's busy check or call the present connected case standby.
Do not repeat this identical pair without a new hypothesis.
