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
## Entry 8 — 2026-10-22 — collector revision 3: the review defects fixed offline, failing tests first

**The review.** The independent API review of 2026-10-22 confirmed five
defects in revision 2 of the collector and rejected several of its claims.
The results are kept outside the repository, in
`work/MINIMAX-API-REVIEW-RESULTS-20261022.md`.

**The sources were checked, not taken on trust.** In
`drivers/scsi/ufs/ufs-sysfs.c` (sha256 `3e5307ab1eea…`, byte-identical
between the Mobian and the Android revision), the `UFS_ATTRIBUTE` macro at
lines 711-726 calls `pm_runtime_get_sync()`, `ufshcd_query_attr()` and
`pm_runtime_put_sync()`, and `current_power_mode` (line 729) and
`psa_state` (line 742) instantiate it. In `ufshcd.c` (sha256
`cc3b00465c2c…`), line 4229 documents `ufshcd_query_attr` as the API that
sends attribute requests. So each read of those two attributes
runtime-resumes the UFS device and sends a hardware query: it is not a
passive observation of a sleeping device. The attributes that stay in the
sampling loop were checked too and are not hardware queries.

**The five defects, fixed.** One pair of samples can now carry a suspend
gap and a USB transition at the same time; the event log is bounded
without the totals depending on its capacity and without the terminal
transition being droppable; the deadline carries an explicit boot-clock
value and a wall-clock value instead of a boot-clock value printed as a
date; the result is written before the first event and every write is
atomic, with a signal handler writing the final result; the two UFS
hardware-query attributes are no longer read during the window, and a
one-shot snapshot is available behind an explicit flag.

**The claims that were rejected, corrected.** Both clocks derive from
adjusted monotonic time, so the collector no longer claims that one of
them is slewed and the other is not. A normal timer is not a wake source
that would prevent a system suspend, and the limits now say what the
polling really costs. The USB boolean is a proxy: transport, power and
charge are reported apart, and only a reading taken with no power source
attached is kept as a discharge endpoint. The difference across the
unplug is no longer called a jump and is no longer presented as a
consumption figure. The result no longer claims to keep every sample.

**The tests.** The suite now holds 28 tests, and the collector under test
is selected by `MINIMAX_COLLECTOR`, so the same suite runs against the
previous revision taken from the history. Against revision 2 (`32bc1c2c…`)
it gives **13 failures**, every one of them a confirmed defect. Against
revision 3 (`67d0dca6…`) it gives **0 failures**. The other suite,
`test-ufs-policy-reader.py`, still passes with 10 tests. No test mirrors
the implementation: each drives the module with synthetic samples and
checks an observable.

**What was not touched.** The ESR IRQ, the charge protections, the normal
sleep delay and the Phosh and GSD thresholds. The `50000` threshold is
50 ms, not 50 s, because `lmi_sleep_total` counts microseconds; it was not
modified. No RTC wake alarm was added, no policy, setting or permission
was changed, and no kernel code was modified.

**The armed run produced no window.** The revision-2 collector started on
the phone at 17:08:10 UTC ran its full hour and stopped on its own
deadline at 18:08:13 UTC. The cable was never removed, so there was no
window: the phone stayed plugged in and did not suspend for a single
second, the accumulated suspend time did not move at the 436.2216 s it
had carried since the first window, and the counter went from 2676996 up
to 2677000, which is `charge_full`, one more observation of a counter
that is remaining charge and rises back while charging. That run also
shows the perturbation of the fifth defect in the open: it read the two
UFS attributes on every poll for an hour.

**Limitations.** Revision 3 has not run on a handset. Nothing about the
physical standby draw follows from this entry. The window remains a gauge
reading, with no calibrated current and no established scale against the
design capacity. The first window is still void as a collector result;
its kernel-log analysis stands on its own. On the duty cycle: with a
900 s inactivity delay, a 1554.1 s unplugged interval could reach at most
(1554.1 − 900)/1554.1 ≈ 42.1 % asleep if the delay had started at the
unplug, against the 436.222 s, about 28.1 %, actually observed, that is
about 217.9 s of awake time beyond that hypothetical bound. That is
conditional arithmetic, not proof that the timer started at the unplug.

**Next decision.** Deploy revision 3 and run the second window: unplug,
let the phone suspend and wake by itself, replug. Then cross-check the
collector's suspend gaps against the frozen gaps of the kernel log, and
read the counter on both sides of the unplug. It needs the operator's
unplug and replug, and it produces the Mobian window figure and the
unplug discontinuity, not a calibrated current and not an explanation of
the standby difference.
## Entry 9 - 2026-10-22 - the esr-delta wake and the screen that came on: verified on the device, with a limited candidate

**The question.** The second resume of the 15:21-15:47 window was caused
by IRQ 445 `esr-delta`, and the display was programmed 0.16 s later. The
quiet-gauge policy knows "438 msoc-delta" and, with guards, "441
msoc-high", but not "445 esr-delta".

**What is really installed and enabled, read on the device.** `phosh`
`0.46.0-3+deb13u1+lmigaugewake3+homedrag7`, that is the v3 build; the v4
candidate was never built nor installed. `/usr/libexec/gsd-power` sha256
`244e3099…` and `/usr/libexec/phosh` sha256 `52412006…` contain the
strings `438 msoc-delta` and `441 msoc-high`, and **neither contains `445
esr-delta`**. Both opt-ins are live: `LMI_PHOSH_GAUGE_WAKE_FILTER=1` in
the phosh process, `LMI_GSD_QUIET_GAUGE_RESUME=1` in the gsd-power
process. `last_resume_reason` reads `445 esr-delta` on the device right
now.

**The path, from the installed sources.** Phosh calls
`phosh_screen_saver_manager_wakeup_screen()` on every resume that is not
a qualified gauge resume; GSD calls `backlight_enable()` in its fallback
branch. The qualification is the exact-match list of the wake reason, and
the reason list is the only condition that differs between the two
resumes of that window.

**The differential inside the window.** The screen was blank and USB was
disconnected across both resumes. The first, by IRQ 438 `msoc-delta` at
15:43:24, produced no display programming at all. The second, by IRQ 445
`esr-delta` at 15:44:37, produced a full mode set 0.163 s later. Only the
reason differed. The wake cost 186 s of screen-on time before the
reconnection, about 17 % of the 1117 s the window spent awake; the other
915 s is the idle delay after the screen blank and 16 s is the grace
timer. **The standby difference is not attributed to this wake.**

**The interrupt.** In `qpnp-fg-gen4.c` the `ESR_DELTA_IRQ` entry is named
`esr-delta`, its handler is `fg_delta_esr_irq_handler`, it is
`wakeable` and is armed with `enable_irq_wake`; the handler reads the
battery resistance and may vote awake and schedule calibration. It is a
fuel-gauge interrupt of the same family as the two the policy knows. No
interrupt is disabled, no gauge processing is suppressed, and keeping the
screen off stays a userspace policy decision.

**How often.** A census of the 15 kept quiet captures, 2026-10-11 to
2026-10-21: 995 `438 msoc-delta`, 23 `441 msoc-high`, 115
`502 typec-cc-state-change`, 10 misconfigured-IRQ, 5 RTC alarm, and **zero
`445 esr-delta`**. For the recognised reasons the quiet path worked every
time: 15.16 s to 15.58 s (median 15.38 s) before going back to sleep over
495 observed cycles. The esr-delta occurrence is the first one in the
kept evidence, so its rate is unknown and its energy cost is not
measured.

**The candidate, prepared but not built.** A limited diff, outside the
repository, `esr-delta-accept-20261022.patch` sha256 `6838a975…`, adds
"445 esr-delta" to the gate in both trees, with the same fresh,
noncritical, discharging guards as "441 msoc-high". It touches the
policy only.

**The off-phone test.** `check-esr-delta-policy-20261022.py` compiles the
actual gate from both trees, patched and unpatched: the unpatched
sources **fail** on `allow("445 esr-delta")`, the patched sources pass
every assertion. The unknown reasons and the combined reasons keep failing
open, that is they still turn the screen on: an unrecognised wake is
never silenced.

**Limitations.** Nothing was built, installed or deployed. The raw kernel
log of the first window has rotated out of the ring buffer, so a
simultaneous touch cannot be excluded from the preserved evidence; the
grounds are the differential inside the window and the source path. The
two userspace gates are not isolated by the log, and the patch changes
both. Accepting the reason means an esr-delta wake keeps the screen blank,
so the behaviour with real user activity has to be validated on the
device.

**Next decision.** Two independent tracks, both waiting on the operator:
the second standby window with the corrected collector, and the
esr-delta acceptance, which needs a build, an installation and a device
observation. The patch is not to be deployed before the second window,
because that window measures the system as it is now.
## Entry 10 - 2026-10-22 - collector revision 4: the discharge endpoint is qualified, the snapshot is one-shot

**The review.** The independent revision 3 review of 2026-10-22 confirmed
the revision 3 fixes and found two defects in them, plus one small source
defect, and said not to deploy until the endpoint handling is qualified.

**Defect 1, the endpoint.** Revision 3 computed the power state as "the
online flag does not read 1", so a missing node, a denied read or an error
read as an absent source, and a sample taken while the battery was
charging could be kept as a discharge endpoint. The review's
counterexample is exact: `usb_online` reading `ERR:13` with the gauge
reporting `Charging` produced a detached sample. The other power sources
were recorded but never checked.

Revision 4 qualifies the endpoint explicitly, and it needs three
independent things: the USB online flag **validated offline**, that is
reading exactly "0"; every other source that exposes an online flag
**known and not online**, on this device `dc` and `pc_port`; and the gauge
**Discharging**, because a Charging or Full reading means the counter can
move back up towards `charge_full`. Any unknown or failed reading
disqualifies the sample, the evidence is kept with its reason, and the
reasons are counted. The power state is tri-state now, and the boolean
stays the proxy it was.

**Defect 2, the snapshot.** With `--ufs-hardware-snapshot`, revision 3
read the two UFS attributes at the start **and again after every event**,
which reintroduced the runtime-resuming hardware queries the option
exists to isolate. It is now read at most once per run and reused. The
default mode never made those queries, so this is not proof that a
default run was perturbed.

**The small defect.** The collector read `max_bus_w`; the driver creates
`max_bus_bw` from a stored vote, so the old name always failed. Checked
on the device: `max_bus_bw` reads 0 and `max_bus_w` does not exist.

**The tests.** The suite holds **38 tests**, and the endpoint tests are
driven from **simulated raw readings**: the read helper and the list of
supplies are replaced, so the real classification runs on raw strings,
including the error strings. Against revision 4: **0 failures**. Against
revision 3: **12 failures**, and against revision 2: **12**. The snapshot
test fails on revision 3 with "the snapshot was read 2 times", which is
the defect itself. `test-ufs-policy-reader.py` still passes with 10
tests. No phone is contacted.

**Limitations.** Revision 4 has not run on a handset. The qualification is
deliberately conservative: a reading that cannot be qualified is kept as
evidence with its reason and is not offered as an endpoint, because a lost
endpoint is a missing measurement and a wrongly qualified one is a wrong
measurement. The USB offline signal is not independent proof of a physical
unplug. The window remains a gauge reading.

**Next decision.** Deploy revision 4 and run the second window, with a
fixed operator-visible maximum duration, keeping the pre-replug
disconnected samples as the endpoints. Nothing was built, installed or
deployed.
## Entry 11 - 2026-10-22 - the esr-delta wake on the reference platform: it recurs, and it costs a fraction of a second there

**The question.** How often does the `445 esr-delta` wake happen on this
hardware, and what does the reference platform do with it? Answered with
the evidence already kept, without a new run.

**The reference answer.** The LineageOS trace kept for the Android
reference contains Android's own wakeup accounting for the night of
2026-10-07: `445 esr-delta` 455 ms over 2 times, next to `438 msoc-delta`
2s 173ms over 7 times and 63 RTC alarms. The battery-stats timeline in
the same file gives the cost of each wake: **0.002 s, 0.326 s and 0.946 s
for the esr-delta wakes, and 0.302 s to 0.360 s for the msoc-delta
ones**. So the interrupt **recurs** on the reference platform, it costs
the same as a msoc-delta wake there, and **a gauge wake does not turn the
screen on**.

**The Mobian side.** The same interrupt, on the same driver, programmed
the display 0.163 s after the resume and left the screen lit for 186 s.
The difference is not in the hardware, it is in the userspace reason
gate of the quiet-gauge policy, which does not know this reason and
therefore takes the path that lights the screen. The cost on Mobian is
currently two orders of magnitude above the cost on the reference
platform.

**What stays open, and why.** `/sys/kernel/debug/wakeup_reasons` **does
not exist on this Mobian build**: the debugfs is mounted and the file is
simply not there, so the kernel wakeup accounting the reference platform
exposes is not available here. The ring buffer rotates, t=452 to 7586 at
17:12 and t=6332 to 13535 at 20:44, so the resume lines of the window are
gone. A census of the whole retained corpus finds exactly one
`Resume caused by IRQ 445, esr-delta` line, the one from the 2026-10-22
window; the fifteen Mobian quiet captures record the wake reason at the
observer's events and none of them carries this reason. The Mobian rate
stays unknown.

**The candidate is not extended.** `448 batt-temp-delta` also appears in
the reference accounting, once. It is not added: it has never been
observed on this platform, and the policy fails open by design, so an
unknown reason keeps turning the screen on until it is observed and
judged.

**A proposal for the next revision, not implemented.** The Mobian rate
could be measured during a window if the collector read
`/sys/kernel/wakeup_reasons/last_resume_reason` at each sample. It is a
passive sysfs read, with no runtime resume and no hardware query. It is
left out of revision 4 on purpose: the review of 2026-10-22 covered the
endpoint qualification and the snapshot, and changing the instrument
again before it is deployed would move the review target.

**Limits.** The two rates are not directly comparable: the reference
night woke every about 50 s to an RTC alarm, a much shallower sleep than
the Mobian quiet nights, and a shallower sleep means more load changes.
The reference episodes come from Android's accounting and its policy, so
Android treating a gauge wake as a wake is a platform behaviour and not
a property of the interrupt. The Mobian captures record the reason at
the observer's events, so an esr-delta wake that produced no event would
not be counted. The 186 s cost is one observation in one window.

**Next decision.** Unchanged: the second standby window with the
corrected collector, and separately the build, the installation and a
device observation of the esr-delta acceptance. The patch is not to be
deployed before the second window.
## Entry 12 - 2026-10-22 - the second matched window: 68.1 % asleep and a matched figure of 77 mA

**The window.** Collector revision 4 on the phone, unplugged from
19:17:31.7 to 20:07:08.7 UTC, 2976.98 s. The operator unplugged, left
the phone alone, and replugged without touching it.

**The collector and the kernel agree.** The collector saw 511.696 s and
763.389 s of sleep; the kernel's frozen gaps are 511.696 s and
763.390 s. The first two sleeps match to the millisecond: the corrected
clock pair is validated on a handset against the kernel's own wall-clock
distance. A third sleep of 753.456 s, from 19:54:35 to the
reconnection, is only in the kernel log, because the collector's one
hour bound expired at 19:54:22 while the phone was asleep. The bound
must be generous next time.

**The awake durations, measured.** 2028.542 s asleep, 948.44 s awake, so
**68.1 % asleep**. The awake time is fully accounted for: 901.2 s of idle
delay after the screen blanked, 15.3 s of screen-on after the unplug, and
two grace timers of 15.7 s and 15.9 s after the two `msoc-delta` resumes.
With its 900 s inactivity delay the interval could reach at most 69.8 %
asleep, and it reaches 68.1 %: the 47.3 s difference is the screen-on and
the two graces. Against the first window at 28.1 % asleep, and the
Android reference at 98.9 %, this window is close to the ceiling its own
idle delay allows.

**The screen stayed dark across both sleeps.** The display marks show
exactly two programmings, at the unplug and at the reconnection. The two
`msoc-delta` resumes did not light the screen: the quiet-gauge path
works as intended during this window.

**The counter variations, measured.** 187 qualified discharge endpoints
out of 477 samples; the 290 rejected ones are the plugged-in samples,
all with the reason `usb_online_present`, and **none rejected for an
unknown or a failed read**. At the unplug the counter stepped
2676998 -> 2533597, **-143401 uAh in five seconds**: the gauge
recomputing itself when the charger went away, the same logical
discontinuity the Android reference excluded at 86 mAh. The phone is at
100 % again now, which confirms it is a reporting artefact of the
charging side and not consumption. With the discontinuity excluded:
**-47334 uAh over 2206.2 s, that is 77.2 mA** over the detached period,
**56.7 mA** over the two sleeps and **106.3 mA** over the awake block.
The gauge's own `current_now` agrees, 148 mA then 88 mA.

**The matched Mobian figure, by the Android method: 77.2 mA against the
reference's 13.84 mA**, and 56.7 mA against roughly 14 mA for the sleep
period alone. The two gauges report the same full value, 2677 mAh
against 2676 mAh, so the rates are comparable as gauge readings. **On
this evidence the Mobian phone draws about four times more than the
reference while asleep**, so the difference is not only a duty-cycle
difference.

**The energy actually measured: none.** No current is computed by the
collector and none is derived beyond the counter quotients. The scale of
the gauge against the design capacity is still not established, and
neither gauge is an independent sensor. The gauge also reports 100 %
while the counter reads 93.6 % of `charge_full`, so the percentage is a
state estimate and not the counter ratio.

**Limits.** One window, one build, one state of charge, 37 minutes of
detached time against 8.5 hours for the reference. The collector's
result is missing the third sleep and the reconnection reading.

**What this changes.** The Mobian side now has a figure by the Android
method, and it is several times the reference, so the earlier framing
that the only difference was a duty-cycle difference does not hold. The
remaining candidates act while the processor is down: the always-on
rails and the peripheral states in suspend. The esr-delta acceptance
stays a separate decision and this window does not make it urgent: the
wake did not occur here, and the screen-on it caused in the first window
is a duty-cycle cost, not a sleep-current cost.

## Entry 13 - 2026-10-22 - what stays on while the processor is down, against LineageOS

**What was compared, offline.** The suspend path of each platform, from
the trace analysis already recorded in the regulator inventory, and the
always requested Mobian rails with their consumers, from the
point-in-time regulator summary. Two things are missing and are not
replaced by an assumption: there is **no point-in-time regulator summary
for LineageOS** in the kept packet, and **no rail current is measured
anywhere**, every current column of the Mobian summary reading 0 mA.

**The suspend path.** The one Mobian trial whose trace is complete
disables display_panel_vci, pm8150_l14, pm8150_l17, pm8150_l9,
pm8150_s3_level, pm8150_s3_mmcx_sup_level, pm8150a_s3_level,
pm8150a_s3_mmcx_sup_level, pm8150a_s4_level, refgen and ufs_phy_gdsc.
LineageOS disables gpu_cx_gdsc, pm8150_l17, pm8150_l9, pm8150_s3_level,
pm8150_s3_mmcx_sup_level, pm8150a_s3_level, pm8150a_s3_mmcx_sup_level,
pm8150a_s4_level and ufs_phy_gdsc. Only in Mobian: display_panel_vci,
pm8150_l14, refgen. Only in LineageOS: **gpu_cx_gdsc**, the GPU core
rail. On two of the three the software difference points the other way:
Mobian disables the panel rails and the reference clock generator, and
LineageOS does not. The inventory's caveat applies: a transition
observed around the suspend is a software transition, not proof of an
electrical state while the processor is down.

**The always-on rails, and why the obvious candidate falls.** The Mobian
rails whose only consumer is `deviceless`, that is requested from the
device tree or the bootloader and never released, are vdd_boost_vreg,
pm8150_s5 and s6 (WLAN), pm8150_l2 (USB-PD), pm8150_l5, pm8150_l5_ao and
pm8150_l12_ao (the CPU limits-dcvs rails), pm8150_l9, pm8150_l12,
pm8150_l14 and display_panel_vci (panel), pm8150_l17, pm8150a_l1 (touch),
pm8150a_s8, pm8150a_bob (cameras), pm8009_s2, pcie_0_gdsc,
usb30_prim_gdsc, hsphy@88e3000 (USB HS PHY) and regulator-dummy.
`vdd_boost_vreg` is the one followed since 12 October: use=1, open=1, one
`deviceless` consumer. A `deviceless` consumer means the request comes
from the device tree or the bootloader, and **the device tree is the same
on the two platforms**, so an always-on rail from the shared tree is
very likely always-on on LineageOS too and cannot by itself explain a
difference. That removes the most obvious candidate as an explanation.

**What survives.** The GPU core rail: LineageOS disables gpu_cx_gdsc in
its suspend path and Mobian does not. A software difference in the
suspend path, and a candidate only: nothing says what current that rail
costs, and the framework reports no currents.

**The one discriminating verification proposed.** Read the regulator
summary in the unplugged state on both platforms and compare the rail
sets. Read-only, changes nothing, disables nothing, and it is the only
step that separates a rail both platforms hold from a rail only Mobian
holds. Proposed, not scheduled: no new unplug is arranged and nothing is
disabled.

**Limits.** The Mobian summary is a point-in-time snapshot taken 110 s
after a boot with the cable connected, so it describes requested rails
and not current-carrying ones. The suspend-path lists come from two
different dates and two different builds, and the 12 October Mobian
observer artefacts record no kernel release string. No electrical
measurement exists, so nothing here designates a responsible party.

## Entry 14 - 2026-10-23 - the night window: 95 % asleep, 47 mA by the Android method

**The window.** Collector revision 4, eighteen hour bound on the boot
clock, no `--ufs-hardware-snapshot`, no RTC alarm, nothing changed on
the phone, which was not touched during the night. Unplugged
2026-10-22 20:31:25 to 2026-10-23 04:35:53 UTC. The collector saw **30
suspend events**, 27,675.691 s suspended, with **no log truncation**; the
kernel log still holds the tail of the night, nine
`Resume caused by IRQ 438, msoc-delta` resumes and the reconnection
waking by `IRQ 502, typec-cc-state-change`.

**Awake durations, measured.** 1388.2 s awake inside the 28,306 s
endpoint set, so **95.1 % asleep**, 93.9 % over the collector's own
window. The awake time is fully accounted for: 926 s before the first
sleep, that is the 900 s inactivity delay plus the screen-on after the
unplug; 29 gaps of 10 s to 15 s between the sleeps, the grace timers;
and about 145 s of awake time inside the sleep brackets, five seconds
each. By third of the night: 89.0 % asleep, then 98.3 %, then 98.7 %.
**The quiet-gauge path worked all night**: every wake was a
`438 msoc-delta`, the screen never came on, the device went back to
sleep after the grace timer each time.

**Counter variations, measured.** At the unplug the counter stepped
−143074 uAh in five seconds, the gauge recomputing itself, the same
logical discontinuity the Android reference excluded at 86 mAh and the
same value as the day window's −143401. With it excluded: −369243 uAh
over 28,306 s, that is **47.0 mA**, against the reference's 13.84 mA, a
ratio of **3.4**. The per-sleep slope, exact, is minimum 33.6 mA,
median 45.3 mA, maximum 102.1 mA; the bracket carries about five seconds
of awake time, some 147 uAh, about 1.3 % of a typical bracket.

**The slope is not constant through the night**: the median per third
falls 54.9, 42.5, 37.1 mA while the sleeps get longer, 793, 992,
1142 s of median. That is a reason not to present a single factor as an
established quantity.

**Energy really measured: none.** The gauge scale against the design
capacity is still not established, the same `charge_full` on both
platforms does not prove a comparable coulomb scale, and the reference's
own figures are one gauge's rounded software history.

**What this changes.** The day window was **not representative of the
duty cycle**, 68.1 % asleep there against 95.1 % here, and its 77.2 mA
was inflated by the 900 s idle delay and by the awake rate around it.
The difference from the reference persists but is smaller than the day
window suggested, about 3.4 times on the net rate and about three times
on the sleep-only rate. **It is still not an established electrical
measurement.** The candidate remains whatever holds the processor down,
and the discriminating verification remains the regulator summary read
in the unplugged state on both platforms.

**Limits.** One night, one build, one device. The endpoint sequence is
bounded to the last 256 detached readings, so the whole-night
reconstruction comes from the events and the counters. The attachment
flag lagged at the reconnection, so the detached period is bounded
between 28,306 s and 29,068 s.
