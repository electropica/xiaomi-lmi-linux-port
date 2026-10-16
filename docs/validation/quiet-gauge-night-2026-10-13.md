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

## Daytime return — 2026-10-14

The explicitly requested passive daytime repeat retained the same v3 pair,
permanent NPU suspend correction, enabled Wi-Fi and normal 15-minute automatic
suspend policy. The unplugged interval lasted 40,043.574 seconds (11h07m24s),
including 38,443.596 seconds of clock-accounted suspension: 96.00%. Displayed
capacity went from 100% to 77% at the charging-contaminated USB return.

All 43 eligible wakes were exact msoc-delta events. The observer recorded no
screen unblank during their quiet intervals; each returned to suspension after
15.186–15.409 seconds. The final USB wake was excluded. Same-boot, package and
service qualification passed with no analysis warnings. The observer completed
successfully; normal timeout, charging, empty RTC alarm, absent NPU recovery
state and no trace instance were checked after retrieval.

Forty-two isolated prepare/resume counter intervals covered 37,275.630 seconds,
of which 37,249.322 seconds were actual suspension. Counter-derived averages
were 48.960 mA (software), 48.784 mA (shadow) and 85.113 mA (raw nominal scale).
These remain distinct correlated gauge estimates, not calibrated meters.
The raw estimate is consistent with the preceding night/day sleep intervals;
this repeat establishes no new saving or regression.

Failed automatic suspension and screen relighting are no longer the primary
explanation being investigated for this qualified baseline. Residual drain
persists during actual suspension. Further work should distinguish peripheral
and other-master power requests from gauge behavior, rather than repeat the
same screen/suspend timing tests without a new causal hypothesis. CPU sleep
residency does not itself prove all peripheral rails are electrically quiet.

## Retained master residency and counter-scale audit — 2026-10-14

This is an offline analysis of retained evidence, not a new handset test,
power-policy change or battery fix.

### Master statistics: distinguish displayed and stored accumulation

In the retained `drivers/soc/qcom/rpmh_master_stat.c`,
`msm_rpmh_master_stats_print_data()` already adds the current architectural
counter minus `last_entered` when `last_entered > last_exited`. The printed
`Sleep Accumulated Duration` therefore includes an ongoing sleep. Adding that
contribution again to the retained text would double-count it.

An older 12-minute observation contains a before/after master pair. At the
19.2 MHz frequency used by retained `rpm_stats.c`, its displayed deltas give:

| Quantity | Retained interval |
| --- | --- |
| Linux elapsed time | 721.244462 s |
| Linux suspended time | 720.546600 s |
| APSS accumulated-duration delta | 720.555921 s, about 99.905% of elapsed time |
| ADSP accumulated-duration delta | 721.270771 s, approximately the full interval |

The APSS result agrees with Linux sleep within about 9.3 ms. ADSP exceeds the
separately recorded elapsed time by about 26 ms; clocks and master reads are
sequential rather than atomic. This is not evidence of more than 100% physical
residency. No fresh architectural-frequency read was performed.

APSS duration/count updates are accepted only when the power-profile validity
bits used by `msm_rpmh_master_stats_update()` are set; the source describes the
rejected case as a sequence that did not execute cx-off. The APSS sleep-count
delta is not a count of Linux system-suspend cycles. The observations support
APSS collapse and ADSP-reported sleep over this older interval. They do not
prove all retained votes, shared supplies or other masters are off. The
October 14 full-day observation did not retain these master snapshots and
must not inherit this interval's coverage.

### Counter scaling: a numerical discrepancy is not extra electrical leakage

The October 14 records consistently report learned capacity of 2,747,000 uAh
and `charge_full_design` of 4,700,000 uAh. Over the selected suspended pairs,
software/raw charge deltas have ratio 506946/881289 = 0.5752324, while the
reported capacity ratio is 2747/4700 = 0.5844681.

Numerically rescaling the 85.112991 mA raw estimate by that reported capacity
ratio gives 49.745827 mA, close to the 48.959751 mA software estimate. This
illustrates why their roughly 36 mA difference must not be interpreted as an
additional physical load. It does not establish either estimate as calibrated
current, prove battery degradation, or explain the residual discharge.

There is a further source boundary: `fg_gen4_get_charge_raw()` calls
`fg_gen4_get_nominal_capacity()`, which reads the nominal-capacity SRAM word.
`POWER_SUPPLY_PROP_CHARGE_FULL_DESIGN` can instead return the battery profile's
`qcom,nom-batt-capacity-mah` value, falling back to the SRAM getter only when
that profile value is unavailable. Thus `charge_full_design` is not guaranteed
to be the exact nominal scale used by every raw read. The numerical rescaling
above is illustrative, not an exact reconstruction of internal counter state.
Reported capacity stability does not by itself qualify all internal scales.

The learning code can prime `CC_SOC_SW` from `BATT_SOC`; its execution at each
gauge wake has not been traced. Successful priming logs through
`fg_dbg(..., FG_STATUS, ...)`; absence of that message in an unqualified log
does not demonstrate absence of priming. No learning, calibration, charge
protection or SRAM state was changed for this analysis.

The next evidence requirement is a qualified distinction between internal
gauge normalization and retained peripheral demand, not another identical
automatic-suspend test. These findings alone do not justify a new kernel,
arbitrary resource shutdown or an assertion that the physical battery is good
or bad.

### Fixed scaling does not explain the complete discharge trajectory

The October 14 suspended pairs were also partitioned by departure charge
level. All five groups have the same reported learned/design capacities,
2,747/4,700 mAh:

| Departure charge | Pairs | Software estimate | Raw estimate |
| --- | --- | --- | --- |
| 95–100% | 6 | 72.64 mA | 84.81 mA |
| 90–94% | 11 | 63.58 mA | 84.86 mA |
| 85–89% | 10 | 49.75 mA | 84.93 mA |
| 80–84% | 11 | 38.87 mA | 85.26 mA |
| 75–79% | 4 | 33.90 mA | 85.66 mA |

These are consecutive parts of one observation, not controlled comparisons.
The changing software/raw ratio cannot be explained by the fixed reported
capacity ratio alone. The close agreement of the rescaled whole-period
average is therefore insufficient to identify the mechanism. Distinct SOC
states, priming, relaxation and unobserved internal changes remain relevant;
none is established as the sole cause by this partition. No physical power
improvement or battery-health conclusion follows.

The source path from `fg_delta_msoc_irq_handler()` through the battery
power-supply notification and `fg_notifier_cb()` can schedule
`status_change_work()`. Learning/priming remains conditional, with early
returns, coalesced work and write failures possible. This path is not proof
that every recorded wake performed a successful priming write.

### Runtime priming at cable transitions — 2026-10-14

A short attended diagnostic temporarily enabled only the FG_STATUS logging
bit through the existing FG debug mask. The kernel's successful-write log
recorded three identical `CC_SOC_SW` priming writes in a context immediately
followed by Discharging status at cable removal. With the recorded learned
capacity, that written value reconstructs 2,623,277 uAh, exactly the first
observed software counter in the discharging transition. One further priming
write was followed by Charging status at reconnection.

This is positive runtime evidence of priming at cable transitions, rather
than merely a possible branch in source code. It does not establish a
one-to-one relationship with gauge IRQs. Driver work and the observer's USB
poll are not synchronized; a physical reconnect can already appear in a
resume callback before the later `replugged` poll event. A poll-defined
interval alone must not classify a kernel write as cable-absent.

Clock accounting records 318.008 s of actual sleep within a 318.641 s
prepare/resume window. The only resume was the final USB wake; no natural
MSOC-delta wake occurred. Its resume endpoint was already USB-present and
Not charging, so no qualified discharge-current average is derived from
this sleep window. The filtered current at return also cannot be treated
as an independent in-sleep measurement.

The observer completed successfully, its restoration record passed, and the
FG debug mask returned to zero. The normal 900-second idle policy, radios,
governors, charge protections and capacity learning were unchanged. One
initial suspend was requested; no RTC alarm or media capture was added.
The next natural gauge-wake case remains unobserved by this diagnostic;
absence of such a wake in five minutes is not evidence of absent priming.

### Bounding the software-versus-shadow mismatch

An offline review of the 14 October daytime observation retained 90 snapshots
with USB absent and battery status Discharging. Between the first and last
such snapshots, charge_counter fell by 562,563 uAh, charge_counter_shadow by
562,552 uAh and charge_now_raw by 962,582 uAh. The software-versus-shadow
endpoint difference is therefore 11 uAh, whereas the raw-versus-software
endpoint difference is 400,019 uAh.

Across those snapshots, software minus shadow ranged from -264 to +2,822 uAh.
For the 42 previously qualified sleep pairs, the cumulative decreases were
506,946 uAh software, 505,124 uAh shadow and 881,289 uAh raw. Across the 43
adjacent gauge-wake grace intervals, they were 23,477, 25,304 and 39,731 uAh,
respectively. These phase selections do not cover every part of the day and
must not be added as if they were a complete cable-to-cable record.

A mismatch affecting only the software counter relative to shadow cannot
numerically explain the much larger raw gap in this retained interval.
However, shadow is BATT_SOC scaled by learned capacity, not an independent
physical current meter. Agreement between software and shadow neither
calibrates raw nor excludes a common hardware/model effect. The sysfs reads
were sequential; these endpoints are recorded snapshots, not exact cable
transition times. This uninstrumented observation does not establish whether
priming executed at each natural gauge wake.

### First natural gauge wake: bounded runtime diagnostic

A subsequent observation left the normal 900-second battery idle timeout
unchanged and made no explicit suspend request. FG_STATUS logging was enabled
only until the first exact IRQ 438 msoc-delta resume, then restored three
seconds later while USB was still absent. The unit exited successfully and
the return check confirmed debug_mask=0 and completed recovery.

The observed prepare/resume window was 440.149 seconds, including 439.507
seconds actually suspended. Fourteen successful priming messages were retained
in the diagnostic window, including cable departure and ordinary awake work;
they are not fourteen gauge wakes. One successful write of CC_SOC_SW appears
in the natural resume transition, after the prepare record and before the
userspace resume callback. The callback reported USB absent and the exact
msoc-delta reason. This is positive evidence of priming in that observed wake
context, not proof of one write at every wake in earlier nights.

Logging ended before cable return. These diagnostic samples do not qualify a
new standby-current average or demonstrate a physical power saving. Together
with the bounded software/shadow comparison, they support treating priming as
part of the counter model rather than assuming that it alone explains the
entire raw-counter gap. No profile, learned-capacity or protection value was
changed, and no new kernel was built or flashed.

### Quiet overnight follow-up, 14–15 October 2026

The passive overnight observation retained the same boot and qualified v3
userspace baseline, with Wi-Fi left enabled and normal 900-second idle timeout.
The poll-observed USB-absent interval lasted 33,445.869 seconds (9 h 17 min),
including 31,870.854 seconds actually suspended (95.29%). Displayed capacity
was 100% at the departure poll and 79% at the charging return poll; the latter
is not an exact pre-charge endpoint.

All 40 exact IRQ 438 msoc-delta resumes remained screen-blank and returned to
suspend after 15.185–15.425 seconds. The observer exited successfully; RTC
wakealarm was empty and no NPU recovery state remained. No accounting warnings
or reboot occurred.

Forty-one qualifying adjacent sleep pairs covered 31,788.827 seconds. Their
counter-derived averages were 54.134 mA software, 53.580 mA shadow and 85.523 mA
raw, with reported learned capacity fixed at 2,738 mAh. These differently scaled
counter estimates are not calibrated current measurements. The raw estimate
remains close to the previous day's 85.113 mA; no new saving or causal fix is
demonstrated. Stable blank-screen resuspension does not establish that every
peripheral rail is electrically off. No new power setting was installed.


### Manual-off boundary pair, 15 October 2026

The one-shot recorder captured an unplugged shutdown endpoint and an unplugged
startup endpoint on a different boot, using the same installed October 7 kernel.
The startup snapshot was taken 8.383 seconds after kernel startup. Both endpoints
reported Discharging and 92% capacity. Learned and design capacities remained
2738 and 4700 mAh respectively. The software, shadow and raw counter decreases
were 1952, 1745 and 3000 microamp-hours, including shutdown and startup energy.

Qualification failed because the system wall clock advanced only 4.215 seconds,
whereas the hardware RTC advanced 2176 seconds (36 minutes 16 seconds). This is
evidence of a boot/timekeeping discontinuity; the specific cause is not yet
established. The original strict analyzer rejects the pair and reports no rate.
The small recorded counter changes are worth retaining, but are not a calibrated
powered-off current measurement, a battery-health verdict, or proof of a hardware
leak. Boot overhead and possible gauge-model initialization remain limitations.

The bounded startup kernel log reports a battery-profile verification retry.
It does not establish a completed profile reload, integrator reset, or the cause
of the clock discontinuity. Those must not be inferred from this message alone.

After retrieval, the temporary one-shot service was disabled and its verified
script and unit removed. The private boundary records were retained. Charging
resumed, the RTC wakealarm was empty and the fuel-gauge debug mask remained zero.


### Passive daytime follow-up, 15 October 2026

The unchanged installed v3 userspace and October 7 diagnostic kernel completed
a same-boot daytime observation with Wi-Fi enabled and the normal 900-second
automatic-suspend timeout. Cable polling covered 45536.603 seconds (12 h 38 min
57 s); clock accounting recorded 43911.599 seconds suspended, or 96.431%.
Displayed capacity was 94% at the unplug observation and 71% at the charging
return observation. The latter is not an exact pre-charge endpoint.

All 44 exact IRQ 438 msoc-delta callbacks kept the screen blank and were followed
by suspension after 15.361–15.582 seconds. One IRQ 441 msoc-high callback also
kept the screen blank and was followed by suspension after approximately 15.38
seconds. The cable-return wake was a typec-cc-state-change event. No unsolicited
screen unblank is established by these recorded gauge callbacks.

Across 45 eligible adjacent suspend/resume boundary pairs covering 43349.206
seconds, software, shadow and raw counter-derived estimates were 42.040, 41.740
and 85.529 mA respectively. Learned capacity remained 2738 mAh. These differently
scaled, correlated gauge estimates are not independently calibrated current.
The raw estimate is effectively unchanged from the preceding overnight value
of 85.523 mA; the lower software estimate does not establish a new power saving.
The high suspend fraction and quiet gauge handling remain confirmed, while the
remaining battery loss is unresolved. No new power-policy change was tested.

The observer ended successfully and was inactive at retrieval. Charging resumed;
the normal timeout was still 900 seconds, input_suspend was zero, and no trace
instance, RTC alarm or pending NPU recovery state remained. Private logs and
device identifiers were excluded from this public note.


### Boot clock and profile retry follow-up, 15 October 2026

A later read of the same boot shows battery authentication succeeding at
6.764 seconds after the initial profile lookup/retry at 6.742 seconds. At
7.286 seconds the driver found j11sun_4700mah, which is also the currently
exposed battery type. The retained source schedules a retry while verification
data is unavailable. These messages do not establish a persistent verification
loop or justify replacing the battery profile. Finding a profile is not by
itself proof that its SRAM contents were reloaded.

The live system wall clock was approximately 2175 seconds behind the host,
consistent with the earlier manual-off RTC/wall discrepancy. The RTC reports
hctosys=1, while its raw epoch is not Unix-aligned on this platform; timesyncd
was active but not synchronized. A saved clock floor existed. The data establish
a failed elapsed-time restoration across that restart, without identifying the
complete boot-time adjustment chain. No RTC write or battery calibration was
performed. The system wall clock alone was resynchronized to the host through
a ready/response handshake (24 ms response interval). This is a one-time clock
correction, not a persistent boot-clock fix. The original strict rejection of
the manual-off rate remains intact.

Same-boot boottime/monotonic accounting of the preceding daytime observation
is independent of this wall-clock correction. Neither the clock issue nor the
transient profile retry demonstrates a cause of its residual suspended drain.


### Gauge-output consistency controls, 15 October 2026

Two bounded awake observations compared trapezoidal integration of BMS
current_now samples with counter changes. Each observation used 61 samples
spaced two seconds apart over 120 seconds. Status, USB state, counter direction
and reported capacity scales remained consistent within each observation.
The discharge run held a temporary sleep/idle inhibitor; boottime and monotonic
durations agreed within 5 microseconds. The inhibitor was released automatically,
the observer ended successfully, and normal charging and the 900-second timeout
were verified afterwards. No supply, governor, calibration or protection setting
was written; no audio or video was captured.

| Awake condition | Integrated current_now | Software delta | Shadow delta | Raw delta |
| --- | ---: | ---: | ---: | ---: |
| Normal USB charging | 22.517 mAh gained | 23.091 mAh | 25.371 mAh | 39.696 mAh |
| Unplugged discharge | 3.113 mAh lost | 3.142 mAh | 3.974 mAh | 5.413 mAh |

Software/integral ratios were 1.025 and 1.009; raw/integral ratios were 1.763
and 1.739. Reported design/learned ratios were 1.717 and 1.720 respectively.
Learned capacity was 2738 mAh in the charging run and 2733 mAh in the later
discharge run, with no change inside either run. This supports a substantial
scaling discrepancy when interpreting the raw getter as electrical charge.
It does not prove the hardware integrator's normalization contract. Current
and counters are correlated outputs of the same gauge, sample integration can
miss fast variations, and these active observations do not calibrate suspended
current. Do not directly call an 85 mA raw-derived quotient 85 mA physical drain,
or silently replace it with an assumed capacity-rescaled physical value.

An offline comparison of three retained long observations also finds a repeated
SOC association: software estimates fall from approximately 73–76 mA in the
95–100% band to approximately 31–38 mA in the lower observed bands, whereas raw
estimates remain approximately 84.8–86.0 mA. These are consecutive, correlated
intervals with temperature/voltage and initial-state differences, not randomized
comparisons. A lower software-only estimate on a later day is insufficient
evidence of a new policy saving.

This does not erase the previous NPU result. A fresh offline qualification of
the retained first-sleep segments of trials 29 and 30 finds 100% displayed SOC
at both endpoints in both segments, unchanged learned/design capacities of
2806/4700 mAh, USB absent and Discharging, and over 99.6% suspension. Raw-derived
rates were 83.957 mA with the correction versus 145.143 mA with the original
policy; software and shadow methods also fell (approximately 39–42%). Segment
lengths differed (449 versus 210 seconds) and order was not randomized. Trial30
later aborted, so it must not be called a complete matched twelve-minute trial.
Together with the earlier immediate counter-check, the retained segments support
the NPU policy lead without constituting independent ammeter calibration.

The retained Gen4 implementation exposes current_avg by reading FG_SRAM_IBAT_FLT,
rather than calculating an application-level average. A short plugged read
confirmed a changing, lagging value, distinct from current_now. Its exact filter
time constant remains unestablished. The next long passive observer is prepared
to add current_avg only at existing events; it is not yet armed and introduces
no additional periodic wakeup. A short post-charge observation of this filtered
field must not be assumed to represent settled suspend current.

### Event-only filtered-current observation, 15 October 2026

A passive observation added BMS `current_avg` (`FG_SRAM_IBAT_FLT`) to the
existing unplug, suspend and resume records. It introduced no periodic wake,
RTC alarm, forced suspension or power-policy change. The normal 900-second
automatic suspend delay remained enabled.

The observed unplug interval was 1,877.9 seconds, including 942.9 seconds
actually suspended. Initial automatic suspension occurred after 914.1 seconds;
therefore the whole-run sleep fraction must not be compared directly with a
long night dominated by suspension. One natural `msoc-delta` wake occurred:
the screen remained blank and suspension resumed after 15.22 seconds.

For the one qualified cable-free sleep pair (390.79 seconds, with only 0.59
seconds awake at its boundaries), filtered current changed from 76.173 mA
before suspension to 55.212 mA at the natural wake. Instantaneous current at
that wake was 48.339 mA. Counter-derived estimates over this same interval
were 67.21 mA (software), 59.11 mA (shadow), and 85.99 mA (raw getter).
The learned capacity remained 2,733 mAh.

These are correlated gauge outputs, not independent electrical measurements.
The filtered-current time constant and its remaining charging-history memory
are not established; its endpoint is not an interval integral. The second
sleep interval ended with cable insertion and is excluded from cable-free
current comparisons. This observation does not establish a new power saving
or identify a consuming peripheral.

The observer finished successfully on the same boot. Charging resumed,
`input_suspend` was zero, the normal suspend delay remained 900 seconds,
and no trace instance, RTC alarm or pending NPU restoration state remained.

### External-modem state-label limitation

A separate read-only check confirmed that the modem-specific PMIC PON node
is bound to its expected driver and is distinct from the system-reset node.
The retained ESOC IPC log contains initialization and registration entries,
without a recorded power-down operation. Log absence alone cannot establish
the electrical state of the external modem.

Source inspection also shows that the SDX55 `power_down` implementation,
registered as the `poff_force` operation, uses a warm reset. This is distinct
from the normal `ESOC_PWR_OFF` path, which can request a firmware shutdown via
sysmon or a userspace handler. It must not be described as proof that every
graceful shutdown is merely a reset. The retained modem DT does not select
the userspace shutdown handler; its `qcom,pil-force-shutdown` flag bypasses
one generic SSR sysmon stage, rather than proving a physical shutdown at probe.
The ESOC probe initially assigns `PWR_OFF` without issuing a physical power-down
command in that probe, and the non-forced shutdown callback returns early when
that state is already recorded. Thus a nominal off request can be a no-op;
neither its success nor the initial state label establishes electrical shutdown.
The reviewed ESOC/PON files are byte-identical to the corresponding LineageOS
source at commit `71b13e62f057a649b77fe4062feb73ee72ad609c`; no source-difference
fix was identified. No PMIC API, register write, GPIO change or modem power
experiment was performed. This remains an unproven lead, not an identified
cause of the standby drain.

### Instantaneous-current endpoints across existing observations

An offline audit selected 129 existing natural gauge-wake pairs across three
long observations and the filtered-current observation above. Each pair had
USB absent, the screen blank at both boundaries, at least 120 seconds elapsed,
more than 99% actual suspension, and valid unchanged-capacity counter results.
No new phone collection or setting change was required.

The BMS instantaneous-current readings at these resume callbacks range from
47.851 to 51.757 mA. Per-session, five-percentage-point SOC-band medians range
from 48.339 to 50.292 mA. These endpoint readings remain comparatively stable
while software-counter interval estimates vary markedly with SOC: for example,
the retained daytime observation spans approximately 72.64 to 33.90 mA in its
software-counter bands, versus 84.81 to 85.66 mA using the raw getter.

This is additional evidence against treating a falling software-counter rate
alone as a demonstrated power saving. It does not prove that current remained
near 50 mA throughout each suspension interval: samples are taken after resume,
their hardware sampling age is not established, and all fields belong to the
same gauge. They cannot replace an independently measured current integral.

The reviewed driver also distinguishes `charge_full_design`, normally obtained
from profile metadata, from the SRAM nominal-capacity word used by
`charge_now_raw`. Consequently the displayed design/learned-capacity ratio is
not an established exact correction for that getter. Existing SOC-band results
already reject a single fixed conversion as a complete explanation of the
software/raw divergence. No gauge calibration, profile rewrite or current-unit
change is justified by this audit.

### Overnight filtered-current return, 16 October 2026

The event-only observer completed on the same boot and stopped successfully
after USB return. It added `current_avg` reads to existing event records,
without a new wake alarm, periodic wake or power-policy change. Wi-Fi remained
enabled and the automatic suspend delay remained 900 seconds.

| Observation | Result |
| --- | --- |
| Poll-observed cable-free duration | 31,997.45 s (8 h 53 min 17 s) |
| Actual suspension | 30,407.44 s, 95.03% of that interval |
| First suspension after unplug | 914.15 s |
| Displayed capacity | 99% at unplug, 78% at charging return |
| Qualified cable-free sleep pairs | 42, covering 29,956.13 s |
| Learned capacity reported throughout | 2,733 mAh |

All 41 exact `msoc-delta` wakes kept the screen blank and returned to
suspension after 15.18–15.43 seconds. One exact `msoc-high` wake at displayed
80% also stayed blank and resuspended after 15.38 seconds. No record reported
an unblanked screen between first suspension and USB return. The displayed
capacity at return is charging-contaminated and is not an exact pre-charge
endpoint.

The added filtered-current readings provide a useful distinction:

| Displayed SOC band | Natural endpoints | Filtered endpoint median | Software-counter interval estimate | Raw-getter interval estimate |
| --- | ---: | ---: | ---: | ---: |
| 95–100% | 7 | 50.055 mA | 76.95 mA | 85.93 mA |
| 90–94% | 10 | 49.857 mA | 67.58 mA | 86.00 mA |
| 85–89% | 10 | 49.671 mA | 56.04 mA | 85.87 mA |
| 80–84% | 11 | 49.652 mA | 45.97 mA | 85.90 mA |
| 75–79% | 4 | 49.651 mA | 40.19 mA | 85.96 mA |

For the 37 natural endpoints occurring at least one hour after unplug, the
filtered-current median was 49.679 mA, with range 49.503–51.725 mA. One hour
is a descriptive reporting boundary, not an established filter-settling
threshold. Endpoint statistics are unweighted samples after resume; the
counter estimates instead use duration-weighted charge differences.

This strengthens the evidence that a falling software-counter estimate alone
must not be reported as improved electrical consumption. It does not establish
a calibrated whole-suspend current: the filter time constant, sampling age and
charging-history memory are not fully characterized, and all outputs share
the same gauge. The residual overnight discharge remains unresolved; this
observation demonstrates no additional power saving or culprit peripheral.

Return checks confirmed normal charging, `input_suspend=0`, the 900-second
delay, no RTC alarm, no trace instance and no pending NPU restoration state.
