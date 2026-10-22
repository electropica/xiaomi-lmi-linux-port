# UFS suspend-policy comparison — LineageOS reference vs Mobian, 2026-10-22

Scope: close the **measurement gap** on the UFS host policy, not the UFS
leakage hypothesis. Nothing here attributes physical current to a component.

Evidence classes used below: **S** source/declared wiring, **A** awake
snapshot, **T** retained suspend-transition evidence, **C** consumption
comparison. A policy value is configuration, never an electrical measurement.

## 1. Why the earlier capture needed re-reading

The retained Android capture
(`work/minimax-rpmh-audit-20261022/ufs-lineage-live.txt`, 2026-10-22
13:56:11 UTC) reached the device and listed the UFS host directory, but read
no policy value: every attribute read was refused. Its generated summary also
labelled several listed names as `ABSENT`.

Both problems are now understood and reproducible:

* The unprivileged `adb shell` runs as `uid=2000(shell)` in SELinux context
  `u:r:shell:s0` and is **denied `getattr()`** on the UFS attribute files.
  `ls -la` therefore prints them as `-?????????  ? ?  ? ?  ?  ?  ?`, and
  `stat` returns `Permission denied`.
* `test -e` returns **FALSE for an entry that the directory listing shows**,
  because it follows symlinks and the `stat` behind them is refused. The
  first reader used `[ -e ]` as its existence oracle, so a refusal was
  reported as an absence.

**Only a successful directory listing is a valid existence oracle.** The
reader shipped in `userspace/power/diagnostics/ufs-policy-read.py` now
classifies as follows, and `test-ufs-policy-reader.py` covers each case:

| Situation | Verdict |
|---|---|
| read succeeded | `OK` |
| explicit permission failure | `DENIED` (errno + message) |
| read failed, listing succeeded, name **not** enumerated | `ABSENT` (local to that directory) |
| read failed, listing succeeded, name **is** enumerated | `LISTED_BUT_UNREADABLE` |
| read failed, listing failed, or no listing for the parent | `UNKNOWN` |

The reader also records UID, GID and SELinux context with every read, and the
identity guard now requires **exact membership** of an explicit device set
(`lmi`, `lmipro`) **and** an explicit build set, plus the known ROM family
prefix; a substring match on any property is rejected and an unknown build
fails closed.

## 2. Source mapping in the two exact kernels

Mobian base `a5b3099017ae581aae8bf597b2f9c8c765026af1`, Android reference
`71b13e62f057a649b77fe4062feb73ee72ad609c`.

**S — one UFS driver file is byte-identical:**

```
5914361ac55598d1e2ffb6105bbe161d93536aba7144310cc67cb94d400ac739  drivers/sci/ufs/ufs-qcom.c  @ a5b3099017ae
5914361ac55598d1e2ffb6105bbe161d93536aba7144310cc67cb94d400ac739  drivers/sci/ufs/ufs-qcom.c  @ 71b13e62f057
```

Any UFS difference *inside this file* must therefore come from **values**,
not from code. **This is one file, not the driver.** The sysfs show/store
implementations of these attributes live in the Qualcomm-patched `ufs_core.c`,
which was **not** compared and was not reachable (see the limit below); the
device tree overlays were not compared either; and the consumers of the same
rails outside this file are not covered by it. An identical file here does not
exclude a difference elsewhere in the UFS stack.

**S — where the suspend-relevant decision is taken**, in
`drivers/scsi/ufs/ufs-qcom.c` (identical on both sides), `ufs_qcom_suspend()`
at line 833 and the reference-clock branch at lines 893-901:

```c
if (host->vddp_ref_clk && (hba->rpm_lvl > UFS_PM_LVL_3 ||
                           hba->spm_lvl > UFS_PM_LVL_3))
        ufs_qcom_enable_vreg(hba->dev, host->vddp_ref_clk);
else if (host->vddp_ref_clk && ufs_qcom_is_link_hibern8(hba))
        ufshcd_qcom_set_vreg_load(host->vddp_ref_clk,
                host->vddp_ref_clk->max_uA);
```

`rpm_lvl` and `spm_lvl` are the UFS power-management levels for the runtime-PM
and system-PM paths. Above `UFS_PM_LVL_3` the **VDD parent reference-clock
regulator is fully enabled** for the suspend; otherwise, if the link is in
hibern8, the same regulator is kept on at its **maximum current limit**.
This is the identified mechanism by which UFS could hold a rail up across a
suspend window.

**S — the LineageOS init policy** (`init.qcom.power.rc` @ `da4ba935`,
sha256 `86780f04dd6da0161165997240610bd10951dec41beee142034fc4626ff37669`):

| Trigger | Line | Write |
|---|---|---|
| `on enable-low-power` | 28-31 | `clkscale_enable 1`, `clkgate_enable 1` |
| `on property:sys.boot_completed=1` | 32-33 | `trigger enable-low-power` |
| `on property:init.svc.recovery=running` | 76-77 | `trigger enable-low-power` |
| `on init` | 126-130 | `clkscale_enable 0`, `clkgate_enable 0`, `sleep_disabled 1` |
| `on charger` | 165-168 | `clkscale_enable 1`, `clkgate_enable 1` |

The write path is `/sys/devices/platform/soc/${ro.boot.bootdevice}/…`, i.e. the
same UFS host directory the reader inspects.

**S — the Mobian side.** Mobian has **no init write to any UFS attribute**;
the `lmi-cpu-idle` service covers `sleep_disabled` only. Every UFS policy
value on Mobian is therefore the **driver default**.

**A — `sleep_disabled`.** Android writes it to 1 in `on init` and the reset
comes from the device post-boot script (Kona branch, quoted in
`kernel/diagnostics/power/README.md:434`); Mobian sets it to `N` at
`multi-user.target` through `lmi-cpu-idle.service`. Both converge to `N` at
steady state, so this is not a differentiator, consistent with the earlier
CPU-idle result.

## 3. The narrow result

1. **The `clkscale_enable` gap is closed on the Android side.** The attribute
   does **not** exist at the inspected UFS host root: the successful listing
   does not enumerate it, and neither does `clk_scaling_enable`. The LineageOS
   init writes to `clkscale_enable` therefore fail, and the "Enable UFS
   powersaving" comment reduces in practice to enabling **clock gating**.
   *Scope:* this is a local absence on the inspected Android directories. It
   does **not** establish absence under Mobian, and it is not universal across
   the kernel.
2. The UFS platform driver is identical on both platforms, so the remaining
   candidate is a **value** difference, not a code difference.
3. The only OS-level UFS policy difference identified so far is that **Android
   explicitly writes `clkgate_enable`** (1 at `sys.boot_completed` and on
   charger, 0 during `on init`) while **Mobian never writes it** and keeps the
   driver default. The retained 2026-10-12 Mobian snapshot (plugged, root,
   uncertified older build) recorded `clkgate_enable=1`.
4. `rpm_lvl`, `spm_lvl` and `auto_hibern8` are **never written by userspace on
   either side**, so they should be the driver defaults on both. The retained
   Mobian values (3 / 3 / 1000) are consistent with that.

**Policy equality would neither prove physical state equality nor exclude UFS
leakage.** A single differing number would not prove a leak either.

## 4. Documented limit on the source mapping

The sysfs **show/store** implementations of `clkgate_enable`,
`clkgate_delay_ms`, `rpm_lvl`, `spm_lvl`, `auto_hibern8`,
`rpm_target_link_state`, `rpm_target_dev_state`, `spm_target_link_state` and
`spm_target_dev_state` live in the Qualcomm-patched `ufs_core.c`. That file is
**not present** in `LineageOS/android_kernel_xiaomi_sm8250` and was not
reachable from the public mirrors tried (`kernel/common` AOSP mirrors,
`android_kernel_qcom_sm8250`, `android_kernel_qcom_techpack`,
`android_kernel_oneplus_sm8250`, torvalds v4.19). The search was stopped
rather than retried indefinitely. **Consequence:** the exact units, defaults
and setter semantics of those attributes are not established from source; only
their use in the suspend path is. The device is the authority for the values.

## 5. Next measurement

One privileged, read-only UFS snapshot per platform over the identical fixed
paths, recording UID/GID/SELinux context and the OS/kernel/build identity:

* **LineageOS** — the authorised ADB device is unprivileged, and SELinux
  refuses the attribute reads. The privileged route requires `adb root`
  (restarts `adbd` as root; reversible with `adb unroot`; no partition, flash
  or persistent setting change). **Operator action, not performed here.**
* **Mobian** — the same reader over the existing SSH route, **with USB
  connected**, explicitly awake and plugged. No new key, account or access
  setup, and no unplugged-SSH request.

Both snapshots use `ufs-policy-read.py --execute`, one shot, no write, saved as
timestamped raw captures outside Git.

If the privileged access is not granted, the comparison stays **UNKNOWN** — not
a match and not a difference — and no further test is proposed.


## 6. Privileged LineageOS read, 2026-10-22 (root, USB connected, awake)

The operator authorised `adb root` for one diagnostic read and its reversal.
Sequence, performed in one script: `adb devices` -> `adb root` -> wait ->
one read -> `adb unroot` -> verify. At the moment of the read the shell was
`uid=0(root)`, SELinux context `u:r:su:s0`; after `adb unroot` the shell was
back to `uid=2000(shell)`, context `u:r:shell:s0`. The device was plugged
(`usb_online=1`), awake, and the kernel was
`4.19.325-cip131-st15-perf-g71b13e62f057`.

Every directory listing succeeded (`failed_listings: none`), so the verdicts
below rest on successful enumerations.

| Attribute | LineageOS 23.2 (privileged read) | Mobian 2026-10-12 retained snapshot |
|---|---|---|
| `clkgate_enable` | **1** | **1** |
| `clkgate_delay_ms` | **50** | **50** |
| `rpm_lvl` | **3** | **3** |
| `spm_lvl` | **3** | **3** |
| `auto_hibern8` | **1000** | **1000** |
| `clkscale_enable` | not enumerated (listing succeeded) | not observed |
| `clk_scaling_enable` | not enumerated (listing succeeded) | not observed |
| `rpm_target_link_state` | `HIBERN8` | not observed |
| `rpm_target_dev_state` | `SLEEP` | not observed |
| `spm_target_link_state` | `HIBERN8` | not observed |
| `spm_target_dev_state` | `SLEEP` | not observed |
| `attributes/psa_state` | `0x00000000` | not observed |
| `attributes/current_power_mode` | `0x00000011` | not observed |
| `attributes/bkops_status` | `0x00000000` | not observed |
| `attributes/active_icc_level` | `0x0000000F` | not observed |
| `qcom/power_mode` | `[Rx,Tx]: Gear[4,4], Lane[2,2], PWR[FAST MODE,FAST MODE], Rate-A` | not observed |
| `qcom/clk_status` | `0` | not observed |
| `qcom/bus_speed_mode` | `0` | not observed |
| `qcom/err_count` | all counters 0 | not observed |
| `qcom/err_state` | `0` | not observed |
| `max_bus_bw` | `0` | not observed |
| `power/control` | `auto` | not observed |
| `power/runtime_status` | `suspended` (platform) / `active` (host0) | not observed |

**Narrow result.** The five UFS policy attributes that exist on both sides are
**identical**: `clkgate_enable=1`, `clkgate_delay_ms=50`, `rpm_lvl=3`,
`spm_lvl=3`, `auto_hibern8=1000`. Neither clock-scaling spelling exists on
LineageOS. The Android init writes `clkgate_enable=1` explicitly, and Mobian
reaches the same value through the driver default, so the two platforms
converge on the value that the suspend path consumes.

**What this settles, and what it does not.** It settles the UFS *policy
value* question for the five shared attributes, on the reference kernel, at one
plugged awake moment. It does **not** establish the UFS state during a suspend
(a plugged awake read is not a sleep observation), it does not identify who
holds the rails, it does not cover the attributes the older Mobian snapshot
never captured, and it does not exclude a difference in the parts of the UFS
stack that were not compared (`ufs_core.c`, the device tree overlays, the
other consumers of the same rails).

**Remaining Mobian datum.** The same reader over the same extended paths, on
Mobian, with USB connected, so that `rpm/spm_target_link_state`,
`rpm/spm_target_dev_state`, `psa_state`, `current_power_mode`,
`qcom/power_mode`, `max_bus_bw` and the runtime bookkeeping can be compared.
The Mobian side of that comparison is still missing, and the reader now
carries the enumerated names so the result is auditable from one capture.
