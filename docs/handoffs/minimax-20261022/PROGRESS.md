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

## Entry 2 — 2026-10-22 — pending: ranked unresolved client differences

**Hypothesis.** Up to three concrete client or configuration differences
remain that could discriminate the standby residual, taken from the existing
peripheral checklist rather than from a new broad audit.

**Artifact identity.** `docs/validation/lmi-standby-peripheral-checklist-2026-10-20.md`
and the driver-coverage and inventory notes of the same date.

**Evidence.** Pending the ranking pass.

**Changes.** Pending.

**Validation.** Pending.

**Limitations.** A missing `pm_genpd` node, a successful PM callback, a zero
logical vote or an absent trace event are not electrical exclusions.

**Next decision.** Pending.
