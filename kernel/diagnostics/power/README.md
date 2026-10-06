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
has passed Python syntax checks; hardware validation remains pending.
