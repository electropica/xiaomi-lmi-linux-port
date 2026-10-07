# Power-domain observation candidate

The running D-repro configuration disables `CONFIG_DEBUG_FS`, preventing
inspection of downstream clock and regulator debug summaries. The preparer
creates a private reset-GPIO diagnostic boot recipe without changing the canonical
locked configuration or either canonical audio constructor. Historical source
patches, audio instrumentation and functional reset-GPIO correction are retained.
No boost/GPIO, regulator policy, gauge calibration or thermal setting is changed.

## Reviewed Kconfig delta

The [config patch](power-debugfs-config.patch) enables debugfs. In this source,
`MSM_PM` selects `MSM_IDLE_STATS` when debugfs is enabled; therefore the candidate
also enables Qualcomm idle statistics with the four existing default bucket
values. Other newly visible optional debug features, including block and
Bluetooth debugfs, are explicitly disabled. Existing functional options stay
unchanged. Enabling idle statistics may add observation overhead; this is a
diagnostic kernel, not a claimed power-saving change.

The preparer verifies the original constructor/config and reviewed delta hashes,
refuses an existing generation directory and retains original input/toolchain
checks. The derived builder still requires byte-identical configuration after
`olddefconfig`. Unexpected changes stop the check rather than relaxing its gates.

Debugfs exposes writable controls: enabling it is not a read-only security
boundary. The intended protocol reads only `clk/clk_summary` and
`regulator/regulator_summary`, with no writes to debugfs controls. Source review
found that clock summary traversal takes transient bus votes when the clock
provider implements them; regulator summary reads voltage/current information.
Snapshots can affect measured state and awake snapshots after resume do not prove
domain residency during deep suspend. Compare diagnostic and original boots
under the same conditions before interpreting current.

## Manual stages

Prepare a new private directory; this stage writes text files only.

?? WSL / Linux ? ??? Prepare only ? suggested model: GPT-6 Luna high

```sh
python3 kernel/diagnostics/power/prepare-debugfs-variant.py \
  --output-directory "$PWD/kernel/diagnostics/audio/state-power-debugfs-reviewed"
```

Use external inputs and the native Alpine toolchain described in the
[existing audio recipe](../audio/README.md). Set `AUDIO_DIAG_ROOT` to the generated
directory and `AUDIO_DIAG_PROJECT_ROOT` to the canonical repository root; set
input/source/tool paths explicitly. Invoke the generated reset-GPIO constructor
first with `--preflight`, then `--check-only`. The latter compiles only Kconfig
host utilities/probes, not a kernel. A heavy build without an option is a
separate manual user operation after those checks pass. It produces
`D-repro-01-power-debugfs-reset-gpio-diagnostic-boot.img`, preserving the ramdisk
and boot metadata. The candidate must not replace the durable boot. No flash or
phone operation is included.

## Validation - 2026-10-06

Initial generation passed exact one-symbol delta, Bash syntax, reset-variant
transformation anchors, preserved output/config gates and overwrite refusal.
External-input preflight then passed all checks, including strict sequential
patch application. Native dynamic/static toolchain probes passed, but initial
`olddefconfig` rejected the one-symbol configuration because newly visible defaults
changed it. The reviewed config patch includes the obligatory Qualcomm statistics
and disables optional Bluetooth/block defaults. Its candidate SHA-256 is
`c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`.
The second native check passed both link probes and byte-identical
`olddefconfig` validation. The later manual build completed successfully; see below. Hardware boot
validation remains pending.


## Manual build - 2026-10-06

The operator ran the heavy build. Both inner and wrapper states are COMPLETE;
post-olddefconfig configuration is byte-identical to the reviewed candidate.
The repacked ramdisk matches the original and the repacked DTB matches the
reset-GPIO-corrected DTB. The resulting temporary diagnostic boot has size
54,652,928 bytes and SHA-256
`147258b2df751cbcdb3c0cb2a10d10f2b0bcacaeee1fe13fdf3bdc79e71e06b0`.
A separate Windows Downloads copy was verified with the same hash. Neither
binary nor raw build logs are tracked. No boot, flash or hardware validation
has occurred yet; a successful build does not establish power improvement.


## Hardware startup - 2026-10-06

After the operator's temporary boot and USB reconnect, SSH reported
`4.19.325-cip128-st12-perf-ga5b3099017ae-dirty`, build timestamp
October 6 16:41:37 UTC. The live IKCONFIG SHA-256 matches the reviewed candidate
`c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`.
Debugfs is mounted and both clock/regulator summaries are readable.
CPU idle remains `sleep_disabled=N`; UPower and the existing CPU-idle opt-in
service are active. Initial state was USB online, 97% charging, 27 C.
The anticipated `/proc/msm_pm_stats` interface is absent, but debugfs
`lpm_stats` is present. Interface names alone are not proof of counters' validity.

An awake, USB-connected snapshot shows zero camera/GPU regulator use counts,
active primary USB and PCIe-0 domain use counts, and the known always-on boost.
These are software use counts under connected conditions, not direct power
measurements or residency during suspend. No regulator/clock debugfs control
was written. A separate bounded unplug/suspend observation is being prepared;
no consumption improvement or diagnostic-kernel long-run validation is claimed.


## First bounded suspend trial - 2026-10-06

A private, 180-second derivative of the existing gauge trial retained USB-off,
settled USB runtime status, capacity, input-quiet and logind-inhibitor checks.
It requested one initial suspend and disabled the gauge re-suspend branch for
this observation. An owned RTC end alarm was cleared on completion; the
transient service finished successfully and is inactive. No debugfs control,
radio or charge policy was changed. Camera and microphone were not opened.

The observed interval was 181.821441 boottime seconds and 0.675646 monotonic
seconds, implying approximately 181.145795 seconds suspended. The newly
available `lpm_stats/suspend` independently reported one successful L3 suspend
lasting 181.169277 seconds. USB stayed offline at both sample endpoints.
The gauge charge-counter decrease was 4,868 uAh, approximately 96.38 mA over
the interval; instantaneous samples were 104.98 mA before initial suspend and
95.703 mA at completion. This short gauge-derived estimate is not an independent
current measurement or a controlled cross-boot comparison. No improvement is
established against the previous approximately 94-97 mA observations.

Before initial suspend, software use counts for primary USB and its PHY had
fallen to zero. PCIe-0, the known always-on boost and several shared storage/radio
rails retained positive use counts. Camera/GPU regulator use counts were zero
in that pre-suspend snapshot. Post-resume snapshots can include display/GPU
activity and must not be described as deep-suspend residency. These summaries
identify consumers/votes, not actual current in individual rails; PCIe DRV
firmware ownership is especially relevant when interpreting a retained vote.
The directory `lpm_stats` cannot be read as a scalar file: future collection
must read its specific read-only `suspend`/`stats` children, with compact parsed
output. Raw logs remain private. After operator reconnection, status was
Charging with USB online and no remaining RTC alarm.


## Read-only consumer follow-up - 2026-10-06

Wi-Fi runtime diagnostics report SUSPENDED, PM usage count zero,
prevent_suspend_cnt zero, 1,663 runtime_get and 1,663 runtime_put, and zero
suspend/runtime_get errors at the inspected instant. The radio interface was
unassociated. This does not establish minimum radio power throughout the trial,
but no outstanding host runtime-PM reference was found.

Source `drivers/pci/controller/pci-msm.c:msm_pcie_drv_suspend` delegates link
management through RPMsg, disables non-suppressible clocks and removes PCIe
vreg/bandwidth votes. It does not take the same GDSC-off path as ordinary
suspend. A retained PCIe GDSC use count under DRV therefore is not sufficient
proof of failed sleep. CNSS `DISABLE_DRV` is enum bit 9 and is read from the
control-params mask, but its debug control is unavailable because
`CONFIG_CNSS2_DEBUG=n`. No quirk mask, PCIe config or driver binding was changed.
Do not imitate a missing control with direct register/GPIO writes.

UFS reported runtime suspended with `power/control=auto`, clock gating enabled
and a 50 ms gating delay. Runtime/system PM levels are both 3: in this source
that means device SLEEP plus link HIBERN8, rather than device POWERDOWN/link OFF.
Its controller snapshot showed no outstanding requests/tasks or recorded UIC/
lane/data-link errors. The live DT contains neither rpm-level nor spm-level,
so the driver's defaults apply. None of the 12 inspected OEM-style overlays
contains those properties; the uninspected OEM base DT prevents claiming full
OEM equivalence. No storage power level was changed.

The TFA9874 debug state is Stopped and firmware state Ok. Uncached regmap reads
(`REGCACHE_NONE` in this driver) found control 0x00=0x0011: PWDN=1, AMPE=0,
DCA configuration=1. Status reads found SWS=0, AMPS=0, CLKS=0, MANSTATE=0 and
DCMODE=0. A configured DCA bit is not evidence that the converter is running.
These awake idle snapshots corroborate an amplifier in powerdown; they do not
measure current in the external always-on boost supply. Only debug reads were
performed, with no sound, microphone capture, reset or register writes.

The residual current is still unexplained. Retained shared supply use counts,
static DDR residency fields and subsystem ONLINE/OFFLINING labels must not be
turned into a hardware-fault diagnosis without meaningful residency/current
measurements. No new power fix or production integration is claimed.


## DDR observation limits and next isolation step

Source review of `drivers/soc/qcom/ddr_stats.c:ddr_stats_show` confirms that it
maps the configured shared-memory table, validates its magic/count and reads
entries; it sends no refresh request to firmware. The observed residency table
sums to about 19.6 seconds even though an independently measured suspend alone
lasted 181 seconds. It therefore is not a complete live residency record for
this experiment. Static low-power counters must not be treated as evidence
that DDR failed to sleep. The firmware table's update policy remains unknown.

If the operator is available, a longer fully powered-off, unplugged interval
can test whether similar reported charge loss persists without Mobian running.
Record pre-shutdown and earliest post-startup gauge data and exact elapsed time,
and account for shutdown/startup consumption, gauge state changes and any USB
charging before comparing. A percentage-only off/on comparison is not independent
current measurement and cannot alone assign a hardware or kernel fault. No
shutdown is scheduled or performed without the operator's readiness.


## Invalidated trace trial - 2026-10-06

The second short unplugged test slept for only 4.122 seconds of a 180.135-second
interval (176.013 seconds awake). The first observed resume reason was IRQ 311,
`pon_kpdpwr_status`, the power-key status interrupt. The operator observed that
the display remained on. This identifies the reported wake source, without
establishing whether a deliberate press or an electrical event caused it.
The resulting approximately 150.37 mA gauge estimate is not a suspend-current
measurement and must not be compared with the previous deep-sleep result as a
power regression.

The trace retained 18,960 of 53,783 written entries, with 34,823 overwritten
entries across three CPU buffers. The initial suspend phases were lost; no
conclusion about rail or clock shutdown during deep sleep follows from this
trace. The transient service finished successfully, its private trace instance
was removed, the owned RTC alarm was cleared, and Charging resumed after USB
reconnection. Raw trace and gauge logs remain private.

The next bounded diagnostic removes high-volume RPMh and regulator-voltage
events, uses 512 KiB per CPU, and stops on a wake occurring more than two seconds
before the planned endpoint. The collector requests initial suspend itself;
the operator should unplug without pressing the power key or touching the
screen. This is a protocol correction, not a production power fix. Preparation
passed Python syntax checks; the following trial validates the revised protocol.


## Complete suspend trace - 2026-10-06

The revised three-minute unplugged trial completed with 181.262 seconds asleep
and 0.678 seconds awake over 181.940 seconds, approximately 99.63% suspended.
Qualcomm L3 suspend statistics independently increased by one success and
181.281 seconds. The wake reason was the planned RTC alarm (IRQ 323), with no
early-wake abort. The gauge-derived interval estimate was 95.63 mA, consistent
with the earlier approximately 96.4 mA result; a short same-gauge estimate does
not establish improved autonomy or independent current accuracy.

All 11,704 trace entries were retained, with zero per-CPU overruns and dropped
events. The initial marker, suspend phases and final marker are present. Trace
timestamps stop advancing across machine suspend in this capture; use the
boottime-minus-monotonic difference and L3 counters for sleep duration instead
of subtracting the identical machine-suspend trace timestamps.

Before machine suspend, the last observed transitions for the PCIe, display and
UFS clocks were disable-complete events. Display panel VCI, PM8150 L14, UFS PHY
GDSC and its L9/L17 supplies also had disable-complete events. No nonzero
device-PM callback result was found. These events confirm driver transitions,
not the physical current or voltage of every rail. Firmware-owned PCIe power,
shared supplies and external boost current remain unresolved; no hardware
power-policy change is justified by this trace alone.

The transient service is inactive with Result=success, its private trace instance
is removed and its owned RTC alarm is empty. Battery status returned to Charging
after reconnection. No camera, microphone or playback was started. No production
power fix or overnight alarm was installed. Raw logs remain outside Git.


## Touchscreen shutdown notification candidate - 2026-10-06

The active touch device is I2C 4-0038 (`fts_ts`), with
CONFIG_TOUCHSCREEN_FTS_MI=y and CONFIG_TOUCHSCREEN_FTS_FOD=y. A read of its
gesture-mode attribute reports Off and register 0xD0=0. That awake read does not
establish the controller's mode during suspend.

In the complete trial's kernel-time window, the touch notifier runs during
panel shutdown, followed by `FTS do resume work` and `Already in awake state`
immediately before PM suspend entry. The retained boot log contains no
`FTS do suspend` or `fts_ts_suspend` message. Source
`drivers/input/touchscreen/focaltech_touch_mi/focaltech_core.c` distinguishes
display-driven `fts_ts_suspend` (which handles gestures/FOD or writes the sleep
mode) from `fts_pm_suspend` (which sets the device-PM flag, enables IRQ wake and
resets a completion, without commanding controller sleep). A zero device-PM
callback result therefore does not prove that this controller entered sleep.

The source's `techpack/display/msm/dsi/dsi_drm.c` uses
`sde_connector_get_lp()` for shutdown notifications when FOD dimlayer is
enabled. `sde_connector_get_lp()` returns CONNECTOR_PROP_LP, not the complete
DPMS state, and can return zero. Zero is MI_DRM_BLANK_UNBLANK, which sends the
touch driver down its resume path even during bridge shutdown. The active
panel selected by cmdline is j11_38_08_0a_fhd_cmd, and its live DT contains
the FOD dimlayer property. This source mechanism is consistent with the logs;
the runtime `mi_cfg` flag and LP value at shutdown have not been directly
instrumented. Attempts to query connector properties with the available
modetest failed to open the device, so they provide no LP-value evidence.

The source-only candidate
`kernel/patches/diagnostics/lmi-dsi-powerdown-notifier-unvalidated.patch`
maps UNBLANK to POWERDOWN only within bridge disable/post-disable notifications.
It preserves LP1/LP2, the startup path, touch gesture/FOD policy, supply controls
and all charge/gauge settings. It is outside the production patch list. The
patch passes `git apply --check` on exact a5b3099017ae source, without changing
that source tree. This is not yet a compiled or hardware-validated fix and does
not establish that the tactile accounts for the residual current.

`prepare-touch-notifier-variant.py` derives a private boot constructor from the
reviewed power debugfs/reset-GPIO recipe, locks the candidate patch hash, checks
its target against the verified source archive and adds it to strict sequential
patch validation/application. The prepared private state is
`kernel/diagnostics/audio/state-power-touch-notifier-reviewed/`.
Shell/Python syntax and external-input/patch-sequence preflight pass. The first
preparation encountered an ambiguous transformation anchor and was rejected;
the corrected preparation uses unique anchors and keeps that failed state.
At preparation time no kernel compilation, source-tree patch application, boot
or flash occurred; the subsequent manual build is documented below.

The manual build will produce a separate
`D-repro-01-power-touch-notifier-diagnostic-boot.img`; retain the current boot
for recovery and use temporary Fastboot boot only. Required hardware checks
are touch suspend/resume logging, usable touch after wake, display/USB/charging,
and matched unplugged deep-suspend current measurements. Check wake/gesture
behavior separately before any production integration. A current reduction
must be measured rather than inferred from corrected notifications.


### Touch notification candidate: manual build completed

The operator's manual build on 2026-10-06 completed in inner state
`audio-swr-20261006T180037Z-66217` and wrapper state
`reset-gpio-variant-20261006T180020Z-66202`, both COMPLETE. Independent output
inspection confirms the two candidate shutdown mappings are present in the
private compiled source, post-olddefconfig configuration matches the lock,
the repacked ramdisk matches the original and the repacked DTB matches the
reset-GPIO-corrected DTB. The temporary boot is 54,652,928 bytes with SHA-256
`390dd50ab4dea33affc8386b300a3c21c4aca9bce39284b8e700a58c1e873bae`.
A separate Windows Downloads copy was verified with the same identity.
No binary or raw build output is tracked. Hardware boot, tactile suspend/resume
behavior and any current improvement remain unvalidated. No flashing occurred.


### Touch notification candidate: temporary hardware startup

After the operator's reported restart, /proc/version exactly matches the banner
embedded in the verified candidate Image: 4.19.325-cip128-st12-perf-ga5b3099017ae-dirty,
build #3 SMP PREEMPT, 2026-10-06 18:01:14 UTC. Live decompressed IKCONFIG SHA-256
matches c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78.
This operational build identity distinguishes it from the earlier #3 build at
16:41:37 UTC; configuration alone would not distinguish the source-only patch.
The running kernel text itself was not hashed. USB SSH works; Charging, USB
online, capacity 100% and temperature 26.7 C were observed. UPower and the CPU
idle service are active; RTC wakealarm is empty. Tactile suspend/resume and
consumption comparison remain pending. No persistent flashing is claimed.


### Touch notification candidate: first unplugged trial

The first unplugged candidate trial on 2026-10-06 completed with 181.407 seconds
asleep and 0.676 seconds awake over 182.083 seconds. Independent L3 statistics
recorded one success lasting 181.425 seconds. RTC IRQ 323 caused the planned
wake; no early wake or nonzero device-PM callback result was observed. All
11,702 trace entries were retained with zero buffer loss. The transient service
finished successfully, its trace instance was removed and its owned RTC alarm
was cleared. Charging resumed after USB reconnection; CPU idle remains enabled.

The touch log now reports `FTS do suspend work by event POWER DOWN`, followed
by `fts_ts_suspend`, IRQ disable and a disabled-gesture branch before machine
suspend. The later `fts_ts_resume` resets the controller, reads chip ID 0x54/0x52,
restores its state and enables the IRQ. This contrasts with the earlier trial's
resume/Already-in-awake-state sequence and confirms that the candidate changes
the observed touch suspend path. Log lines tagged Error that explicitly say
register-write success are not evidence of failed writes. The operator subsequently confirmed
normal touch response after unlocking, opening an application and scrolling.
This validates one wake cycle, not repeated-cycle or gesture/fingerprint coverage.

Charge counter fell from 2,774,941 to 2,770,200 uAh while USB was offline,
giving 93.735 mA over the measured interval. Capacity remained 100%; initial
instantaneous current was 145.019 mA and final current 92.773 mA. The earlier
valid trace trial estimated 95.629 mA. This approximately 1.89 mA difference
(about 2%) is a single, non-interleaved comparison across a reboot and different
gauge state, not proof of an autonomy improvement. Wi-Fi conditions, battery
temperature and gauge settling were not controlled as matched variables.
The approximately 94-96 mA residual current remains unresolved. No production
patch or permanent boot was installed, and raw logs remain private.


### Wi-Fi shutdown isolation and October 7 overnight observation

A finite phone-local radio-off check on October 6 exercised the normal CNSS
idle-shutdown path. After 15 seconds, use counts for pm8150_s5, pm8150_s6,
pm8150a_s8, pm8009_s2 and pcie_0_gdsc were all zero; they remained zero at
45 seconds. The log recorded psoc idle timeout and CNSS idle shutdown. These
are driver-vote observations, not independent measurements of rail current.
The first restore command exceeded its eight-second timeout, but subsequent
inspection confirmed Wi-Fi enabled again and the original votes restored.
A pre-scheduled restoration timer had provided a fallback; none remains active.

The subsequent Wi-Fi-off suspend trial was invalidated by IRQ 438 msoc-delta
after only 2.944 seconds asleep over 3.625 seconds. Its trace had no buffer loss
or nonzero device-PM result, but that interval is too short to estimate or compare
idle consumption reliably. Wi-Fi was restored, the collector stopped, and its
RTC alarm and trace instance were removed. A revised bounded collector allowing
one guarded gauge-only re-suspend was prepared but not started before the night.
No persistent Wi-Fi, gauge or suspend policy was changed.

On October 7, the phone reconnected without rebooting. Its running build banner
still identifies the October 6 18:01:14 UTC touch-notifier candidate. Persisted
UPower history records 99% discharging at 21:12:26 CEST on October 6 and 66%
at 06:03:41 CEST on October 7: 33 percentage points over 8 h 51 min 15 s,
approximately 3.73 points/hour. The first inspection at 06:06 already found
68% charging and 22.5 C. Exact unplug/replug capacities were not captured.
The initial disk history ended at 01:48; a later UPower write recovered all
remaining overnight samples. The service stayed active with zero restarts,
so the apparent gap was delayed persistence rather than demonstrated data loss.

Kernel journal accounting found 66 completed suspend pairs between 21:12:39
and 06:05:01: 30,901.694 seconds suspended over a 31,941.929-second span
(96.74%). Sixty-five wake reports identified IRQ 438 msoc-delta; typical awake
intervals were about 16 seconds. The remaining current is therefore not
explained by the phone staying continuously awake. Radio state was enabled
before and after the night, but association and power votes were not continuously
sampled. This is an uncontrolled overnight observation, not the pending
fully-radio-off comparison. It does not demonstrate an autonomy improvement
from the touch notification candidate. All test services/timers were inactive,
the RTC alarm was empty, and charging worked after reconnection. Raw histories
and kernel logs remain private; no camera or microphone was started.


### Fully-radio-off suspend measurement — October 7

The repeat Wi-Fi-off trial completed without an early wake or guarded retry.
Clock accounting records 180.695 seconds asleep and 0.679 seconds awake over
181.374 seconds (99.63% suspend occupancy); independent L3 statistics increased
by one success and 180.712 seconds. Capacity remained 80%, and charge counter
fell from 2,102,047 to 2,097,408 uAh, giving approximately 92.077 mA over the
measured interval. Initial and final instantaneous readings were 91.796 and
90.331 mA. All five CNSS/PCIe supply use counts were zero both before suspend
and at the final snapshot. This establishes substantial gauge-reported residual
current even with the normal radio shutdown path, but does not independently
measure physical rail current or exclude a battery/gauge calibration issue.

The RTC produced the planned wake. Wi-Fi was restored, charging resumed, the
service and restoration timer are inactive, the owned alarm is empty, and the
trace instance was removed. The trace retained only 7,836 of 11,578 events,
with 3,742 overruns: clock/L3/gauge accounting remains independently available,
but the incomplete trace cannot support conclusions about every device transition.
No nonzero PM callback result appears in retained events; absence in an incomplete
trace is not proof that every callback succeeded. A nearby Wi-Fi-enabled arm
is pending to reduce the confounding of the older different-capacity comparison.


### Nearby Wi-Fi-enabled comparison — October 7

The enabled-radio arm on the same running candidate completed with 180.765
seconds asleep and 0.683 seconds awake over 181.448 seconds (99.62% occupancy).
L3 increased by one success and 180.782 seconds. Capacity stayed at 81%, and
charge counter fell from 2,125,537 to 2,120,758 uAh: approximately 94.817 mA.
The five CNSS/PCIe supply use counts were one at both snapshots, contrasting
with the radio-off arm's zero votes. The original enabled radio state was kept;
this is not a controlled associated-network workload comparison.

The nearby off/on difference is approximately 2.740 mA (about 2.9% of the on-arm
current). Both arms slept almost throughout and neither needed a gauge retry.
This single sequential pair, at 80% then 81% with charging between arms and
without matched temperature/association control, is insufficient to quantify
a stable Wi-Fi penalty. It does show that stopping the radio did not eliminate
the approximately 92 mA residual gauge-reported consumption in this experiment.
It does not identify the remaining consumer or independently calibrate the gauge.

The larger 1,024 KiB-per-CPU trace retained all 11,704 events without overruns
or nonzero PM callback results. The RTC caused the planned wake; the service
is inactive, its alarm is empty, the trace instance is removed, Wi-Fi remains
enabled and charging resumed. No permanent radio or suspend policy changed.


### APSS/ADSP sleep accounting — October 7

A further bounded three-minute trial retained the enabled radio state and added
RPMh master snapshots before and after suspend. Capacity stayed at 90%; charge
counter fell from 2,355,464 to 2,350,729 uAh over 181.883 seconds, approximately
93.720 mA. Clock accounting records 181.202 seconds suspended and 0.681 seconds
awake (99.63% occupancy); L3 recorded one success lasting 181.223 seconds.
No gauge retry or early reconnection occurred; the RTC caused the planned wake.

The exposed RPMh master counters were APSS and ADSP only. Using their 19.2 MHz
accumulated-duration counters, APSS added 181.240 seconds asleep (99.65% of the
interval; seven entries), and ADSP added 181.793 seconds asleep (99.95%; eight
entries). These counters support sleep of both processors despite substantial
gauge-reported residual current. They do not establish physical removal of every
DSP supply or account for unexposed masters, external peripheral loads or gauge
calibration. In particular, missing modem statistics are not proof of modem sleep.
The downstream kernel exposes msm_subsys states rather than remoteproc devices;
labels such as ONLINE/OFFLINING alone were not treated as current measurements.

The trace retained all 11,561 events without loss or nonzero PM callback results.
The collector is inactive, its RTC alarm is empty, the trace instance was removed,
Wi-Fi remains enabled and charging resumed. No processor, peripheral, driver,
regulator or gauge protection was disabled. This narrows the residual-current
investigation toward retained physical loads and measurement accuracy rather
than demonstrating an autonomy fix. Raw traces and histories remain private.


### Display chronology and codec supply policy — October 7

The completed trials were compared without another suspend or media capture.
In trials 06 and 08, `display_panel_vci` and `pm8150_l14` already had zero
use counts in the pre-suspend snapshot, then had one after wake. Trials 04
and 07 started with one and recorded their disable/enable transitions.
The missing panel-disable event in trial 08 is therefore explained by the
snapshot chronology; it is not evidence that the panel stayed powered in sleep.

The live WCD938x node lists `cdc-vdd-rxtx`, `cdc-vddio`, `cdc-vdd-buck` and
`cdc-vdd-mic-bias` as static supplies, with no per-supply `lpm-supported`
properties. The first three resolve to `pm8150_s4`; microphone bias resolves
to `pm8150a_bob`. The requested loads are 30,000, 30,000, 650,000 and
30,000 uA respectively. These are regulator policy requests, not measured
battery currents, and must not be added to estimate discharge.

In the locked source, `techpack/audio/asoc/codecs/msm-cdc-supply.c` defaults
missing `qcom,<supply>-lpm-supported` properties to zero. Its
`msm_cdc_set_supplies_lpm_mode()` only calls `regulator_set_load()` for
supplies with that flag. `wcd938x.c` registers a late-suspend callback which
requests this mode when the component was suspended. Trial 08 recorded that
callback returning zero; with the live properties, the helper cannot lower
these four load requests. This identifies a policy worth investigating, not
a demonstrated cause of the approximately 94 mA residual current.

Further inspection identified the actual live provider as
`qcom,rpmh-vrm-regulator`, implemented by `drivers/regulator/rpmh-regulator.c`,
rather than the separate upstream-style `qcom-rpmh-regulator.c`. S4's provider
has no supported-mode table; the downstream driver removes its `set_load`,
`set_mode` and `get_mode` operations when that table is absent. Reducing a
codec load request alone would therefore not change S4's hardware-mode vote.
S4 also supplies UFS and WLAN; it cannot be treated as an audio-only rail.

BOB does expose supported modes 0, 2 and 4, with load thresholds of 0,
1,000,000 and 2,000,000 uA. The driver's load mapping selects the same first
mode for both 30,000 and zero uA. Its PMIC5 mapping identifies that first mode
as PASS, exposed as framework STANDBY. The live debug view already reports
framework mode 8 (STANDBY) for both the normal and active-only BOB regulators;
the only enabled normal-regulator consumer is the codec's 30,000 uA request.
These are software votes and do not independently measure physical current.

Consequently, adding the missing codec LPM flags alone is not a justified
power-saving candidate on this live configuration: S4 cannot act on the load
change and BOB would retain the same mode. No kernel build is proposed for
that change. This does not exclude physical codec consumption while its
static supplies are enabled. Establishing whether those loads explain the
residual current requires a separately justified isolation or measurement;
blindly disabling a shared rail or converting static supplies to on-demand
would risk the validated audio and storage paths.

No supply was disabled, no DT property was changed, and no driver was unbound
during this inspection. No microphone or camera capture was performed.
Raw DT and trace dumps remain private.


### Final RPMh sleep commands — October 7

A bounded three-minute trial added the existing `rpmh_send_msg` and
`rpmh_tx_done` events without changing the radio or regulator policy.
The interval lasted 181.315 seconds, including 180.631 seconds suspended
(99.623%); L3 added one success lasting 180.649 seconds. Capacity stayed at
96%, while the charge counter fell from 2,493,460 to 2,488,679 uAh:
approximately 94.927 mA by the gauge. APSS and ADSP master counters recorded
99.636% and 99.953% asleep respectively. The RTC caused the planned wake;
no gauge retry, early reconnection or early-wake abort occurred.

All 11,937 trace events were retained without overrun, dropped events,
nonzero PM callback results or RPMh acknowledgement errors. Of these,
291 were RPMh send events. The live command database and TCS configuration
`[2,2,0,3,1,3,3,1]`, interpreted using the locked downstream driver's allocation
order, identify apps_rsc banks 0–1 as active, 2–4 as sleep and 5–7 as wake.
Bank 56 represents the separate PDC data-write path, not a regulator bank.

At the `machine_suspend` entry, the final sleep commands superseded earlier
nonzero bus commands. The final votes were:

| Resource | Sleep command | Interpretation |
|---|---|---|
| `cx.lvl` / `mx.lvl` | 0 / 0 | APSS requests level zero |
| `xo.lvl` | 0 | APSS requests level zero |
| `bobc1` mode | 2 | PMIC5 PASS; wake command is AUTO (6) |
| `ldoa12` enable | 0 | Disable request; wake command is 1 |
| `SH4`, `SN11`, `CN0` | `0x40000000` each | Commit bit, invalid/zero X and Y bandwidth votes |

The BCM interpretation follows `msm_bus_fabric_rpmh.c`: commit is bit 30,
valid is bit 29, and X/Y each occupy 14 bits. Earlier values such as
`0x60198000` are not the final sleep request. Post-reconnection `bw` sysfs
snapshots contain nonzero USB/NPU client entries, but are awake snapshots;
they must not override the final sleep trace or be treated as proof of a
sleep-time bus leak. An absent command for a resource does not establish its
state: unchanged requests can remain cached, and other masters can vote.

These observations establish the APSS software requests, not the physical
state or current of every PMIC rail, peripheral or unexposed subsystem.
The approximately 95 mA remains unexplained. No new kernel build, regulator
write, driver unbind, camera capture or microphone recording was performed.
The collector is inactive, its trace instance was removed, its RTC alarm is
empty, Wi-Fi remains enabled and charging resumed. Raw traces stay private.


### Read-only RPMh aggregate observer candidate — October 7

The existing event trace shows commands that are emitted, not a complete
snapshot of unchanged requests. The isolated diagnostic patch
`kernel/patches/diagnostics/lmi-rpmh-vote-observer-unvalidated.patch` adds a
read-only `lmi_diag_votes` sysfs attribute to each downstream RPMh provider
when DEBUG_FS is enabled. It is outside the production patch list.

The reader holds the provider's existing aggregation mutex, computes active
and sleep requests into local zeroed structures, and prints their validity
masks, register values, cached sent requests and each regulator's active/sleep
participation. It does not send RPMh commands, access PMIC registers, call
regulator setters or change enable/voltage/mode policy. The existing aggregate
helper only modifies its local output structures. Device-managed attribute
removal precedes managed provider memory release; an attribute creation failure
warns without failing regulator probe. Output is bounded to one sysfs page.

These are software requests, not measured current or physical rail states.
A cached sleep request is not valid just because its storage contains a value;
its valid mask and `sleep_request_sent` must be interpreted. Other masters'
votes remain outside this reader, and snapshots around suspend do not sample
the system continuously while it is asleep.

`prepare-rpmh-vote-observer-variant.py` derives from the current debugfs/reset-GPIO/
touch-notifier recipe, locks the observer patch hash and adds it to the archive
comparison, strict patch sequence and application steps. It prepares an ignored
private state directory and never builds or contacts hardware. The output name
is `D-repro-01-power-rpmh-votes-diagnostic-boot.img`. The private prepared state
is `kernel/diagnostics/audio/state-power-rpmh-votes-reviewed/`.

Host validation passed: preparer Python syntax, wrapper shell syntax,
`git apply --check --whitespace=error-all` on exact source, archive target
comparison, the complete sequential patch check and native Kconfig validation.
No kernel target was compiled. The initial check rejected missing environment
paths, and a subsequent noninteractive user check stopped at sudo; the fully
specified root-WSL check then completed. Failed checks are retained in ignored
private state. This validates preparation, not the C compilation or hardware.

At preparation time, the candidate was source-only pending the manual build. After temporary
Fastboot boot, verify identity, provider attributes, display, USB, charging and
touch before a bounded unplug test. Capture requests after USB runtime suspend,
then compare with the final command trace. Do not disable a retained supply
merely because its software sleep enable is nonzero.


### RPMh observer manual build and extended observation ? October 7

The operator manually produced `D-repro-01-power-rpmh-votes-diagnostic-boot.img`,
54,652,928 bytes, SHA-256
`a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50`.
The internal builder recorded COMPLETE; kernel build, DTB build and DTB
verification each returned zero. The outer wrapper reported a missing status
file because the inner state directory was root-owned mode 0700 and unreadable
by the invoking user. Root inspection confirmed completion and the output
manifest; the Windows transfer was independently checked against the same hash.
This is a wrapper reporting/access defect, not evidence of a failed kernel build.
No global permissions were changed and no repeat compilation was started.

After the operator's temporary boot, USB SSH and charging worked and all 47
RPMh provider attributes were readable. The live banner identifies the build
of October 7 at 05:27:54 UTC; IKCONFIG SHA-256 is
`c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`.
The banner/config and observer presence corroborate the candidate but are not
cryptographic attestation of running kernel text. No new touchscreen or media
validation has yet been performed with this variant.

The operator reported approximately 10 hours 20 minutes disconnected, with
capacity falling from 100% before departure to 63% at first SSH after return:
about 3.58 percentage points per hour. This uncontrolled interval is not an
independently calibrated current measurement. The same boot remained active.
Kernel logs contain 80 completed deep-suspend intervals from 08:02:37 to
18:04:55 local time: approximately 34,889 seconds asleep over a 36,139-second
span (96.54%). Of the 80 resume causes, 76 were msoc-delta, one esr-delta,
one RTC alarm, one msoc-high and one Type-C state change. Median awake gaps
were 15.83 seconds; median sleep among the 77 intervals lasting at least two
minutes was 481.66 seconds. No panic, Oops or matching suspend-failure message
was found in the inspected current-boot kernel journal. This does not establish
absence of every possible device error. The observation provides no autonomy fix.

An awake, plugged-in observer snapshot has eleven VRM resources with a valid
computed sleep enable of one. It is not their final suspend state. In the locked
provider driver, a separate sleep request is sent only when active and sleep
requests differ or previously differed; an absent sleep command or invalid
cached sleep mask cannot be interpreted as an off request. Late-suspend changes
must be matched against the final command trace. A bounded three-minute
collector adding all 47 observer snapshots is prepared but has not been run.
No RTC alarm or collector was installed for the extended absence; raw histories
and snapshots remain private. Shared supplies must not be disabled based solely
on these software requests.


### First bounded aggregate-observer trial ? October 7

With the observer candidate and Wi-Fi enabled, the operator completed a bounded
three-minute unplugged trial. Elapsed time was 181.240 seconds, including
180.547 seconds suspended (99.617%); L3 added one success of 180.564 seconds.
Capacity remained 73%, while the charge counter fell from 1,933,009 to
1,928,237 uAh: approximately 94.787 mA by the gauge. APSS and ADSP counters
recorded 99.636% and 99.950% asleep respectively. The RTC caused the planned
wake, with no retry, early reconnect or early-wake abort.

All 47 provider snapshots were readable at armed, pre-suspend and finished
points. The trace retained all 11,892 events without overrun, dropped events,
nonzero PM callback results or RPMh acknowledgement errors. Exact begin/end
markers delimit the machine-suspend command window; substring matching of
`end` would incorrectly match `suspend` and must not be used for extraction.
The final sleep bank again requests zero CX/MX/XO levels, BOB mode PASS (2),
L12 enable zero/mode 4, and zero/invalid bandwidth for SH4/SN11/CN0.

The pre-suspend aggregate requests include enabled BOB, L5, L6, L17, the
PM8150A L1 touch supply, S4 and four Wi-Fi rails. These snapshots precede
late device suspension: the trace explicitly disables L17 before machine
suspend, while L12 already has a zero sleep enable before initial suspend.
L14 is already disabled in that snapshot and is enabled again after wake.
Consequently neither pre-suspend L17 nor post-wake L14 activation establishes
sleep-time retention. Remaining computed requests are software state, not
independent physical-current measurements, and unexposed masters remain outside
this observer.

Consumer mapping identifies L5 as shared among display/USB/UFS/PCIe PHY paths,
L6 and L17 as UFS supplies, PM8150A L1 as the touchscreen supply, S4 as shared
codec/WLAN/UFS power, and BOB as a static codec supply. The locked UFS driver
intentionally retains its I/O rails in low-power mode for device sleep with
HIBERN8 while switching off VCC. The touch driver normally sends a sleep
command rather than cutting supply power; supply cycling is confined to its
factory-build branch. These policies do not prove excessive consumption by
those consumers or justify disabling shared supplies.

The collector is inactive, the owned RTC alarm is empty, the trace instance
was removed, charging resumed and Wi-Fi remains enabled. No regulator policy,
voltage, device binding or persistent setting changed. A radio-off comparison
with the same 47 observer snapshots is prepared, not executed. Its new purpose
is to distinguish retained aggregate requests from the previous radio-off
current measurements; no autonomy improvement is claimed. Raw data stays private.


### Radio-off aggregate comparison and gauge limits ? October 7

The second aggregate-observer trial stopped Wi-Fi using NetworkManager and
verified zero software use counts for S5, S6, PM8150A S8, PM8009 S2 and PCIe
GDSC before suspend and after the planned wake. All four VRM sleep-enable
requests changed to zero in the observer as well. No driver was forcibly unbound.

Elapsed time was 182.097 seconds, including 181.390 seconds suspended
(99.612%); L3 added 181.408 seconds. Capacity stayed 77%, while the charge
counter fell from 2,026,412 to 2,021,701 uAh: approximately 93.135 mA by the
gauge. APSS and ADSP counters recorded 99.623% and 99.989% asleep. The RTC
caused the planned wake without retry or early abort. All 47 snapshots were
readable and all 11,958 trace events were retained without loss, nonzero PM
callback results or RPMh acknowledgement errors.

Compared with the preceding enabled-radio arm's 94.787 mA, the difference is
1.652 mA. These short sequential arms had intervening charging and different
capacity, without matched temperature or association control; the difference
is not a calibrated stable Wi-Fi penalty. The important result is that disabling
the four radio requests still leaves approximately 93 mA by the gauge.
BOB, L5, L6, the touch L1 supply and shared S4 requests remain comparable.
L17 is explicitly disabled during device suspension in both traces. The final
L5/L6 mode commands are PMIC5 LDO LPM (4), not HPM (7), despite the earlier
awake/pre-suspend values. BOB retains its PASS sleep-mode command.

The read-only follow-up found no modem exposed through ModemManager and
Bluetooth soft-blocked. Downstream subsystem labels were not interpreted as
physical-current measurements. Flash intensity values can remain nonzero when
its switch controls are zero: the driver getter returns cached brightness,
not a hardware light/current measurement. No flash or microphone was activated.
GPU force-clock, force-bus and force-rail settings are zero; both traces contain
GPU clock and CX GDSC disable transitions. `force_no_nap=1` affects the ACTIVE
to NAP idle path, not proof of a permanently powered GPU through system sleep.
No graphics policy was changed.

The operator confirmed the original battery. Its selected gauge profile is
`j11sun_4700mah`; reported design capacity is 4,700 mAh and learned full capacity
2,822 mAh, while the exposed cycle count is one. These values do not establish
physical battery health or lifetime cycles. No independent capacity test exists.
The active DT enables weighted learning and permits replacing a mismatched
profile; the driver does not reload an identical profile solely because
`fg-force-load-profile` is set. Profile replacement can clear cycle accounting.
The absent min/max learning-limit properties default to zero (disabled); there
is no evidence that 2,822 mAh was forced by a 60% lower clamp.

In the locked GEN4 driver, `charge_counter` is computed from the hardware
CC_SOC_SW fraction multiplied by learned capacity. Its delta is therefore not
an independent coulomb/current calibration. `current_now` uses the separate
IBATT register conversion, approximately 488.281 uA per signed count; the
pre/post-unplug readings near 92?95 mA are internally consistent with the
counter-derived interval, but both still depend on the same gauge hardware.
No learned capacity, battery profile, charging limit or calibration was reset.
Changing the reported full capacity would not demonstrate lower physical drain.

Wi-Fi was restored and confirmed enabled before reconnection; the restore timer
and collector are inactive, the owned RTC alarm is empty, the trace instance
was removed and charging resumed. Further identical short suspend trials are
not justified by these results alone. Remaining discrimination requires a
specifically justified peripheral isolation or an independent/off-state baseline;
no unsafe shared-rail shutdown is proposed. Raw data remains private.

### Completion reporting correction — 2026-10-07

The reset-GPIO wrapper now verifies private internal completion metadata with
sudo when it is inaccessible to the invoking user. It retains the private
state/output modes and still rejects missing or linked STATUS, non-success
status, nonzero builder exit, and empty or linked build outputs. Sixteen bounded
metadata regression cases passed, including a root-owned private fixture
that rejects an unprivileged reader. The same verifier accepted the existing
observer state and its expected 54,652,928-byte output without modifying them.
A newly prepared observer chain passed recipe checksums and host-only strict
patch preflight. No kernel was compiled for this correction; interactive sudo
authentication and a complete user-invoked build have not been retested.
Previously prepared recipes and their evidence remain unchanged. See the
[audio constructor documentation](../audio/README.md#private-internal-completion-metadata).

### Approximate powered-off comparison — 2026-10-07

An initial systemd poweroff reached the poweroff target but the operator reported
that the phone restarted. That attempt is not a valid powered-off discharge
test. The restart returned to the original persistent D-repro kernel, so the
temporary RPMh observer identity must be checked again before later observer
tests. The operator subsequently confirmed a manual shutdown for an unplugged
comparison; the return observations are recorded below.

The last pre-shutdown sample reported 88% and 2,273,114 uAh. It did not
include a paired host/phone clock sample; a later host reading does not establish
an exact phone-clock offset. Measure elapsed time using the trusted host/operator
interval rather than subtracting phone timestamps. Read the return battery
before any further diagnostic reboot. Startup and any connected charging still
affect that return sample: this
comparison is approximate and cannot independently calibrate the gauge or
measure powered-off current. Do not infer a battery fault or an autonomy fix
from this approximate test.

### Single read-only return snapshot — 2026-10-07

`read-power-snapshot.py` emits one bounded JSON snapshot of the battery, BMS,
USB supply, kernel release/banner, decompressed IKCONFIG hash, device compatible
strings, uptime, existing RTC alarm and CPU-idle parameter. It runs no commands,
starts no service or acquisition, makes no writes and schedules no wakeup.
Missing or invalid fields remain explicitly unavailable; a missing USB property
must not be interpreted as zero. Current signs and reported gauge capacity are
preserved without recalibration or overriding the kernel's status.

📱 SSH — Xiaomi lmi — 🔎 Read only — phone already powered on and reconnected

```sh
python3 /path/to/read-power-snapshot.py
```

Keep raw JSON outside Git: the kernel banner can contain a build-host identity.
For a powered-off comparison, collect the first return snapshot before another
diagnostic reboot. Record the off interval using a trusted host/operator clock
and note any startup/USB-charge time. This snapshot cannot measure current while
the phone is off or prove physical battery capacity. Banner/config identity also
does not establish the executable boot image's hash; retain the manual boot
artifact manifest and reconfirm the candidate before later controlled trials.

`test-power-snapshot.py` uses a temporary fixture tree, including missing fields,
negative charging current, malformed and oversized config data. It never opens
the host's live power supplies or contacts the phone. These fixture tests passed;
the first live return read also succeeded without changing phone state. No shutdown,
Android restore, battery learning reset or charging-limit change is automated.

### Shared Android gauge source and retry candidate — 2026-10-07

The selected lmi battery-profile file and five inspected gauge-read/counter
function bodies match both pinned Android references. A shared retry-boundary
defect was reproduced using the actual C functions and simulated register reads.
A separate two-loop candidate passes the same twenty cases but is not included
in any diagnostic recipe or live kernel. It addresses inconsistent-read handling,
not charge calibration or demonstrated residual consumption. See the
[source comparison and proof](../../../docs/provenance/external-lmi-source-comparison-2026-10-07.md#battery-profile-and-gauge-read-follow-up).


### Powered-off return observations — 2026-10-07

After at least one hour confirmed off, the operator reported approximately two
minutes in Fastboot while awaiting instructions, then a normal boot showing 88%.
The first SSH return snapshot, at about 174 seconds of kernel uptime after USB
reconnection, still reported 88%, Charging, 2,288,607 uAh, approximately -651 mA
and 22.2 C. The permanent D-repro banner and IKCONFIG hash
`6512a0c29ebf987d25c0cceb79917df32d6fed4b67e4c3b94bfad9fdb1745e37`
were present; the transient RPMh observer was no longer running. No further
diagnostic reboot occurred before this measurement. The RTC alarm was empty.

The percentage matches the last pre-shutdown 88% sample, so there is no visible
large percentage drop in this approximate comparison. It does not establish
zero off-state consumption, battery health or a Mobian autonomy fix. Charging
between the pre-shutdown sample and actual manual shutdown was not quantified;
Fastboot, startup and resumed USB charging also affect the return. The counter
increase of 15,493 uAh cannot be treated as an off-state gain or discharge rate.
The phone clock was not used to determine the off interval. Raw identifying
snapshot data remains outside Git. No battery calibration or profile was reset.


### Permanent-kernel profile lookup failure — 2026-10-07

The powered-off return boot reproduced the older profile-load failure: the
gauge reported `Unknown Battery`, zero design capacity, resistance ID 99,800
ohms and profile errors -6/-61 followed by the driver's OTP fallback. This is
an observed selection failure, not proof that retained gauge SRAM has been
erased or contains a particular profile. The earlier successful lmi-profile
identification must not be attributed to this permanent boot.

Read-only inspection of the live DT confirmed that the gauge's existing
`qcom,battery-data` phandle targets `/soc/qcom,battery-data`, containing
`j11sun_4700mah`, 100 kOhm ID, 4,700 mAh nominal capacity and 416 profile bytes.
The flattened tree order places that container before the gauge. The only
subsequent node named `qcom,battery-data` is `/vendor/qcom,battery-data`, whose
children are generic profiles rather than the lmi profile. In the locked
driver, `of_find_node_by_name(node, "qcom,battery-data")` searches only nodes
after `node`, not its property target. The source traversal and live ordering
therefore explain why the named lmi lookup cannot succeed on this boot.

The isolated candidate
[`lmi-fg-profile-phandle-unvalidated.patch`](../../patches/diagnostics/lmi-fg-profile-phandle-unvalidated.patch)
resolves the existing phandle first. If absent/unresolved, it retains the
legacy name search and supplies an owned node reference because that API
consumes its starting reference. The patch makes no direct changes to profile bytes, charging parameters,
learning code, capacity conversion or authentication policy. However, reaching
the existing load path can change retained gauge state, as explained below.
Patch SHA-256:
`59e357834e97f043a45c51e50e29ada59a44ca657afa9c2fcfdeafbfb56884f6`.
The locked `qpnp-fg-gen4.c` input SHA-256 is
`0f5676829cb2a40daa191a456998c700d744afe8346e07dd3c7af2a7e8685957`.

`test-fg-profile-lookup.py` verifies that exact input and applies the patch with
zero fuzz in a temporary tree. The actual changed C lookup fragment compiles
with strict warnings against bounded OF stubs. Explicit-link precedence,
legacy fallback, missing-container handling and 200 repeated reference-balanced
lookups pass; the source remains unchanged. These stubs are not a full kernel
OF implementation or a hardware test. No kernel was compiled or deployed and
the candidate is not included in any prepared constructor.

A future manual diagnostic build must first review profile-loading side
effects, including the existing force-load policy and retained gauge state.
Validation must identify the boot, inspect startup profile selection and
confirm charging before any autonomy comparison. Successful selection alone
would not prove lower physical consumption or battery health. Do not merge
this with the separate shadow-read retry candidate merely to combine trials.


#### Profile-loading side effects reviewed before deployment

The locked `is_profile_load_required()` compares only the first 24 profile
bytes when an accepted integrity marker is present. A matching prefix skips
reload even with `qcom,fg-force-load-profile`; it does not prove all 416 bytes
match. A different prefix with force-load enabled, an absent integrity bit or
an invalid integrity marker can trigger a load. SRAM read errors instead skip
the load. No live SRAM integrity or profile-prefix measurement was obtained in
this permanent boot, so its reload decision remains unknown.

If loading occurs, `profile_load_work()` can clear cycle counters, write the
416-byte profile, restart the gauge, and store nominal capacity as learned
capacity on the normal non-aged path. SDAM handling also depends on its cookie.
Even a temporary `fastboot boot` therefore does not guarantee that all gauge
state changes disappear after reboot. The candidate must not be deployed as
though it were only a cosmetic battery-name fix. A future trial needs an
explicit gauge-state preservation/observation plan before activation. No
profile reload, counter clearing or learned-capacity write was performed here.


### Guarded retained-profile observer — 2026-10-07

The separate diagnostic patch
[`lmi-fg-profile-observer-unvalidated.patch`](../../patches/diagnostics/lmi-fg-profile-observer-unvalidated.patch)
adds the root-readable, non-writable `lmi_fg_profile` device attribute when
CONFIG_DEBUG_FS is enabled. An explicit read follows the existing lmi DT
phandle, copies the named 416-byte reference into a local buffer, then reads
retained profile SRAM and the integrity marker before/after. It reports marker,
24-byte prefix and full 416-byte equality, cached profile status, force-load,
multi-profile flag and battery ID. Missing or malformed reference data and SRAM
read errors are returned explicitly; a changed integrity marker returns EAGAIN.
Stable markers are not a guarantee of an atomic 416-byte sample.

The attribute calls no profile selector/loader, setter, work scheduler, gauge
restart or gauge-data write. SRAM reads use the existing memory-interface
transport and can wake it; take this snapshot while connected, not during a
standby-consumption measurement. No periodic polling or acquisition is added.
Raw profile bytes and authentication identifiers are not emitted.

The diagnostic also blocks the existing reload-required branch before cycle
clearing and `qpnp_fg_gen4_load_profile()`. It does not bypass the existing
profile-selection failure or authentication policy. A matching retained-prefix
path can still perform the driver's normal post-profile initialization, including
its existing SDAM handling; this is not a claim that the whole boot performs
no gauge writes. Battery removal and ordinary hardware initialization remain
normal driver behavior. This temporary guard is diagnostic, not a production fix.

Host tests apply the patch with zero fuzz to the locked source and compile the
actual attribute fragment with strict warnings and bounded DT/SRAM stubs.
Twelve cases cover full/prefix/tail equality, missing data, malformed lengths,
all three read-error positions and a changing marker. References balance and
cached chip state remains unchanged. Two extracted control-flow cases confirm
that the reload-required path exits before clearing/loading, while the matching
path still reaches existing initialization. The stubs are not a full kernel or
hardware test. No kernel was built or booted for this observer.

Patch SHA-256: `ec86f4cb13d7efe78f3dfcddbe6771c09373b24b2ab868d05e04f2261de80440`.
`prepare-fg-profile-observer-variant.py` derives a new private recipe from the
already tested RPMh/touch/debugfs chain; the selection-fix and shadow-retry
candidates are explicitly excluded. The final guarded recipe passed manifest
checks and the complete strict patch preflight. Earlier prepared states were
not overwritten. The original boot's ramdisk and DTB sections are retained and
verified by the constructor. Runtime bootloader overlays still need live review.

The user performs all kernel builds. Use the guarded prepared directory,
not the earlier observer-only preparation. A full user-invoked build and
live attribute availability remain pending. Before any later standby trial,
identify the temporary boot and take a single connected profile snapshot from
`/sys/class/power_supply/bms/device/lmi_fg_profile`; retain it privately.
Report prefix equality separately from whole-profile equality and interpret
the integrity marker using the driver's whitelist. Do not infer physical
capacity, lower consumption or safe profile replacement from equality alone.


#### Single guarded-profile read and interpretation

`read-fg-profile-observer.py` reads at most 4,096 characters once from the
root-only attribute and emits parsed JSON. It rejects missing, duplicate,
unknown and inconsistent fields. Missing attributes and kernel read errors
remain explicitly unavailable rather than becoming zero or "no reload".
It emits no raw SRAM bytes and performs no writes or background sampling.

The integrity whitelist matches the locked driver's symbolic bit combinations.
For single-profile mode, `reviewed_reload_rule` reports the reviewed logic from
marker and prefix equality, including force-load behavior. It is interpretation
of this snapshot, not an observed execution of the loader; the diagnostic guard
blocks the reload-required branch. Multi-profile age state is not captured, so
that interpretation is unavailable in multi-profile mode. Full-profile equality
is reported separately because the driver checks only the first 24 bytes.

The host-only reader test derives the whitelist from the exact locked source,
then checks marker boundaries, prefix/full mismatch, forced/non-forced behavior,
multi-profile limits, malformed input, missing files and the size cap. It uses
only local fixtures. A live read awaits the user-built diagnostic boot; do not
present successful parsing as evidence that the attribute is already installed.

📱 SSH — Xiaomi lmi — 🔎 Read only — guarded diagnostic boot already confirmed

```sh
python3 /path/to/read-fg-profile-observer.py
```

Keep its result private with the manual boot manifest and first battery/kernel
snapshot. The normal permanent boot has no such diagnostic attribute. Do not
run the reader in WSL expecting it to read the phone; it must execute over SSH
on the confirmed diagnostic boot. This step needs neither camera/microphone
acquisition nor a cable manipulation.


### Reuse of the existing reviewed kernel — 2026-10-07

The operator requested persistent installation of the already built/tested
RPMh observer rather than another kernel build. The selected existing artifact
is `D-repro-01-power-rpmh-votes-diagnostic-boot.img`, 54,652,928 bytes,
SHA-256 `a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50`.
Both existing host copies match. This does not make the diagnostic a production
autonomy fix. Its RPMh attributes are available in the previously tested boot;
the newer guarded FG attribute, phandle fix and shadow-retry candidate are not
part of this image. Do not request another build merely to change observation
detail while the operator has selected this existing baseline.

The currently installed partition is a single `boot`, 134,217,728 bytes; no
boot A/B label or slot token was found. Its first 52,924,416 bytes exactly match
the existing original D-repro image, SHA-256
`0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad`.
That image is the available rollback baseline. This comparison covers the image
prefix, not an exact backup of all partition padding or any trailing metadata.
No new kernel or full-partition backup was created; the existing rollback image
was made accessible to the host flashing tool without modifying its bytes.

At this checkpoint persistent installation is prepared but not performed.
The constructor's historical temporary-only message remains its default policy;
the operator specifically authorized this persistent baseline for reproducible
comparisons across shutdown/restart. The operator performs Fastboot actions.
Only the boot partition is in scope; no userdata, firmware, recovery, vbmeta,
bootloader-lock or partition-layout change is requested. After installation,
identify the running build/config and diagnostic attributes, check the live DT
and gauge status again, and confirm basic display/touch/USB behavior. A reboot
alone is not proof that the requested candidate is running or that gauge state
is unchanged. Retain one working candidate and the rollback baseline; obsolete
diagnostic images can be removed after the retained installation is confirmed,
preserving the small recipes/manifests and evidence rather than daily binaries.

The guarded FG recipe/readers remain prepared research, not the next requested
manual build and not deployed functionality. Hardware profile comparison using
that new attribute is deferred unless a later justified build includes it.
