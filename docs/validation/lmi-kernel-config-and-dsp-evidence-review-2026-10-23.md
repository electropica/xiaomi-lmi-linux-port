# Pinned kernel configuration and regulator-readback review — October 23, 2026

The configuration extraction and source review were performed offline. A separate
one-shot read of the running Mobian /proc/config.gz and /proc/consoles confirmed
the configuration identity and active consoles. No register access, build or
policy change was made.

## Configurations extracted from the retained boot inputs

IKCONFIG was extracted directly from SHA256-verified boot images, not inferred
from an old defconfig or a branch name. Runtime releases were observed in the
paired capture separately. The input kernel hashes can be checked against the
permanent-menu asset manifests before applying this result to another build.

| Input | Mobian | LineageOS |
| --- | --- | --- |
| Boot SHA256 | a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50 | 9d7dd4823860f7ad73c82542669620b2cee1ca466789958175be63bb77e85411 |
| Kernel segment SHA256 | 87c53d33202d4607591fa0ba6d2bf091dc2dfc4673a3326436740a1f0e7bae6a | 632247727d42157c7e01a99317ba9c10a6c0dc941201722aa3a380d02483a1cc |
| Config SHA256 | c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78 | 6c168341dfa9987656c6f738dbd8e4a58a72a0381a3c0cdf072a5a3a7fba3a90 |
| Parsed config keys | 5319 | 5307 |

The Mobian config is byte-identical to the already-retained October 20
power-debugfs.config. The extraction resolves provenance; it does not create
a new candidate kernel. There are 84 raw key/value differences, including
absent versus explicitly disabled dependent symbols and toolchain metadata.
That number is not a count of independent power-policy differences.

PM_SLEEP, CPU_IDLE, QCOM_RPMH, QCOM_SMEM and MSM_CDSP_LOADER are enabled in both.
Thus the missing Mobian CDSP record cannot simply be attributed to compiling
out its loader. Loader presence does not establish that it was invoked.

DEBUG_FS is enabled on Mobian and disabled on LineageOS. This accounts for
the observed Android debugfs unavailability. MSM_IDLE_STATS is enabled only
on Mobian: the exact Kconfig selects it when MSM_PM and DEBUG_FS are enabled
(drivers/soc/qcom/Kconfig, lines763-779). Its dependent bucket settings follow.

The exact lpm-stats.c maintains histograms and counters from LPM entry/exit
callbacks. No timer, delayed work, wakeup source or runtime-PM get request was
found in this file. lpm-levels.c invokes its CPU/cluster/system entry and exit
hooks. This establishes bookkeeping overhead at those events, not a mechanism
for continuous load throughout a successful suspension. It does not justify a
new kernel build solely to remove those counters. Effects elsewhere remain
outside this limited source review.

Other differences include the custom Bluetooth UART path, RNDIS gadget support,
toolchain/LTO/hardening, security, filesystem options and debug-dependent
symbols. They are not automatically excluded as relevant, but no new causal
sleep-current mechanism is established by their configuration values alone.

## RPMh regulator values are cached requests in this driver

Exact a5b3099017ae drivers/regulator/rpmh-regulator.c was fetched independently:
SHA256 e24f271ce7627f1212dc2808ad7c217cc80aac61aa12547b268b4985b19f821c.
The qcom,rpmh-vrm-regulator compatible is registered at line1836.

- is_enabled(), lines887-892, reads vreg->req.reg[ENABLE].
- vrm_get_voltage(), lines1021-1031, reads vreg->req.reg[VRM_VOLTAGE], scaled
  by1000. It does not sample the physical regulator. A zero request is replaced
  with VOLTAGE_UNKNOWN=1; the comment at lines444-448 explicitly says this is
  used when the current voltage cannot be determined.
- arc_get_voltage_sel(), lines1197-1202, returns the cached ARC_LEVEL request.

The alternative qcom-rpmh-regulator.c likewise returns cached voltage_selector
and enabled fields. Reading these callbacks through regulator sysfs/debugfs
does not transform their results into measured AOP state or electrical voltage.
A zero-looking regulator-summary field is not proof of a physically off rail.

The three proposed CDSP/SLPI rails already occur in the preserved connected
and unplugged Mobian summaries. Those are awake request observations, not
suspend-state measurements. Re-reading them does not by itself answer what
unobserved remote votes or firmware retain in suspension.

## Evidence handling and next decision

Raw configs, full differences, the extraction script and source receipts remain
in private work/. No historical kernel input was changed or removed.
Before recommending a new rail comparison, identify whether its exact getter
reads hardware or a cached request and explain what unresolved hypothesis the
result could discriminate. Matched awake requests cannot close an unobserved
sleep-state question. The final independent CDSP/SLPI review has now been
received; its proposed rail observation is not an electrical discriminator.

Primary source anchors:

- [Pinned Kconfig](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/a5b3099017ae581aae8bf597b2f9c8c765026af1/drivers/soc/qcom/Kconfig#L763)
- [Pinned LPM bookkeeping](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/a5b3099017ae581aae8bf597b2f9c8c765026af1/drivers/soc/qcom/lpm-stats.c)
- [Pinned regulator getters](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/a5b3099017ae581aae8bf597b2f9c8c765026af1/drivers/regulator/rpmh-regulator.c#L1021)

## Review of the final MiniMax CDSP/SLPI report

The original report and proposal are preserved unchanged in private work/.
Useful findings: the identical master-stat reader gates remote records on SMEM
reachability; missing output is not physical-power evidence. The passive CDSP
loader and secure PIL loading path identify possible startup mechanisms, not a
demonstrated battery cause. Firmware not staged or requested is distinct from
firmware physically absent from the mounted vendor image.

The SSR enum starts at OFFLINING=0, registration uses kzalloc, and the inspected
stop path sets OFFLINING before shutdown and OFFLINE afterwards. The observed
labels are consistent with no successful framework startup, but a single label
cannot prove the entire history: an in-progress or stalled shutdown has the
same value. Neither interpretation measures power.

Three corrections are required before accepting the proposed next action:

1. The alleged non-APSS cross-clock error is not established. The reader adds
   arch_counter_get_cntvct() - last_entered for an open sleep episode. A large
   contribution is consistent with an old sleep entry on a shared counter.
   Computing that contribution's percentage does not establish different clock
   domains. An independent counter contract or offset/frequency observation is
   required. Remote durations remain unvalidated, not proven corrupt.
2. The exact RPMh getters above return cached requests. Matching connected-awake
   values cannot establish matching physical rails during suspend or close that
   physical hypothesis. Existing Mobian rail captures should be reused first.
3. Android DEBUG_FS is compiled out, not merely unmounted. Another debugfs mount
   cannot supply that interface. Regulator class entries also need discovery by
   their name attributes, rather than assuming human-readable directory names;
   subsystem numbers must be resolved by name and DT properties recursively.

The running Mobian config SHA256 is
c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78,
identical to the pinned input. This resolves the report's DV43-only config
uncertainty for the present Mobian kernel. Only pstore-1 is listed in the live
console list; serial console support is disabled in both extracted configs.
The console=ttyMSM0 token alone therefore does not justify a UART-console test.

Decision: no DSP start, SSR, mount, rail write or new discharge test follows
from this report. Retain the visibility/startup explanation; classify a DSP
power-saving benefit as unsupported and remote-duration calibration as open.
Any further source task must identify a concrete startup client or a genuine
hardware-state interface and state a falsifiable prediction before device use.

## Independent recheck of the retained October 22–23 night

The original collector JSON SHA256 is
38fea6fa2b6cb928ce083c1d085fa56e0a13ed01bf6550e2c80746f1fbc9e134.
An offline audit uses boottime for bracket elapsed time and monotonic for awake
time, checks their difference against each recorded suspend gap to within 2 ms,
rejects attached USB endpoints, and verifies non-overlapping brackets. It uses
no interpolation and does not integrate sparse instantaneous-current readings
across unobserved sleep. The raw captures remain private.

There are 29 detached brackets: 27063.320 seconds elapsed, 26917.803 seconds
suspended and 145.517 seconds awake (99.462% suspended). Their summed counter
decrease is 331716 reported microampere-hour units. One additional suspend-gap
event is rejected because it includes a USB-attached endpoint. This scope
excludes the initial awake period, inter-bracket gaps and recharging; it is not
the whole unplugged window.

For three equal boottime regions between the first and last selected bracket,
only complete brackets inside each region are used. Two crossing brackets are
omitted from this regional comparison, not split or interpolated:

| Region | Complete brackets | Suspended share | Counter units lost per hour |
| --- | ---: | ---: | ---: |
| First | 12 | 99.331% | 53077 |
| Middle | 8 | 99.495% | 42108 |
| Last | 7 | 99.566% | 36659 |

These rates are gauge-output quotients, not independently calibrated electrical
current. The declining rate persists with an elapsed-time denominator including
the awake portion. Dividing by suspended time alone instead inflates the
aggregate by about 0.54%, and the shortest bracket by about 4.14%; that arithmetic
choice does not explain the much larger chronological trend. The data do not
identify its cause: SOC, temperature, initial state and wake frequency are not
independent controls. They do not justify fitting an electrical cost per wake
or attributing the trend exclusively to gauge correction.

No new phone test, build, calibration or protection change was performed for
this audit. A future matched comparison must preserve channel identity, exclude
charging/rebasing boundaries, and state whether it tests gauge behavior or a
specific power-policy hypothesis. Repeating an unchanged standby test would not
resolve the outstanding measurement scale.

## Matched gauge-channel coverage follow-up

## Decision

Prepare one common explicit reader for a future already-awake OS visit, not a
new standby test. Nothing was deployed or read from the phone for this review.
The reader is `userspace/power/diagnostics/matched-gauge-snapshot.sh`. It is intentionally not
armed and cannot determine sleep current from a single observation.

## Verified source identity and channel contracts

The retained exact-source manifest pins Mobian a5b3099017ae581aae8bf597b2f9c8c765026af1
and Android 71b13e62f057a649b77fe4062feb73ee72ad609c. Both qpnp-fg-gen4.c
files hash to 0f5676829cb2a40daa191a456998c700d744afe8346e07dd3c7af2a7e8685957.
This verifies identical source for this file, not identical gauge firmware,
configuration, learned capacity, SRAM contents or init behavior at runtime.

- charge_counter: CC_SOC_SW times learned capacity / CC_SOC_30BIT (793–812).
- charge_counter_shadow: BATT_SOC times learned capacity / BATT_SOC_32BIT
  (814–835). It is not an independent electrical meter.
- charge_now_raw: CC_SOC times nominal capacity / CC_SOC_30BIT (preceding
  getter, dispatched at 5269). Its scale cannot be equated to the software
  counter simply because both attributes use charge units.
- current_now and current_avg dispatch at 5236 and 5239; the latter uses
  FG_SRAM_IBAT_FLT. Its filter cadence during suspend remains unestablished.
- The retained qpnp-smb5.c battery CHARGE_COUNTER getter forwards to BMS at
  3158–3160. This verifies that forwarding path in the retained source; the
  exact Android health-service selection/overrides are not established here.

## Existing evidence and the missing comparison

The two retained Android batterystats histories used in the unplug analysis
contain rounded software-charge history, not a matched time series of raw,
shadow, filtered-current and capacity channels. Searching their saved JSON
also finds none of the charge_counter_shadow, charge_now_raw, current_avg or
charge_full attribute names. This is a coverage statement about those two
artifacts, not every Android capture in the project.

Mobian's October 15 awake discharge control found software-counter/integrated
current ratio 1.009 and raw-counter/integrated-current ratio 1.739. The latter
was close to design/learned capacity 1.720, without establishing a universal
normalization rule. That control cannot calibrate Android or suspended current.
Do not repeat that already-completed Mobian-only control.

The October 22–23 night audit confirms a changing software-counter rate while
suspension remains high, but cannot choose between a changing physical load and
gauge state. This is why a GPU result and a gauge result must remain distinct.

## Reader scope and interpretation

Explicit read list avoids uevent and charge_done. Missing supplies, missing
files and failed reads have different output tags; none is converted to zero.
Raw signs are retained, and /proc/uptime brackets the sequential snapshot.
The reader does not mount, write a property, acquire an inhibitor, poll, start
a service or request suspend. Telemetry getters themselves can briefly access
gauge SRAM, so this is not a zero-overhead suspended measurement.

A single future Android snapshot can verify channel availability and capacity
scale. A connected snapshot cannot measure detached consumption or establish
the history of a counter. Any subsequent paired discharge protocol must have
qualified detached endpoints and a causal question before it is armed.

No new physical action is requested now. MiniMax's GPU investigation remains
independent and its result should be reviewed before selecting the next test.

## Comparative report identity and runtime-policy correction

The original report is preserved outside the repository under the user's
MiniMax dossier. Its central device identity is wrong: the actual handset and
project are POCO F2 Pro / lmi, not surya. Official LineageOS device metadata
identifies lmi variant 1 as POCO F2 Pro with Snapdragon 865; surya is POCO X3
NFC with Snapdragon 732G. Therefore the proposed lmi-to-surya transfer matrix
and a missing-surya-DT blocker do not apply to this project.

Primary identity reference:
https://github.com/LineageOS/lineage_wiki/blob/main/_data/devices/lmi_variant1.yml

## Scale-mode claim checked against preserved and current evidence

The claim that Mobian scale_mode_en was never read is false. Retained October
16 gauge-percentage data has scale_mode_en=0; the October 21 runtime flag
snapshot also records cached_scale_mode_en=0. A bounded current read now
confirms bms/scale_mode_en=0 again. This does not calibrate the other gauge
channels or prove that every internal state remained identical throughout a
discharge. It removes the stated missing-read premise for this flag.

## Actual LPM topology instead of assumed Android script paths

One connected-awake read found no attributes under the proposed
/sys/module/lpm_levels/system subtree. A second bounded topology read established
that this is a path mismatch, not an empty supported-state set:

- module root contains parameters and L3;
- L3/l3-wfi and L3/llcc-off both expose idle_enabled=Y and suspend_enabled=Y;
- L3/cpu0 through cpu7/rail-pc all expose idle_enabled=Y and suspend_enabled=Y;
- cpu0 cpuidle state0 is C0/wfi and state1 is C1/rail-pc, both disable=0;
- sleep_disabled=N.

The live config hash still matches the pinned Mobian input:
c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78.
These are policy permissions, not proof that a state was physically reached.
The topology must not be misread as equivalent to unrelated system/pwr/perf/ret
nodes. No attribute was written and no suspend/discharge was requested.

The retained Android post-boot script has several platform branches with
different paths. Near lines 3251–3260 it writes ten system/perf|pwr/ret paths;
near lines 5980–5991 it writes twelve paths with different CPU group labels.
A source occurrence is not proof of a successful write on this device.
In the pinned lpm-levels.c, idle selection calls lpm_cpu_mode_allow(..., true)
around line 714, whereas system suspend scans deepest-first with
lpm_cpu_mode_allow(..., false) around line 1734. This is enough to reject
assuming an idle_enabled path is automatically the system-suspend control;
the helper implementation and actual Android topology still require matching.

## GPU claim and prioritization

The comparative report restates an old gpu_cx_gdsc difference that the separate
GPU review withdrew after source and event-order analysis. Do not treat it as
the sole surviving difference without resolving that contradiction. Conversely,
identical GPU source/DT does not exclude differing runtime votes or firmware.

Decision: no build or policy copying follows from this report. Correct device
identity first; compare the actual LPM hierarchy on the next already-planned
Android visit, before considering any retention-policy experiment. Do not
repeat the scale_mode read as if it were missing evidence. Existing peripheral,
modem and gauge questions remain scoped separately.

Private receipts: battery-lpm-policy-20261023-private.json and
battery-lpm-topology-20261023-private.json. Reads used only existing USB SSH;
no firmware, GPIO, regulator, protection, service or policy control was changed.

## LPM source follow-up accepted with runtime limits

Verified the supplied lpm-idle-versus-suspend-review against pinned sources.
lpm-levels-of.c:317–341 chooses independent idle_enabled/suspend_enabled fields
using from_idle. lpm_suspend_enter passes false in the CPU loop and passes false
to cluster_prepare; cpu_power_select passes true. This rejects the proposed
direct system-suspend fix based on ret/idle_enabled=N.

In the retained Android post-boot script the kona block begins at 5673–5674
and ends after sleep_disabled=N at 5841. It contains no proposed ret writes.
Those writes belong to other platform branches. The runtime Mobian hierarchy
is L3, with rail-pc and llcc-off permitted for both idle and suspend.

Scope accepted: no demonstrated missing kona retention policy in this script;
do not copy the proposed ret writes. Scope not accepted: permanent exclusion of
all LPM differences, assertions about successful/failed Android writes without
runtime evidence, or 'nobody changes defaults' merely because current values
match defaults. Actual Android permissions/topology remain unobserved.

The supplied reader is preserved unchanged, not executed. Its claims of reading
only three LPM attributes are inaccurate: it also reads full /proc/cmdline,
mem_sleep, pm_async and wakeup_count, and invokes Android-only getprop. A stricter
cross-OS reader is prepared as userspace/power/diagnostics/lpm-policy-snapshot.sh. It reads only the
three attribute names under lpm_levels and a non-unique kernel release. No
phone contact was needed for this acceptance; no policy/build/test changed.

Next already-planned Android visit: use the bounded LPM reader and existing
matched-gauge reader in the same awake session. No unplug or extra long test is
needed to establish availability and current policy flags. A matched result
closes that specific permission/topology comparison, not physical LPM state.
