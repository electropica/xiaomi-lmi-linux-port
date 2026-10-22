# MiniMax battery investigation — progress ledger

Branch: `codex/minimax-battery-20261022`. Base: `0e9c3e73c2f208c0ca00636ad06015278574c69c`.
Ownership: MiniMax investigates, implements focused fixes and validates on this
branch; Julien operates the phone and runs heavy builds. Raw captures,
identifiers and private logs stay outside Git.

This ledger records one entry per bounded task: hypothesis, artifact identity,
evidence, changes, validation, limitations, next decision.

---

## Entry 1 — 2026-10-22 — UFS measurement gap: classifier, identity guard, source mapping

**Hypothesis.** The UFS suspend policy differs between the LineageOS reference
and Mobian in a way that could keep a rail powered across a suspend window,
and the earlier Android capture was not sufficient to decide it because the
existence oracle was wrong and the reads were unprivileged.

**Artifact identity.**
* Retained Android capture: `work/minimax-rpmh-audit-20261022/ufs-lineage-live.txt`
  (2026-10-22 13:56:11 UTC), preserved with hashes in the private workspace.
* LineageOS device ROM family `Redmi/lmipro/lmipro:12/…`, kernel
  `4.19.325-cip131-st15-perf-g71b13e62f057`.
* Mobian base kernel `a5b3099017ae581aae8bf597b2f9c8c765026af1`.
* Android reference kernel `71b13e62f057a649b77fe4062feb73ee72ad609c`.
* Driver `drivers/scsi/ufs/ufs-qcom.c` identical on both sides, sha256
  `5914361ac55598d1e2ffb6105bbe161d93536aba7144310cc67cb94d400ac739`.
* LineageOS init policy `init.qcom.power.rc` @ `da4ba935`, sha256
  `86780f04dd6da0161165997240610bd10951dec41beee142034fc4626ff37669`.
* Retained Mobian snapshot `work/ufs-suspend-policy-private.json` (2026-10-12,
  plugged, root, older uncertified build).

**Evidence.**
1. The unprivileged ADB shell is denied `getattr()` by SELinux on the UFS
   attribute files: `ls -la` prints `-?????????`, `stat` and `cat` are refused,
   and `test -e` is **FALSE for entries the listing shows**. The earlier
   summary therefore mislabelled refusals as absences.
2. A successful listing of the UFS host root does **not** contain
   `clkscale_enable` nor `clk_scaling_enable`. The LineageOS init writes to
   `clkscale_enable` at `on init`, `on enable-low-power` and `on charger`; on
   this kernel those writes fail, so the only effective UFS knob in the init
   policy is `clkgate_enable`.
3. `ufs_qcom_suspend()` (identical driver) decides the VDD parent
   reference-clock regulator from `rpm_lvl` / `spm_lvl` and the hibern8 state
   (`ufs-qcom.c:893-901`). No init write touches `rpm_lvl`, `spm_lvl` or
   `auto_hibern8` on either side, so those should be driver defaults on both.
4. The only OS-level UFS policy difference identified is `clkgate_enable`:
   Android writes it (1 at `sys.boot_completed` and on charger, 0 during
   `on init`), Mobian never writes it. The retained 2026-10-12 Mobian snapshot
   recorded `clkgate_enable=1`, plugged, on an older uncertified build.
5. `sleep_disabled` converges to `N` on both platforms (Android through the
   device post-boot script, Mobian through `lmi-cpu-idle.service`); it is not
   a differentiator.

**Changes.**
* `userspace/power/diagnostics/ufs-policy-read.py` — read-only reader:
  listing-based existence oracle, `UNKNOWN` on a failed listing, `DENIED` on
  an explicit permission failure, `LISTED_BUT_UNREADABLE` when a listed name
  cannot be read, strict exact-membership identity guard, UID/GID/SELinux
  context recorded, plan-only by default, one shot with `--execute`.
* `userspace/power/diagnostics/ufs-policy-read.sh` — the remote read-only
  snippet over fixed paths covering policies, link/device targets, runtime
  bookkeeping and the available PHY/clock attributes.
* `userspace/power/diagnostics/test-ufs-policy-reader.py` — classifier and
  guard tests.
* `docs/validation/lmi-ufs-policy-comparison-2026-10-22.md` — the comparison
  and its limits.

**Validation.** `sh -n` on the snippet; the reader self-test and the repo test
file both pass, covering failed listing, listed-but-denied,
listed-but-unreadable, true absence, both scaling spellings classified
independently, and four identity-guard cases (substring rejected, exact
device accepted, unknown build rejected, foreign ROM rejected).

**Limitations.**
* The absence of the two clock-scaling spellings is established **only for the
  inspected Android directories**. It is not established under Mobian and not
  universal across the kernel.
* `ufs_core.c` was not reachable from the public mirrors tried, so the
  attribute show/store implementations, units and defaults are not
  established from source; only their use in the suspend path is.
* The Android observations come from the Android reference kernel; the Mobian
  observations come from an October 12 plugged snapshot on an uncertified
  older build. The comparison spans two kernel states and two OS
  environments.
* A policy value is configuration. Policy equality does not prove physical
  state equality, and no physical current was measured.

**Next decision.** Obtain one privileged read-only snapshot per platform over
the identical fixed paths — LineageOS through `adb root` (operator action,
reversible, no persistent change) and Mobian over the existing SSH route with
USB connected — then compare `clkgate_enable`, `rpm_lvl`, `spm_lvl`,
`auto_hibern8` and the `*_target_link_state` / `psa_state` values. Until those
exist, the UFS comparison stays **UNKNOWN**. No further UFS test is proposed,
and no discharge test is justified by the present evidence.

---

## Entry 2 — 2026-10-22 — ranking of unresolved client/configuration differences

**Hypothesis.** At most three concrete client or configuration differences
remain that could discriminate the standby residual. They are taken from the
existing peripheral checklist and from retained evidence, not from a new broad
audit.

**Artifact identity.**
* Checklist `docs/validation/lmi-standby-peripheral-checklist-2026-10-20.md`
  and the driver-coverage note of the same date.
* LineageOS reference raw trace, four complete suspend windows.
* Mobian 2026-10-12 wide observer raw trace: the only Mobian trace with
  `complete_trace_possible: true`, no overrun, no unmatched call and a
  190.634 s userspace-qualified sleep.
* Mobian 2026-10-12 forced observer trace: qualified durations, cpu3 overrun
  7307, narrow regulator capture.
* `drivers/scsi/ufs/ufs-qcom.c` identical on both kernels, sha256
  `5914361ac55598d1e2ffb6105bbe161d93536aba7144310cc67cb94d400ac739`.

**Evidence and ranking.**

**R1 — display panel VCI release timing (ranked first, concrete difference).**
On the LineageOS reference `display_panel_vci` and `pm8150_l14` are released
at screen-off, 255.08 s / 596.07 s / 1196.06 s / 1796.07 s before the
corresponding suspend entry. On the Mobian wide trial they are released
0.301 s before the suspend entry, inside the suspend path, with no enable event
in the 110.6 s of preceding coverage, and they are not re-enabled in the
observed post-resume window. Mechanism: the panel rails stay **requested**
through the whole screen-off to suspend idle gap on Mobian, and are released
early on the reference. The gap is governed by the inactivity delay, and the
shipped Mobian profile sets `sleep-inactive-battery-timeout=900`
(`build/profiles/lmi-current/94_lmi-current-power.gschema.override`). This is
invisible to a deep-suspend current measurement because the rail is off
during the sleep on both platforms; it would appear in daily consumption.
Counter-evidence: a regulator request is not a current measurement, the
Mobian build is uncertified, and the length of the Mobian idle gap is not
measured. Discriminator: one awake, read-only observation of
`display_panel_vci` and `pm8150_l14` during the idle gap, on both platforms,
with the screen-off to suspend interval recorded.

**R2 — UFS suspend policy values (measurement gap, not yet a difference).**
The UFS platform driver is byte-identical, so any difference is in values.
Neither clock-scaling spelling exists in the inspected Android directory, which
closes that gap locally. The only OS-level write difference identified is
`clkgate_enable`: the reference writes it (1 at `sys.boot_completed` and on
charger, 0 during `on init`), Mobian never writes it and keeps the driver
default. `rpm_lvl`, `spm_lvl` and `auto_hibern8` are written by nobody on
either side, and the suspend-path reference-clock decision depends on them
(`ufs-qcom.c:893-901`). Counter-evidence: the retained Mobian snapshot says
`clkgate_enable=1`, `rpm/spm_lvl=3`, `auto_hibern8=1000`, but it is plugged,
older and uncertified. Discriminator: the privileged read-only snapshot
already prepared (`userspace/power/diagnostics/ufs-policy-read.py`).

**R3 — always-on and shared rails (structurally invisible to the method).**
An `always-on` regulator emits no enable or disable event at all, so the
transition comparisons used so far cannot see that class. `vdd_boost_vreg`
(`regulator-always-on`, PM8150B GPIO 5, shared with `pm8150b_haptics` and
`aw8697_haptic@5A`) is the concrete instance, and the haptics sharing is why
releasing it is not a trivial change. The retained Mobian `regulator_summary`
snapshot shows the consumer lists that make this class analysable. Discriminator:
the same privileged read-only snapshot, reading the regulator summary instead
of the UFS policy.

**Changes.** `docs/validation/lmi-panel-vci-release-timing-2026-10-22.md`
added; the peripheral checklist display row annotated with the new transition
evidence; the ranking recorded here.

**Validation.** The panel timings were extracted from the retained raw traces
with a dedicated offline extractor; the four LineageOS windows agree on the
pattern, and the Mobian value comes from the only Mobian trace that is
complete. No device contact.

**Limitations.** A regulator transition is a request, never a calibrated
current. Missing `pm_genpd` nodes, successful PM callbacks, zero logical votes
and absent trace events are not electrical exclusions. The Mobian evidence is
from an uncertified older build. R2 and R3 are measurement gaps, not
differences.

**Next decision.** One bounded, awake, read-only measurement resolves R1 and,
with the same capture, R2 and R3: read the display panel rail state during the
screen-off to suspend idle gap, and read the UFS policy values and the
regulator consumer lists, on Mobian and on the LineageOS reference, over
identical fixed paths. This needs the privileged ADB route on LineageOS and
the existing SSH route on Mobian with USB connected. Until that happens, all
three rows stay as they are: R1 is a measured timing difference of unmeasured
magnitude, R2 and R3 are unobserved.

## Entry 3 — 2026-10-22 — pending operator actions

**Hypothesis.** The remaining uncertainty is measurement access, not analysis.

**Artifact identity.** `userspace/power/diagnostics/ufs-policy-read.py`,
`userspace/power/diagnostics/ufs-policy-read.sh`,
`userspace/power/diagnostics/test-ufs-policy-reader.py`.

**Evidence.** The ADB device is authorised and unique, but `adbd` runs as
`uid=2000(shell)` in SELinux context `u:r:shell:s0`, which is denied the UFS
attribute reads and the regulator summary. The build is `userdebug`
(`ro.debuggable=1`), so the privileged route is `adb root`, which restarts
`adbd` as root and is reversible with `adb unroot`; it is an access change,
not a persistent setting change, and it is not performed here.

**Changes.** None beyond the reader and its tests.

**Validation.** The reader resolves the Windows `adb.exe` from the mounted C:
volume, prints a PowerShell-readable snippet path, and its plan mode contacts
nothing.

**Limitations.** `adb root` is an operator decision; the reader never performs
it. The Mobian route needs the cable connected and the phone awake.

**Next decision.** Await the operator: (a) authorise `adb root` for one
read-only snapshot on the LineageOS reference, and (b) make Mobian available
with USB connected for one read-only snapshot over the same fixed paths, with
an awake read of the display panel rail during the idle gap.


## Entry 4 — 2026-10-22 — privileged LineageOS read and the UFS narrow result

**Hypothesis.** The UFS suspend policy differs between the two platforms in a
way that could keep a rail powered across a suspend window. The privileged
read should either expose a value difference or close the value question for
the attributes that exist on both sides.

**Artifact identity.** One privileged LineageOS read, 2026-10-22 16:44 local,
kernel `4.19.325-cip131-st15-perf-g71b13e62f057`, ROM family
`Redmi/lmipro/lmipro:12/...`, USB connected, device awake, shell `uid=0(root)`
in SELinux context `u:r:su:s0`. The Mobian side is the retained 2026-10-12
root snapshot. The raw capture stays in the private workspace, outside Git,
with its SHA256 recorded in the private evidence manifest.

**Evidence.** At the moment of the read `usb_online=1` and every directory
listing succeeded (`failed_listings: none`). The five UFS policy attributes
that exist on both sides read **identically** on the two platforms:
`clkgate_enable=1`, `clkgate_delay_ms=50`, `rpm_lvl=3`, `spm_lvl=3`,
`auto_hibern8=1000`. Neither clock-scaling spelling is enumerated on the
reference. The reference additionally reports
`rpm/spm_target_link_state=HIBERN8`, `rpm/spm_target_dev_state=SLEEP`,
`attributes/psa_state=0x00000000`, `attributes/current_power_mode=0x00000011`,
`qcom/power_mode=[Rx,Tx]: Gear[4,4], Lane[2,2], PWR[FAST MODE,FAST MODE],
Rate-A`, `max_bus_bw=0`, `qcom/clk_status=0`, `qcom/bus_speed_mode=0`.

**Changes.** The reader now carries the enumerated listing names in its
summary, so an absence claim is auditable from one capture, with a test for
it. The UFS comparison note, the panel note, the peripheral checklist and this
ledger are updated. The privilege was restored in the same script: after
`adb unroot` the shell was back to `uid=2000(shell)`, context `u:r:shell:s0`.

**Validation.** Reader self-test and the repository test file pass. The
privileged read is reproducible with the committed reader; the restoration of
the unprivileged state is recorded in the capture.

**Limitations.**
* The read is plugged and awake. It is **not** a sleep observation, it does
  not identify which consumer holds a rail, and it does not measure a current.
* An identical `ufs-qcom.c` excludes nothing elsewhere in the UFS stack: the
  show/store implementations live in `ufs_core.c`, which was not compared and
  was not reachable; the device tree overlays were not compared; other
  consumers of the same rails are outside that file.
* A regulator disable event is a request, not proof of an electrical cut.
* The Mobian side of the newer attributes is still missing.

**Next decision.** The remaining Mobian datum is one reader run over the same
extended paths with USB connected, so the target, PSA and power-mode attributes
can be compared. Until then the UFS value comparison stays open for the newer
attributes and closed for the five shared ones. R1 (display panel rail
timing) is unaffected by this read and still needs its own awake observation.


## Entry 5 — 2026-10-22 — Mobian privileged capture: R2 closed for the policy

**Hypothesis.** The Mobian and LineageOS UFS suspend policies differ in a way
that could keep a rail powered across a suspend window. A privileged capture on
the current Mobian kernel over the identical fixed paths should either expose
the difference or close the value question.

**Artifact identity.** One capture over the existing SSH route, root, USB
connected, device awake, about 110 s after boot, kernel
`4.19.325-cip128-st12-perf-ga5b3099017ae-dirty`, i.e. the **current** Mobian
kernel. The raw capture stays in the private workspace outside Git, with its
SHA256 in the private evidence manifest.

**Evidence.** Every directory listing succeeded. **Every UFS policy attribute
observed on both platforms has the same value**: `clkgate_enable=1`,
`clkgate_delay_ms=50`, `rpm_lvl=3`, `spm_lvl=3`, `auto_hibern8=1000`,
`rpm/spm_target_link_state=HIBERN8`, `rpm/spm_target_dev_state=SLEEP`,
`spm_target_link_state=HIBERN8`, `spm_target_dev_state=SLEEP`,
`attributes/psa_state=0x00000000`, `attributes/current_power_mode=0x00000011`,
`attributes/bkops_status=0x00000000`, `attributes/active_icc_level=0x0000000F`,
`qcom/power_mode` identical, `qcom/bus_speed_mode=0`, `max_bus_bw=0`,
`qcom/err_count` all zero, `qcom/err_state=0`. Neither clock-scaling spelling
nor `auto_bkops` is enumerated on either platform. The only differing reading
is `qcom/clk_status`, 0 on the reference and 1 on Mobian, which is a **live
clock status**, not a configured value.

The same session's regulator summary shows `vdd_boost_vreg` with `use=1`,
`open=1` and a single `deviceless` consumer, a rail enabled by its own
`regulator-always-on` declaration that emits no transition; and
`display_panel_vci` / `pm8150_l14` each with `use=1`, `open=2` and the consumer
`soc:qcom,dsi-display-primary`; `gpu_cx_gdsc` with `use=0`, `open=4`.

**Changes.** The UFS comparison note and the peripheral checklist record the
complete comparison; the always-on instance is documented.

**Validation.** The reader ran unchanged over the SSH route and produced
verdicts consistent with the privileged ADB capture, and every listing
succeeded on both platforms, so the absence claims remain auditable.

**Limitations.**
* Both reads are plugged and awake. They compare policy and consumer
  bookkeeping, not the physical state during a suspend, and they measure no
  current. The Mobian capture was about 110 s after boot, so its consumer
  lists are an early-boot state.
* The earlier correction stands: an identical `ufs-qcom.c` excludes nothing
  elsewhere in the UFS stack, and a regulator disable event is a request, not
  proof of an electrical cut.

**Next decision.** R2 is closed for the policy and is no longer a candidate.
R1 needs its own observation of the panel rails with the screen off and the
system still awake, and the consumer that holds them is now identified as
`soc:qcom,dsi-display-primary`. R3 has a concrete instance
(`vdd_boost_vreg`, always-on, single `deviceless` consumer) whose state
during the suspend is still unknown.


## Entry 6 — 2026-10-22 — R1 refuted on the current build; matched collector prepared

**Hypothesis.** R1, the display panel rail timing, holds on the current Mobian
build: the panel rails would stay requested through the screen-off to suspend
idle gap. The discriminator is a point-in-time regulator summary read with the
system awake and untouched, compared with a read taken while the panel was
still lit.

**Artifact identity.** Two point-in-time `regulator_summary` reads over the
existing SSH route, root, USB connected, current Mobian kernel
`4.19.325-cip128-st12-perf-ga5b3099017ae-dirty`: one at 16:53 local, about
110 s after boot, one at 17:00, about 536 s after boot, untouched in between.
Raw captures stay in the private workspace outside Git.

**Evidence.** In both readings the consumer of `display_panel_vci` and
`pm8150_l14` is `soc:qcom,dsi-display-primary`, which holds them **open**
(`open=2`) throughout; the **enable** count changes from 1 to 0 while the
system stays awake and is not touched. The retained 2026-10-12 summary shows
the same consumer and the same `open=2` with `use` toggling 0 -> 1 -> 0, so the
release-at-blank path exists on that build too. `vdd_boost_vreg` reads
`use=1`, `open=1`, single `deviceless` consumer in every reading, and
`gpu_cx_gdsc` reads `use=0`, `open=4`.

**Changes.** The panel note records the current-build reading and withdraws the
earlier statement that Mobian keeps the panel rails requested through the idle
gap; the peripheral checklist display row is annotated; the matched collector
is added as `userspace/power/diagnostics/collect-matched-standby-window.py`.

**Validation.** The collector is read-only, plan-only by default, detects the
suspend from the CLOCK_BOOTTIME / CLOCK_MONOTONIC divergence already used by
the project observer, and writes one JSON file. Its plan mode contacts
nothing.

**Limitations.**
* The absolute screen state is not directly readable on this platform: the DRM
  connector reports `connected` either way and the OLED panel has no
  backlight. The conclusion is **differential**, from the enable count
  changing while the system stayed awake and untouched.
* A regulator `use` count is a framework state, not an electrical
  measurement, and the reading says nothing about the sleep interval.
* The readings are point-in-time and single-occurrence.

**Next decision.** R1 is refuted and R2 is closed for the policy, so the
standby difference is not in the UFS policy and not in the display panel
rails. What remains unmeasured is the **comparison method itself**: the
Mobian standby figure has never been produced by the Android reference
method, so the two platforms have still never been compared like for like.
The single bounded discriminator is therefore one matched Mobian standby
window, collected locally on the phone because the SSH route needs the cable
connected and an unplugged suspend cannot be observed over it. That needs
Julien's agreement and a local collector run, and it is prepared, not
proposed as a generic discharge test.


## Entry 7 — 2026-10-22 — collector clock defect corrected offline; the 15:21-15:47 window reclassified

**Review.** An independent review of this branch
(`work/MINIMAX-BRIEF-REVIEW-20261022.md`, outside Git) found a blocking
defect in the matched standby collector before any handset run could rest on
it. It is recorded here with the correction, because the defect changes what
the previous collector output means.

**The defect.** `collect-matched-standby-window.py` read `/proc/uptime` and
returned its two fields as `boottime` and `monotonic`. The second field of
`/proc/uptime` is the aggregate CPU idle time summed over every CPU, not
`CLOCK_MONOTONIC`. `suspended_accumulated` was therefore meaningless, the
suspend detection could not fire on real suspends, and every duration in the
output was invalid. On the host the pair read `uptime=39631.42`,
`monotonic=631946.02`, which is the wrong order and gives
`suspended_accumulated = -592314.6`.

**The correction.** The collector now uses
`time.clock_gettime(time.CLOCK_BOOTTIME)` and
`time.clock_gettime(time.CLOCK_MONOTONIC)` and refuses to collect, with exit
code 2, when either is unavailable. A suspend is detected as the growth of
the difference between two readings, not as an absolute difference, because
the monotonic clock is slewed by the timekeeping layer and the boot clock is
not. The wall-clock deadline moved to `CLOCK_BOOTTIME`, which keeps counting
across a suspend; the previous `time.monotonic()` deadline did not bound the
real duration of the window. No RTC wake alarm was added, because a periodic
wake would be a new wake source on a device whose wake sources are what is
under study. Suspend events are kept as a bounded sequence instead of only
the first. `--poll` and `--max-seconds` reject non-positive and non-finite
values. The counter statement that it "does not move while the processor is
down" was removed: it was an assertion about the gauge, not a measurement.

**Validation.** `userspace/power/diagnostics/test-collect-matched-standby-window.py`
is new and offline: 18 tests, no phone contacted. They cover the awake
passage, a synthetic suspend gap of a known duration, the resume after it,
several suspends kept as a sequence, the USB transitions, the bounded event
list, the wall-clock deadline, the refusal of a missing clock, the refusal of
invalid sampling arguments, the preservation of the counter jump across the
unplug, the reporting of the suspended fraction, the absence of any claim of
a calibrated current, and the clock slew. The same suite run against the
previous implementation from `HEAD` fails immediately. `test-ufs-policy-reader.py`
still passes with 10 tests.

**The window reclassified.** The kernel log of the 15:21-15:47 unplugged
window was analysed separately, because the collector's own clock was invalid.
The device suspended twice, for 379.217 s and 57.005 s, total **436.222 s**,
resumed by IRQ 438 `msoc-delta` and IRQ 445 `esr-delta`. The same figure
comes out of `CLOCK_BOOTTIME - CLOCK_MONOTONIC` measured on the awake,
reconnected device, to within a millisecond. The unplugged interval is
1554.1 s, so **the phone was awake for about 72 % of its own unplugged
window**. The `upower` charge history agrees from the userspace side.

The screen wake observed by the operator at about 17:45 local is in the log:
the display was blanked at 15:22:04 UTC after the unplug and programmed
again at 15:44:37.345 UTC, 0.16 s after the second resume, with no operator
action.

**Correction to the framing.** The previous entry said the single open
question was "produce the Mobian figure by the Android method". The window
shows the question is different: the Android reference is 98.9 % asleep over
its 30m44s interval, and the Mobian window is 28 % asleep over its interval.
A like-for-like number needs the duty cycle equalised, or the comparison has
to be stated as a duty-cycle difference rather than a current difference.

**Limitations.** The suspend intervals come from the kernel log, not from the
corrected collector, so they do not prove the corrected collector works. One
window, one build, one state of charge. The 168.3 mAh figure is a raw
counter difference between the reading before the unplug and a reading
taken while the device was charging after the reconnection; it spans the
unplug and the subsequent recharge, so it is not an attributed window
consumption and cannot yet be split into consumption and discontinuity.
The gauge scale against the design capacity is not established. No current is
measured anywhere in this entry.

**Next decision.** One second matched window with the corrected collector, to
confirm the suspend intervals and the awake fraction with a correct
instrument and to read the counter on both sides of the unplug. It needs the
operator's unplug and replug, and it produces the Mobian window figure and
the unplug discontinuity, not a calibrated current and not an explanation of
the standby difference.
