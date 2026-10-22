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
