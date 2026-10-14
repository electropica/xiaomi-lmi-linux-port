# Quiet-gauge validation, 12–13 October 2026

## Installed baseline and result

The persistent RPMh diagnostic kernel, suspend-only NPU hook, Phosh
`0.46.0-3+deb13u1+lmigaugewake2` and GSD `48.1-1+lmiquietgauge2` were unchanged.
Both quiet-resume opt-ins were active, debug logging was off, Wi-Fi remained
enabled and the normal automatic-suspend timeout was 900 seconds. The optional
battery viewer had been removed. A passive observer used sleep/screen callbacks
and an awake USB poll, without a wake alarm or forced suspension.

Observed unplugged duration was 31,041.226 seconds (8 h 37 min 21 s). Battery
capacity read 100% at departure and 77% at cable return; the return endpoint was
already charging and is not a pristine discharge endpoint. The boot did not
change. Clock-accounted suspension totaled 28,281.213 seconds across 42 paired
windows: 91.11% of the unplugged interval. The first automatic suspension began
915.163 seconds after observed unplug.

All 40 `438 msoc-delta` resumes started with the screen blank, kept it blank and
were followed by suspension after 15.204–15.565 seconds. This qualifies the
installed delta filter over the night; it does not establish low standby power.

One other unplugged resume reported `441 msoc-high`. A WakeUpScreen signal and
unblank followed it; blanking returned about 300 seconds later and suspension
resumed 1,200.216 seconds after that wake. Existing filters deliberately match
only `438 msoc-delta`, so this is an unhandled event rather than a failure of the
qualified delta path. It accounts for a twenty-minute awake episode, not the
entire residual drain.

Scale-stable, battery-only counter intervals covered 30,711.140 seconds.
Software/shadow/raw estimates were respectively 69.27 / 69.30 / 92.06 mA. These
include awake intervals and are differently scaled gauge estimates, not three
independent ammeters or a pure deep-suspend current measurement. Do not infer a
causal regression from a prior shorter, approximately 50 mA sleeping observation.
The observer finished successfully; RTC state was clear, the NPU restoration
state was absent and normal charging/input settings were verified after return.

## Guarded msoc-high candidate

The preserved `qpnp-fg-gen4.c` registers `msoc-high` as wakeable and directs it
to `fg_soc_irq_handler`, which logs the IRQ and returns handled. `msoc-empty`
uses a separate handler. This does not justify suppressing all fuel-gauge events
or changing thresholds/calibration.

The [candidate patches](../../userspace/power/msoc-high-resume/README.md) extend
both existing userspace guards to the exact single reason `441 msoc-high`, only
with a fresh Discharging status and a valid 30–100% capacity reading. The existing
USB, actual-sleep, lock/blank, peer opt-in and activity checks remain in place.
Low/empty, combined IRQs, unknown reasons, missing/malformed data and ordinary
user/USB/alarm wake paths fail open. Notifications and battery-protection handling
are unchanged. Neither the kernel nor its IRQ wake policy is modified.

Native tests compiled the actual candidate matchers: 20 reason/data cases through
both guards plus eight surrounding resume boundaries passed. Both normalized
patches applied to the recorded baselines and yielded the expected candidates.
Phosh's original CRLF bytes and LF-normalized identity are recorded separately;
the guarded build copies the pinned LF candidate only after validating the actual
compiled baseline bytes. GSD baseline bytes already use LF.

At the initial source publication, ARM compilation, installation and target
qualification had not been performed. The subsequent update below records the
completed build/install and normal-path smoke test. The exact msoc-high resume
remains unqualified; no saving is established yet. The intended effect is to
avoid the identified screen relight and twenty-minute awake episode.

## Build, installation and normal-path smoke update

The user completed the incremental ARM build. Source identities match the pinned
candidates; package names, versions and architectures were checked for Phosh/
common `0.46.0-3+deb13u1+lmigaugewake3` and GSD/common `48.1-1+lmiquietgauge3`.
Four qualified v2 rollback packages were verified and staged before installation.
The package simulation upgraded only these four packages and removed none.
A bounded rollback was armed before installation; existing opt-ins, the kernel
and the NPU policy remained unchanged. Both services started without restart
loops, and the user confirmed normal touch, application scrolling and power-key
behavior. The session can read the new capacity/status guard inputs.

One accepted three-minute unplugged smoke observation temporarily reduced the
automatic-suspend delay from 900 to 60 seconds, with independent restoration.
There was no forced suspension or wake alarm. Clock accounting measured
154.149 seconds of actual sleep, followed by the expected USB interrupt. The
screen was blank before suspension, all four v3 versions remained installed on
the same boot, and no pending RTC/NPU restoration or observer remained.

The normal 900-second delay was restored. Owned restart overrides and both trial
fallback timers were removed/stopped after verification; the qualified v2
rollback remains available. Charging/input settings and unchanged service PIDs
were verified. V3 is retained as a candidate for a longer natural discharge.
No msoc-high interrupt occurred during this smoke test: it does not qualify the
new high branch, prove a battery saving or solve the residual sleep drain.

## Daytime v3 qualification: 13 October

The normal-timeout passive observation ran on the same persistent kernel and
Phosh/GSD v3, with both opt-ins, debug off and Wi-Fi left enabled. No wake alarm,
forced suspension, capture or new power-policy change was introduced. The
observer was armed before departure and no phone contact occurred between the
confirmed unplug and return. Its one-hour unplug-wait limit accommodated the
planned departure; the measurement begins at observed USB loss, not arming.

The unplugged interval was 37,754.451 seconds (10 h 29 min 14 s). Reported capacity
was 100% at departure and 75% at USB return; the latter is a charging-contaminated
endpoint. Actual suspension totaled 36,089.465 seconds across 48 paired windows,
95.59% of the interval. Initial automatic sleep occurred after 911.133 seconds.

All 46 observed msoc-delta wakes stayed blank and resuspended. Crucially, one
exact `441 msoc-high` wake occurred at 80% with Discharging and USB absent. The
screen was blank before and at resume, no unblank was observed in its awake
gap, and the next suspension began 15.366929 seconds later. The prior v2 night
had the same reason at 80% followed by screen relight and 1,200.216 seconds
awake. This qualifies the guarded v3 behavior for this real noncritical case;
it does not qualify every battery level or establish a calibrated total saving.

Valid battery-only counter coverage was 37,461.874 seconds; software/shadow/raw
estimates were 59.43 / 59.42 / 88.29 mA. They include awake intervals and remain
differently scaled gauge estimates. The day and previous night are not a
controlled identical-duration electrical A/B, so do not claim their rate
difference as the isolated power saving of this filter. Residual drain is
still present despite successful suspension and the fixed screen episode.

The boot and four v3 versions were unchanged, services were active with no
restart, and analysis found no unmatched sleep window or clock warning. The
observer finished successfully; RTC state was clear and NPU restoration was
complete. Normal charging and input_suspend=0 were checked after return.
The qualified v2 rollback remains available. No new short repeat is required
merely to reproduce this already observed high-wake result.

## Separating suspended and awake counter intervals

An offline re-accounting of the same daytime evidence retained 47 adjacent
PrepareForSleep/resume endpoint pairs with USB absent, Discharging at both
endpoints, unchanged capacity scales, non-increasing counters and more than
99% of each interval accounted as suspended. These pairs cover 35,828.595
seconds, including 29.662 seconds of callback-boundary awake overhead.
The USB-return sleep window is excluded because its endpoint is charging.

| Counter method | Covered interval time | Gauge-derived average |
| --- | --- | --- |
| Software charge counter | 9 h 57 min 09 s | 56.276 mA |
| Shadow charge counter | 9 h 57 min 09 s | 55.741 mA |
| Raw charge counter | 9 h 57 min 09 s | 84.009 mA |

For comparison, the previously reported software estimate over all eligible
USB-absent intervals was 59.426 mA. The remaining counter decline is therefore
present during the suspended endpoint pairs; it cannot be attributed entirely
to the brief gauge wake gaps. This narrows the next investigation to residual
suspend consumption and gauge interpretation. It does not identify a specific
powered peripheral or independently measure electrical current.

The three counters use correlated internal gauge states and different capacity
scales. Quantization, callback overhead and undetectable internal recalibration
remain possible. Short awake gaps are unsuitable as standalone current meters.
No isolated causal saving is claimed from this re-accounting.

The next targeted observation records only RPMh commands and suspend boundaries
across real gauge resumes. Earlier complete traces qualified the initial sleep
commands but did not capture a subsequent gauge-triggered suspension. A new
result requires such a sequence, complete buffers and matched boundaries;
absent or cached commands must remain unknown rather than be called zero votes.

## Counter interpretation: source-supported correlation

Stratifying the suspended pairs by their starting reported capacity exposes
different trends. The raw estimate remains 83.90–84.18 mA across the five
bands; software and shadow estimates decrease together. These bands are
consecutive portions of one observation, not controlled comparisons.

| Starting reported capacity | Software estimate | Shadow estimate | Raw estimate |
| --- | --- | --- | --- |
| 95–100% | 87.31 mA | 84.69 mA | 83.91 mA |
| 90–94% | 76.15 mA | 75.31 mA | 83.96 mA |
| 85–89% | 61.63 mA | 61.16 mA | 83.90 mA |
| 80–84% | 48.16 mA | 47.96 mA | 83.97 mA |
| 75–79% | 38.25 mA | 38.23 mA | 84.18 mA |

The retained `fg-alg.c` is byte-identical to the
[pinned LineageOS source](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/71b13e62f057a649b77fe4062feb73ee72ad609c/drivers/power/supply/qcom/fg-alg.c),
SHA-256 `436db2892f19c0055bcb1f21916bbfe3bbcdb9429db694aad0cabbb4c79166f1`.
Its `cap_learning_update()` can prime `CC_SOC_SW` from `BATT_SOC` when learning
is inactive and the battery is Discharging. The FG driver's status-change work
calls that function; its priming callback writes `CC_SOC_SW`. Software charge
uses that value and learned capacity, whereas shadow charge uses `BATT_SOC`
and learned capacity. Raw charge uses `CC_SOC` and nominal capacity.

This supplies a source-supported correlation mechanism; execution of that
branch at each observed wake was not traced. It neither explains every change
nor establishes an electrical current calibration. A falling software/shadow
estimate must not be presented as a power-policy improvement by itself. No
gauge state, capacity learning, battery profile or protection was modified.

## Targeted power traces: scope and charge-pump ADC

The initial thirty-minute RPMh capture overflowed during its initial awake
period. The whole capture remains unqualified. A separate retained-suffix
review found that overwritten CPU buffer prefixes end at least 352.89 seconds
before the selected machine-suspend windows. All eight CPU buffers have zero
commit overruns, dropped events and consumed records; retained timestamps are
monotonic. Thirteen boundary cases reject loss reaching the selected interval
or incomplete buffer evidence. This qualifies only the selected suffix.

One retained IRQ438-following sleep interval lasted 635.277 seconds by separate
BOOTTIME-minus-MONOTONIC accounting. No valid nonzero BCM sleep-bank command
was observed there. This describes emitted commands, not cached requests,
other masters, unobserved resources or physical rail current. A subsequent
gated capture had no loss but observed no gauge wake, so it does not qualify
the missing target sequence.

A separate filtered SMBus capture observed only the charge-pump driver's
existing transactions on adapter 5, address 0x66, register 0x14. The collector
initiated no device transactions or register writes. The complete trace has
no buffer loss, and its strict transaction parser passes eight boundary cases.

| Driver phase | Transaction | Value | Bus result |
| --- | --- | --- | --- |
| Before suspend | Read | 0xa8 | 0 |
| Before suspend | Write | 0x28 | 0 |
| Resume, before enabling ADC | Read | 0x28 | 0 |
| Resume | Write | 0xa8 | 0 |

Bit 7 is the ADC-enable control. The successful clear and subsequent readback
show that the ADC control was off across the observed 325.036-second sleep
window, then enabled again on resume. This rules out a failed ADC-disable
command for this interval; it neither identifies the exact silicon variant
nor measures analog current or establishes a battery saving. No charger,
calibration or protection setting was changed. The normal fifteen-minute
idle timeout was restored, owned observers and trace instances were cleaned
up, and no test alarm remained.

## Auxiliary peripheral review

The bound Goodix device is a platform device, not SPI0.0; SPI0.0 is the IR
transmitter. The selected kernel configuration builds `GOODIX_FOD`. Its
header leaves `AP_CONTROL_CLK` disabled. Probe creates the device and reads
GPIO numbers without driving its power GPIO. Open and ioctl paths manage
GPIO requests and power separately. A bounded, completed descriptor scan
found no process holding the Goodix device at the inspected plugged state.
This does not establish its initial pin level or physical sleep current;
no device node was opened, ioctl issued, GPIO driven or driver unbound.

The retained IR driver acquires its regulator at probe without enabling it;
transmission enables it around the SPI transfer and then disables it, including
transfer failures. A missing runtime-PM status is not proof of continuous
power. No IR transmission was requested.

The official October 7 LineageOS package contains twelve device overlays.
The overlay identified by its model as Xiaomi lmi is entry 7, SHA-256
`019bd837d01396d86dcecc65a39c6591fc0ceeb6aa5ef98cc7374cc6248c7466`.
Its Goodix GPIO arguments match the retained Mobian runtime tree. All 22
shared named regulator nodes have matching observed `regulator-always-on`
and `regulator-boot-on` flags. This is a package-overlay comparison, not a
reconstruction of Android's final merged runtime tree or an electrical
measurement. It supplies no basis for removing shared-rail constraints.

## Overnight reproduction, October 13–14

A passive observation used the installed v3 Phosh/GSD pair, normal fifteen-minute
battery idle timeout, unchanged Wi-Fi-enabled state, persistent diagnostic kernel
and NPU suspend correction. No host contact, alarm, forced suspension, trace or
media capture occurred during the cable-free interval.

The interval lasted 36,617.592 seconds (10 h 10 min 18 s). Clock accounting
records 34,947.595 seconds of suspension, 95.44% of the interval. Displayed
capacity was 100% at departure and 76% at charging return; the latter is not a
pure discharge endpoint. Same boot and exact package versions were confirmed.
Both userspace units remained active with zero restarts and debug disabled.

All 47 observed eligible gauge resumes remained blank and resuspended after
15.206–15.424 seconds: 46 exact IRQ438 delta events and one exact IRQ441 high
at 80%, Discharging, USB absent. USB IRQ502 was excluded from this qualification.
This reproduces the userspace wake handling, not a new electrical saving.

Separately, 46 adjacent USB-absent, Discharging suspend-boundary pairs cover
34,181.090 seconds, including 34,151.963 seconds of actual sleep. With unchanged
capacity scales and non-increasing counters, modeled averages are 58.85 mA
software, 58.29 mA shadow and 84.30 mA raw. The prior daytime raw estimate was
84.01 mA. These methods are differently scaled, software/shadow can be correlated,
and neither comparison is a calibrated physical-current measurement. Residual
counter decline persists during real suspension; brief visible wakes do not
explain it by themselves.

The passive collector finished successfully and is inactive. RTC is empty,
NPU recovery state absent, no trace instance remains, charging is restored and
the normal idle timeout remains 900 seconds.

A subsequent metadata-only TLMM read found the Goodix power pin27, reset pin26
and IRQ pin23 in GPIO function0, input, low, with pull-down. There is no observed
high power-enable drive at this plugged snapshot. Input level is not an analog
rail measurement or a capture of the entire preceding sleep interval. No GPIO
was requested or driven, and no fingerprint node was opened. No forced power
change is justified by this finding.

## Targeted peripheral and firmware follow-up, October 14

A read-only camera wiring review mapped six described sensor nodes to ten
unique TLMM clock/reset pins and thirteen named supplies/domains. At the
inspected plugged idle state, all ten pins were GPIO inputs, low, pull-down;
all thirteen supplies/domains reported disabled and zero users. This provides
no observed high output backfeeding those mapped pins. It is not a definitive
exclusion during every sleep interval, nor an analog leakage measurement.
No camera was opened and no regulator or GPIO was written.

The actual regulator summary distinguishes `use` from `open`: an acquired
consumer handle is not necessarily an enable request. Configured voltages
and zero reported current must not be treated as measured output voltage or
zero physical draw. Prior retained sleep traces already show L5/L6 low-power
mode requests and L17 disable; a plugged snapshot cannot replace those traces.

The generic power-domain summary exposes only the MDP display domain,
reported off-0. It contains no SLPI/SSC domain. The proposed qcom_ssc, ssc and
slpi debugfs directories and the two checked master-stats filenames are absent.
This does not prove missing power management or a powered-off sensor island.
The retained sensors_ssc.c provides a boot_slpi sysfs loader with write-only
boot/SSR controls, not the suggested debugfs client-vote list. Probe initializes
its firmware ownership pointer to NULL; source alone does not establish live
ownership. No boot/SSR control was read as a status value or written.

The firmware sleep snapshot correlates with the final overnight interval:
Linux accounts 774.125 seconds asleep; aosd, cxsd and ddr each report a last
mode duration of 774 seconds, with matching time since exit. The source
truncates seconds before converting to milliseconds. Its misleadingly named
`actual last sleep` field is accumulated residency, not that last duration.
This confirms temporal agreement for that window, not rail current or an
across-night before/after count delta. Existing GPIO, radio, audio and supply
constraints must not be changed merely because a generic checklist expects
every non-CPU domain to be off.

## CNSS/MHI DRV interpretation and additional camera pins

The retained CNSS driver selects MSM_PCIE_DRV_SUSPEND when DRV is connected,
uses mhi_pm_fast_suspend(), and deliberately skips the ordinary PCI_D3hot path.
The MHI function places host PM in M3 and device state in M3_FAST. Requiring
ordinary device M3 or D3hot would therefore misclassify this supported path.

The PCIe DRV controller waits for RPMSG acknowledgement before changing to
its DRV link state, disabling non-suppressible local clocks, removing its bus
vote and releasing regulator requests. Its ACK callback checks payload size,
reply sequence and a zero status before completing the request. This source
review does not prove every physical rail transition succeeded.

The audited MHI states reader reports cached software fields only. A plugged
idle snapshot shows pm_state M3, dev_state M3_FAST, zero wake request, zero
device wake and zero pending packets; the Wi-Fi PCIe endpoint is runtime
suspended. Its cumulative M3_Fast count is not a measured overnight delta.
The root bridge's runtime-active flag alone is not proof that DRV-managed
hardware stays electrically awake during system suspension. No PCI config,
register dump, reset, state-trigger or vote interface was used.

The existing NPU-active radio isolation already estimated 50.150 mA with
Wi-Fi stopped versus 49.593 mA in its preceding enabled-radio interval,
with the five reviewed radio supply/domain use counts at zero. This was a
short sequential gauge comparison, not a calibrated association/traffic or
long-duration control. It provides no new justification to repeat identical
radio-off tests merely because the latest long baseline kept Wi-Fi enabled.

The additional eight CCI camera bus pins101–108 are also GPIO inputs, low,
pull-down in the subsequent plugged idle snapshot. Together with the ten
previously mapped clock/reset pins, no high drive was observed on these
selected camera lines. This remains a bounded idle check, not a definitive
asleep leakage exclusion. No GPIO or camera state was changed.

## Charge-pump conversion versus ADC enable

Reanalysis of the retained successful register reads distinguishes charge-pump
conversion from ADC sampling. Register 0x0c was 0x07, with CHG_EN (bit7) clear;
register 0x0a was 0x20, with CONV_SWITCHING_STAT (bit2) clear. A retained
resume-side converter-status log also reported 0x00. The driver skip-read and
skip-write controls were zero. These are plugged idle and resume observations,
not continuous conversion telemetry throughout suspension.

The retained device-ID byte 0x10 matches the locked header's named BQ25970 ID
and selects its driver family. The selector also has a fallback branch, so
the generic driver name alone should not be used as silicon identification.
The separate filtered suspend trace already establishes ADC disable for its
qualified sleep interval. Neither observation measures quiescent electrical
current or warrants disabling charger protection or repeating the same ADC
experiment. No additional hardware register read or write was performed for
this reanalysis; whole-register dumps can consume diagnostic flag state.

## Popup motor and codec supply policy review

The retained runtime tree maps the DRV8846 motor power-enable signal to TLMM
GPIO153. Its suspend callback returns gpio_direction_output(power_enable, 0);
resume restores it to 1. The retained wide transition trace contains the bus
suspend and resume callbacks with err=0. This confirms the software command
path, not the motor rail's measured voltage or residual electrical current.
No motor operation, GPIO write or device unbind was performed in this review.

The WCD938x supply helper reduces requested regulator load only for supplies
marked qcom,<supply>-lpm-supported. Those properties are absent from the
retained Mobian runtime node. The lmi LineageOS package overlay has the same
four static supply names, voltage constraints and requested loads, and also
omits these properties. The overlay comparison is not a final merged Android
runtime comparison. The 30000/30000/650000/30000 uA values are regulator load
requests, not measured battery consumption, and do not establish a Mobian
specific fault or justify transplanting a low-power flag without validation.

A subsequent plugged idle read of the audited DAPM bias-level memory readers
reports WCD938x and TFA bias Off; all 38 component contexts read are Off, with
the card context itself Standby. The card aggregate alone is not an active
codec or microphone indication. The existing trace also contains a successful
WCD938x late-suspend callback, but its return value does not establish the
conditional supply helper's execution or a physical regulator mode change.
No audio playback, microphone recording, widget connection callback or codec
register dump was used. Residual sleep consumption remains unresolved.

## Shared supply requests and cache validity

The retained trial36 diagnostic snapshots include 47 aggregate regulator
resources, with separate computed/cached active and sleep requests and validity
masks. The locked driver takes the maximum of client requests assigned to each
set. It does not send a separate sleep request until valid sleep parameters
differ from active parameters. A zero cached sleep value with its validity bit
clear therefore cannot be interpreted as a regulator-disable request.

The shared S4 resource (smpa4), supplying several codec inputs and other
consumers, has no supported-mode table in the retained runtime tree. The locked
regulator driver disables its set_mode/set_load operations when that table is
absent. Merely adding codec lpm-supported properties would not provide the
assumed mode-switch operation for those S4-backed supplies. No such patch or
new build is justified by this review.

The BOB resource (bobc1) does have mode controls. Its retained computed and
valid cached sleep mode is 2, which the PMIC5 BOB mapping defines as bypass;
the active aggregate mode is 6 (auto). The complete trial36 trace contains
sleep-bank BOB mode commands carrying 2. This software evidence already
distinguishes the sleep policy from the active policy; it does not measure
physical rail current or every other master's request. The pre-suspend S4
enable request remains valid and enabled, but that snapshot precedes device
callbacks and does not by itself identify an unnecessary consumer in sleep.
No new phone access, regulator write or physical test was performed.

## Reconstructed Lineage base-plus-overlay power configuration

To remove the earlier overlay-only limitation, the existing Lineage boot DTB
section and the lmi package overlay were pinned to their previously retained
hashes and merged in memory using libfdt. All three base candidates merged
successfully; the Kona v2.1 candidate's msm-id matches the retained Mobian
runtime property. No image was produced and no handset access was required.

All 106 named regulators are present on both sides. The 374 compared explicit
properties match in every candidate: regulator constraints/flags, selected
initial vote fields and aggregate mode tables/thresholds. This is a bounded
property comparison, not a proof that every regulator driver, consumer vote
or physical rail behaves identically under both operating systems.

The 977 comparable pin-configuration nodes have only two differences: the
WCD938x reset active/sleep mux functions are gpio under the retained Mobian
diagnostic tree and func2 in the reconstructed Lineage trees. These are the
known reset-pinmux adaptation used for audio bring-up, not a newly discovered
unrelated pin bias difference. The codec reset helper uses the sleep/active
states to drive reset low/high; an identically named sleep state must not be
assumed to be selected on every system suspension. The working audio patch
was not reverted. Actual Android bootloader selection/later fixups and live
electrical behavior remain outside this reconstruction.
