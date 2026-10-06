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
