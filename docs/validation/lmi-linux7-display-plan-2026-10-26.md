# Linux 7 display bring-up: diagnosis and prepared escalation plan

Date: 2026-10-26
Target: Xiaomi POCO F2 Pro / Redmi K30 Pro (`lmi`), SM8250, AMOLED 1080x2400
Scope of this milestone: **diagnosis, prepared sources and a prepared build
recipe only**. No kernel Image was built, no image was packaged, no handset
was flashed, no partition was written, and the handset was only read.

> **Review of October 27, 2026.** This plan was never executed: the display1
> artifacts were prepared and host-checked, but no Image was built from them and
> they never ran on the handset. The host checks below were reproduced
> independently against the pinned tree
> cc9de5d4b5ab6459f5774946aa3195ad51236fa8 and still pass, so the sources are
> auditable and usable as a reference. What is host-checked covers the patches,
> the merged configuration, the board DTB, the panel driver object and the
> bundle self-test; the complete operator chain, from the kernel Image through
> the bundle and the pinned menu recipe to a firmware build and a handset trial,
> was never executed, so the reproducible publication of that path remains to be
> done. The escalation plan in section 6 is
> superseded in direction: the community kernels
> `7.1.0-lmi-ccc-ram1` and `7.2.12-lmi-community-port1` reached real DSI/DRM
> and USB journal output on the handset without this display1 path. See
> [the 7.1 record](lmi-linux7-community-display-2026-10-27.md) and
> [the 7.2.12 record](lmi-linux7-community-port-display-2026-10-27.md).

---

## 1. First-hand state of the handset

The handset was reached over the USB RNDIS link on 2026-10-26 and read.

- The address `172.16.42.2` is **this workstation's** side of that link: the
  `Ethernet 3` NDIS adapter of the host holds `172.16.42.2/24`. The handset
  owns `172.16.42.1`, which the handset itself reports in its journal
  (`NET: 172.16.42.1/24 assigned to usb0`, and a `link/ether` line whose
  address is redacted here as a device identifier).
- Open ports on the handset: **9000** (journal listener) and **9001** (bounded
  touch capture). Port 22 is closed, which is exactly what the observer
  `/init` contract states ("no remote shell").
- The journal retrieved on TCP 9000 reports:
  - kernel: `Linux linux7-lmi 7.2.12-dirty #3 SMP PREEMPT Mon Oct 26 20:02:07 CET 2026 aarch64`
  - provenance markers: `lmi_menu=outer-v2-linux7`, `lmi_kernel=7.2.12`,
    `kernel_sha=e3d459f7…`, `dtb_sha=e9b56cfc…`, `initrd_sha=feaac77a…`
  - `observer ready; staying alive (no reboot, no userdata mount, no firmware)`
  - device tree model: `Xiaomi POCO F2 Pro (minimal mainline experiment)`
  - **no** `msm_drm`, DSI, panel, fbcon or GPU line anywhere in the journal.

**Conclusion 1.** The handset is not running Mobian. It is running the
temporary Linux 7.2 observer, from RAM, through the `outer-v2-linux7` menu
candidate. The running kernel was compiled at 20:02 on 2026-10-26, which
matches the last image the operator flashed (`lmi-menu-linux7-touch1-20261026.img`,
20:10). The installed 4.19 Mobian is untouched and remains selectable from the
menu; nothing was written to userdata.

**Conclusion 2.** The white screen is the expected consequence of the observer
configuration. It is not a panel, rail, cable, bootloader or DSI fault.

## 2. Why the screen is white: the configuration fact

- `kernel/experimental/linux7/configs/observer-tested.config` contains **no
  `CONFIG_DRM` line at all** (the only `CONFIG_DRM*` entry is
  `CONFIG_DRM_PANEL_ORIENTATION_QUIRKS`). There is therefore no DRM core, no
  KMS, no MSM display controller, no DSI host, no panel driver and no GPU
  driver in the running kernel.
- The observer device tree disables the display subsystem explicitly
  (`&mdss { status = "disabled"; }`), so upstream `sm8250.dtsi` never brings
  `mdss_mdp`, `mdss_dsi0` or `mdss_dsi0_phy` up.
- The initramfs carries no firmware and no modules, so even a built-in GPU
  would have nothing to load.
- With no display driver, the panel keeps whatever state the bootloader left
  it in, which is the observed white screen.

The same fact explains why there is no SSH: the observer `/init` is a busybox
script that only publishes a journal over USB.

## 3. What a graphical Mobian boot actually needs

| Layer | State in the accepted observer | Needed for a graphical Mobian |
|---|---|---|
| Storage | no `CONFIG_UFS` in the config | UFS + ext4 to mount the Mobian root |
| Kernel modules | 925 modular symbols, none loadable from the initramfs | the display stack built **in** (`=y`) |
| GPU firmware | none in the initramfs | `qcom/a650_sqe.fw` and `qcom/a650_gmu.bin` |
| Display driver | absent (`CONFIG_DRM` unset) | DRM + MSM + DSI + 7 nm PHY + panel driver |
| Panel rails | absent | vddio 1.88 V (PM8150 LDO14), vci 3.0 V (PM8150L LDO10), DSI vdda 1.2 V (PM8150 LDO9) |
| Panel timing | absent | 1080x2400 @ 60, vendor DCS sequence, reset on tlmm 46 |
| Userspace | observer `/init` | real init, systemd, Phosh/Weston on KMS, GPU userspace |

Two upstream facts shape the next step and are worth keeping in the record:

- Upstream v7.2 binds the Adreno 650 as `qcom,adreno-650.2` with a separate
  GMU node; `a6xx_catalog.c` requests `a650_sqe.fw` and `a650_gmu.bin` under
  the `qcom/` firmware prefix. The matching files already exist in the project
  at `userspace/gpu/files/firmware/a650/`. Upstream has no `.mdt`/`.b00`
  split assembly, so the zap split files are not usable there and are not
  needed for the GMU path.
- The 7 nm PHY driver requests `vdds` without a voltage constraint, which is
  why the PM8150 LDO5 declaration that this tree already carries for the USB2
  PHY (880 mV) can be reused for the DSI PHY. The community lmi board names
  the same rail `vreg_l5a_0p875` (875 mV); the difference is documented, not
  silently reconciled.

## 4. Artifacts prepared by this milestone

| Path | Role |
|---|---|
| `kernel/experimental/linux7/configs/display1.fragment` | Kconfig fragment adding the display stack, all built-in |
| `kernel/experimental/linux7/drivers/gpu/drm/panel/panel-samsung-ams667uu01.c` | lmi AMOLED panel driver on the 7.2 DRM API, with rails and the vendor DCS sequence |
| `kernel/experimental/linux7/patches/0002-lmi-dsi-display.patch` | observer DTS plus the DSI wiring and the three panel rails |
| `kernel/experimental/linux7/patches/0003-add-msm667uu01-panel.patch` | panel driver file plus its Kconfig and Makefile entries |
| `kernel/experimental/linux7/tools/regen-display-patches.py` | regenerates patches 0002 and 0003 from the pristine tree and the repository copies |
| `kernel/experimental/linux7/tools/check-display1-host.sh` | static validation: patches, configuration, DTB, driver object |
| `kernel/experimental/linux7/tools/find-modular-selectors.py` | host tool that lists the modular symbols capping the display chain |
| `kernel/experimental/linux7/tools/build-linux7-bundle.py` | rebuilds the LMIBNDL1 RAM bundle with the four linux7 components of a kit, keeping every other component byte-identical |
| `kernel/experimental/linux7/tools/prepare-menu-recipe.py` | prepares a pinned menu recipe for a new bundle (paths, bundle hash, manifest) |
| `kernel/experimental/linux7/build/build-linux7-kit.sh` | operator recipe that builds the kit (Image, DTB, initramfs, command line) and its manifest |

The panel driver is a port of the community lmi driver
(`yuweiyuan8/linux-xiaomi-thyme-mainline`, v7.2-rc5) with three deliberate
differences, each traceable to a source:

1. **Rails are driven by the driver** (`vddio` 1.88 V then `vci` 3.0 V, with
   the vendor 6 ms and 10 ms delays), instead of being left to the bootloader
   state.
2. **The vendor DCS sequence is used verbatim**, including `35 00` and
   `55 00`, which the generated community sequence drops. `35 00` also turns
   the panel TE signal off, which is the safe choice here: upstream v7.2 has
   no TE source configured for the lmi DSI link, so tear-on would stall the
   panel on a TE signal that never arrives.
3. **Vendor geometry and backlight range** (1080x2400 @ 60, hfp 64 / hpw 20 /
   hbp 64, vfp 34 / vpw 20 / vbp 34, DCS 0x51 with 0..2047 and the vendor
   initial level 536).

The device tree patch reuses the upstream `sm8250.dtsi` display nodes
(`mdss`, `mdss_mdp`, `mdss_dsi0`, `mdss_dsi0_phy`, `mdss_dsi0_out`) and adds
the three rails the observer tree did not carry, the panel node with its
vendor supplies and the `tlmm 46` reset line, and the four-lane DSI output.

## 5. Static validation results

Host checks only. They do not prove anything about the panel, the rails or the
handset.

| Check | Result |
|---|---|
| Patch 0001/0002/0003 apply to a copy of the pinned tree `cc9de5d4…` | pass |
| Merged configuration resolves every display symbol as `=y` | pass, after one correction |
| Board DTS compiles with `dtc` | pass, 115766 bytes |
| Compiled DTB carries `xiaomi,lmi-ams667uu01`, `vddio-supply`, `vci-supply`, `reset-gpios`, `data-lanes`, `qcom,dsi-phy-7nm`, `qcom,pm8150l-rpmh-regulators` | pass |
| Panel driver compiles against the 7.2 headers | pass, 11640-byte object |

### The configuration defect the check caught

The first fragment was rejected by the static check, and it had caught a
defect that would have reproduced the current white screen with no visible
cause.

`CONFIG_DRM_MSM` cannot be forced to `y` while modules are enabled.
`CONFIG_DRM_MSM` selects `DRM_EXEC`, `DRM_GPUVM`, `DRM_SCHED`,
`QCOM_UBWC_CONFIG` and `QCOM_MDT_LOADER`. Those five are invisible tristate
symbols, so their value is not user-settable: with `CONFIG_MODULES=y` they
take the value `m`, and Kconfig caps a `y` symbol that selects a `m` symbol
at `m` as well. The whole display stack therefore silently fell back to
modules and would never have loaded, because the observer initramfs carries
no module payload.

Five independent experiments on the pinned tree measured this: with
`CONFIG_MODULES=y` every symbol of the chain ends up `m`, whatever the
fragment asks for; with `CONFIG_MODULES=n` they all end up `y`. Disabling
modules removes exactly one symbol from this configuration,
`CONFIG_CRYPTO_BENCHMARK`, a crypto self-test module that is irrelevant to
this handset. The other 924 modular symbols belong to other platforms and
could never load from an initramfs without a module payload anyway.

The fragment now pins `CONFIG_MODULES=n` and the validation asserts that the
whole chain resolves to `=y`.

### Packaging chain, validated without a build

The chain that turns a kit into a flashable menu image has three links, and
all three were validated on host artefacts of the accepted candidates, without
running the firmware build:

| Check | Result |
|---|---|
| The bundle container contract was decoded from the accepted touch2 bundle | 9 rows, `LMIBNDL1`, 4096-aligned offsets, crc32 over the stored bytes |
| `build-linux7-bundle.py --self-test` re-packs the accepted touch2 bundle | all nine components decoded-identical, every crc32 valid |
| `prepare-menu-recipe.py --verify-only` regenerates the manifest rule of the committed `recipe-touch2` | reproduces it exactly, 73 files |
| Dry run of the full chain on the accepted observer kit | bundle written, read back, 9 components with valid crc32, recipe prepared and re-verified |

The storage encoding of each component was measured, not assumed: `mobian/kernel`,
`mobian/initrd`, `linux7/kernel` and `linux7/initrd` are gzip streams, the
other five components are stored raw. The bundle command line is the kit
command line plus the ` initcall_debug` token, which is what produced the
84-byte entry of the accepted candidate.

One property of the chain matters for the operator: the menu recipe is
*pinned*. `build.sh` verifies the sha256 of every recipe file against
`RECIPE_RESULT.json`, and `external-mobian/make-outer.py` verifies the sha256
of the bundle it embeds. A new candidate therefore needs a new recipe
directory, which `prepare-menu-recipe.py` produces from the reference recipe
with exactly three pinned values changed.

## 6. Escalation plan

Each rung changes one thing, is flashed temporarily, and is judged on the
handset. The installed 4.19 Mobian stays recoverable in every rung.

**Rung 1 — display1 (this milestone's prepared artifact).**
Kernel: DRM + MSM + DSI + 7 nm PHY + panel driver, all built-in; DTS with the
DSI wiring and the three rails; initramfs with the observer `/init` plus the
two GPU firmware files.
Expected on the handset: the panel lights up; the journal shows the `msm_drm`
probe, the DSI host attach, the panel attach and the regulator rails
(`vreg_l14a_1p88`, `vreg_l10c_3p0`).
Invalidated by: no `msm_drm` line at all (the display path did not build or
did not probe), or a regulator error on `vddio`/`vci`.

**Rung 2 — console over KMS.**
Add `CONFIG_FRAMEBUFFER_CONSOLE` on the DSI mode so that the kernel console
is visible on the panel, without any userspace compositor. This separates
"the panel is driven correctly" from "the compositor can use it".
Expected: kernel log text on the panel. Invalidated by: a lit but featureless
panel with no console output.

**Rung 3 — real userspace.**
Replace the observer `/init` with an initramfs that mounts the Mobian userdata
root and starts systemd, then Phosh. This needs storage support
(`CONFIG_UFS`, `CONFIG_UFS_QCOM`) and the 7.2 module set for that root, which
is a separate piece of work.
This rung is where the project rule applies: the existing Mobian rootfs must
not be booted with 7.x before storage, modules, firmware, display and input
are qualified.

**Rung 4 — graphical session.**
Phosh/Weston on KMS with the GPU userspace (`userspace/gpu/files/gpu72`),
the input stack, and the remaining radios.

**Rung 5 — autonomy.**
Battery, suspend and the rest of the handset, only once the graphical session
is stable.

## 7. Guardrails observed by this milestone

- The 4.19 Mobian installation was not touched: no flash, no partition write,
  no userdata mount, no reboot.
- The handset was read only, over the USB journal service the observer
  itself publishes. No ADB and no Fastboot operation was performed.
- The pinned kernel tree `linux-v7.2.12-clean` was not modified; the patches
  are applied to a copy, and the tree revision `cc9de5d4…` was verified before
  the work.
- No kernel Image was built and no boot image was produced: the heavy build
  and the flash remain operator steps, by project policy.

## 8. Operator procedure

Three build steps, then the usual temporary flash and journal retrieval. Steps
2 and 3 are the project's own packaging steps and are driven by the tools
prepared here; only step 1 compiles the kernel.

**Step 1 — build the kit (heavy, operator-run).**

```bash
bash kernel/experimental/linux7/build/build-linux7-kit.sh --variant display1
```

It writes `output/minimax-kernel7-feasibility/linux7-display1/kit/` with the
Image, the DTB, the initramfs and the command line, plus a manifest with the
sha256 of each component and the loader size limits.

**Step 2 — rebuild the RAM bundle with the new linux7 components.**

```bash
python3 kernel/experimental/linux7/tools/build-linux7-bundle.py \
    --base output/minimax-kernel7-feasibility/codex-linux7-bundle-touch2 \
    --kit  output/minimax-kernel7-feasibility/linux7-display1/kit \
    --output output/minimax-kernel7-feasibility/codex-linux7-bundle-display1
```

Every component other than the four linux7 ones stays byte-identical. The
tool prints the bundle sha256, which the next step pins.

**Step 3 — prepare the pinned menu recipe and build the firmware.**

```bash
python3 kernel/experimental/linux7/tools/prepare-menu-recipe.py \
    --reference output/minimax-kernel7-feasibility/codex-linux7-menu/recipe-touch2 \
    --name      display1 \
    --bundle    output/minimax-kernel7-feasibility/codex-linux7-bundle-display1 \
    --output    output/minimax-kernel7-feasibility/codex-linux7-menu/recipe-display1

sudo bash output/minimax-kernel7-feasibility/codex-linux7-menu/recipe-display1/build.sh --build
```

The firmware build prints `DUAL_DIRECT_RAM_HANDOFF_BUILD_COMPLETE_NOT_FOR_FLASHING`
and writes `firmware-output-display1/boot-lmi.img`. The permanent four-entry
menu is not touched by any of this.

**Step 4 — flash temporarily and collect.**

Flash from Windows with the operator's own Fastboot launcher, using the
`boot-lmi.img` of step 3 and the new hash. Then read the result over USB: the
observer publishes the journal on `172.16.42.1:9000` (one-shot per
connection) and the bounded touch capture on `172.16.42.1:9001`. The journal
contains the `msm_drm` probe result, the panel attach and the rail messages.

**Step 5 — judge.**

Compare the screen and the journal against the expectations of section 6,
then decide the next rung.

## 9. Files

- `kernel/experimental/linux7/configs/display1.fragment`
- `kernel/experimental/linux7/drivers/gpu/drm/panel/panel-samsung-ams667uu01.c`
- `kernel/experimental/linux7/patches/0002-lmi-dsi-display.patch`
- `kernel/experimental/linux7/patches/0003-add-msm667uu01-panel.patch`
- `kernel/experimental/linux7/tools/regen-display-patches.py`
- `kernel/experimental/linux7/tools/check-display1-host.sh`
- `kernel/experimental/linux7/tools/find-modular-selectors.py`
- `kernel/experimental/linux7/tools/build-linux7-bundle.py`
- `kernel/experimental/linux7/tools/prepare-menu-recipe.py`
- `kernel/experimental/linux7/build/build-linux7-kit.sh`
