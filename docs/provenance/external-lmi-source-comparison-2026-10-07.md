# External lmi source comparison — 2026-10-07

These operator-supplied repositories are comparison references, not selected
replacement builds. Inspection covered GitHub metadata, pinned text recipes,
device-tree declarations and firmware Git-object identifiers. No external
script, build, image or firmware was executed or installed. No immediate
validated battery fix was identified by this limited comparison.

| Repository | Inspected revision | Role / relevant boundary |
| --- | --- | --- |
| [N1kroks/alioth-nightly-builds](https://github.com/N1kroks/alioth-nightly-builds/tree/1c9ee21ca01ac5db28925ecba7dd8e02d4df09bf) | `1c9ee21ca01ac5db28925ecba7dd8e02d4df09bf` | Archived alioth postmarketOS/Phosh CI reference; not an lmi validation. |
| [yuweiyuan8/lmi-nightly-builds](https://github.com/yuweiyuan8/lmi-nightly-builds/tree/83e043b82b1e12c1a529b34e9567da6ba237c2ba) | `83e043b82b1e12c1a529b34e9567da6ba237c2ba` | Confirmed fork adapted to xiaomi-lmi; builds external kernel/pmaports branches. |
| [N1kroks/firmware-xiaomi-alioth](https://github.com/N1kroks/firmware-xiaomi-alioth/tree/95dfcdf6b154c00af3e093db82015cda90f4299a) | `95dfcdf6b154c00af3e093db82015cda90f4299a` | Alioth firmware/calibration reference. |
| [yuweiyuan8/firmware-xiaomi-lmi](https://github.com/yuweiyuan8/firmware-xiaomi-lmi/tree/dde156380b2ac372619ed332dbe60640b838b7fe) | `dde156380b2ac372619ed332dbe60640b838b7fe` | Confirmed fork with lmi paths and changed calibration/sensor data; origin and suitability of individual blobs are not independently established. |
| [UtsavBalar1231/kernel_xiaomi_sm8250](https://github.com/UtsavBalar1231/kernel_xiaomi_sm8250/tree/99352d52fed224160798675f138d6af0051a5e5c) | `99352d52fed224160798675f138d6af0051a5e5c`, android14-stable | Archived Android/CLO downstream tree; Makefile identifies 4.19.315. A source-comparison lead, not a compatible Mobian boot proven here. |
| [PixelExperience-Devices/kernel_xiaomi_lmi](https://github.com/PixelExperience-Devices/kernel_xiaomi_lmi/tree/d26c193dcd97812a9a565ac40fe5092cc9a18fbf) | `d26c193dcd97812a9a565ac40fe5092cc9a18fbf`, thirteen | Archived lmi Android tree; Makefile identifies 4.19.288. No battery fix validated by this inspection. |
| [Zhuchen00123/lml_test](https://github.com/Zhuchen00123/lml_test/tree/fecd4689685fc827a20eed0e96caedaae4a2e624) | `fecd4689685fc827a20eed0e96caedaae4a2e624` | Experimental Debian 13/mainline lmi integration notes and scripts, plus binary artifacts. Author-reported results are not our hardware validation. |

## Mainline recipe identity and limits

The lmi workflow selects yuweiyuan8/linux branch v6.19 and pmaports branch
nikroks/alioth. At inspection their heads were
[linux 999ef8b](https://github.com/yuweiyuan8/linux/tree/999ef8bfd90ca4c214f18ac5d0138bf380386c38)
and [pmaports b6453d5](https://github.com/yuweiyuan8/pmaports/tree/b6453d5aaead33bb297d7c64d8575987ebcf29f7).
The workflow environment names 6.19.2, the pmaports APKBUILD names 6.19.7,
but the selected linux Makefile identifies 6.19.0-rc8. These labels must not
be treated as interchangeable or proof of the identity of a downloadable boot.
The workflow checks out moving branches; no matching CI artifact was verified.
Its Phosh rootfs uses postmarketOS with systemd=never, distinct from our Debian
13/systemd Mobian userspace and downstream 4.19 diagnostic kernel.

The pinned device tree identifies Xiaomi POCO F2 Pro / xiaomi,lmi and declares
an OV13B10 rear-facing camera, FocalTech touchscreen, TFA9874 codec, fuel gauge
and charger. Declarations do not establish that the drivers work on our phone.
The external lml_test update notes report display/touch/Wi-Fi bring-up but still
report audio, battery reporting and camera failures in the last described state.
They also call a kernel stable while reporting a running rc8 version. Their
config-merging diagnosis and poweroff patches require independent source review;
no claim of official support or successful autonomy follows from these notes.

## Firmware fork comparison

After normalizing only the alioth/lmi directory component, Git trees contain
305 alioth and 319 lmi blobs: 155 shared paths have identical Git blob IDs,
53 shared paths differ, and 111 lmi paths have no normalized alioth counterpart.
Changed shared paths include ACDB calibration and sensor data. This proves
that the fork is more than a directory rename; it does not authenticate the
source ROM, licenses beyond package declarations, or device compatibility.
Only metadata was read for this comparison; no firmware binary was downloaded.

## Use for the current investigation

Downstream 4.19 trees may provide comparable PM, touch and audio implementation
choices; the mainline trees provide a separate architecture reference. Neither
is a ready replacement for the currently validated build. Preserve our external
locked inputs and hardware results, and compare a specific function or binding
before proposing any transplant. Current battery measurements and their limits
remain in the [power diagnostic record](../../kernel/diagnostics/power/README.md).


## Targeted downstream comparison

Follow-up compared pinned source files against our exact unmodified
`a5b3099017ae581aae8bf597b2f9c8c765026af1` diagnostic input. Both Android trees
contain a vendor/qcom lmi overlay identifying xiaomi lmi and board ID 37;
entries under vendor/xiaomi are symbolic links to these files. This establishes
an lmi source target, not successful hardware operation or measured stability.
Their FocalTech sources are under focaltech_touch, unlike our focaltech_touch_mi;
a missing file at our path was not treated as an absent driver.

In both references, qpnp-fg-gen4.c functions fg_delta_msoc_irq_handler,
fg_gen4_suspend and fg_gen4_resume have identical extracted bodies to our source.
No change to the gauge wake handler or these suspend hooks is therefore gained
by copying those functions. Other gauge-driver differences were not all reviewed;
identical functions do not imply identical runtime configuration or battery data.

Utsav's lpm_suspend_enter body and psci_enter_sleep implementation match ours.
PixelExperience uses a different integer-return convention at the suspend call
site, with corresponding changes in psci_enter_sleep; this is not a standalone
power-saving patch to transplant into our boolean-return implementation.
The reviewed rpmh.c differences principally add oops_in_progress handling around
completion waits, rather than identifying a normal-suspend rail-saving change.

Both dsi_drm.c references retain the conditional FOD shutdown notification that
reads sde_connector_get_lp and otherwise selects POWERDOWN. Neither reviewed
branch provides our diagnostic candidate's explicit UNBLANK-to-POWERDOWN mapping
inside that shutdown path. Whether the branch is active depends on each kernel's
config and device tree; no identical hardware fault is claimed for their builds.

No selected difference establishes a lower idle current. Keep our hardware-tested
kernel as the current base. The mainline integration's reported missing features
justify caution for that port, but do not establish that the Android references
are less stable than our kernel. No comparative boot or stability test occurred.


## Touch supply sleep-path follow-up

The already pinned and downloaded Utsav and PixelExperience FocalTech sources
both send FTS_REG_POWER_MODE_SLEEP_VALUE in their normal suspend path; neither
reviewed path cuts supplies there. Their power-off calls are in teardown/error
paths. Our selected focaltech_touch_mi normal path also requests controller sleep,
with supply cycling confined to its factory-build branch. This review supplies
no existing normal-suspend supply-cut fix to transplant and does not measure
controller current or authenticate which driver configuration each Android
build uses. Runtime supply requests must not be mistaken for a failed sleep
command solely because the regulator remains enabled.

## Battery profile and gauge-read follow-up

The selected `fg-gen4-batterydata-lmi-sun-4700mah.dtsi` is byte-identical to
the same file in both pinned Android source trees. Its SHA-256 is
`ba5cf69c105e5c8a3b2dcbb084f06b5ff62a74b0f8a3b03d0a06df7774c4c86c`.
The 416-byte profile payload has SHA-256
`583d77b61a7723fe4f40990eafa42c6283a87c41ba39a69ad2be77ce70f16050`.
All three specify revision 24, `j11sun_4700mah`, 4,700 mAh nominal capacity,
100 kOhm battery ID and 4,480,000 uV maximum voltage. The earlier live BMS
selection and approximately 99.8 kOhm reported resistance are consistent with
this source profile; this does not establish physical cell condition or
independently verify the live SRAM profile contents.

Five function bodies are also byte-identical in the selected source and both
references: `fg_get_battery_current`, `fg_get_battery_voltage`,
`fg_gen4_get_learned_capacity`, `fg_gen4_get_charge_counter` and
`fg_gen4_get_charge_counter_shadow`. The retry/current/voltage conversion
constants used by the first two functions match as well. The complete driver
files differ; this narrow comparison does not establish identical profile
selection, learning policies, IRQ handling, charging behavior or suspend.
There is no different profile or replacement read/conversion implementation
to transplant from these two references on this evidence.

Pinned primary references:

- [Utsav profile](https://github.com/UtsavBalar1231/kernel_xiaomi_sm8250/blob/99352d52fed224160798675f138d6af0051a5e5c/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-lmi-sun-4700mah.dtsi),
  [read helpers](https://github.com/UtsavBalar1231/kernel_xiaomi_sm8250/blob/99352d52fed224160798675f138d6af0051a5e5c/drivers/power/supply/qcom/fg-util.c),
  [GEN4 driver](https://github.com/UtsavBalar1231/kernel_xiaomi_sm8250/blob/99352d52fed224160798675f138d6af0051a5e5c/drivers/power/supply/qcom/qpnp-fg-gen4.c).
- [PixelExperience profile](https://github.com/PixelExperience-Devices/kernel_xiaomi_lmi/blob/d26c193dcd97812a9a565ac40fe5092cc9a18fbf/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-lmi-sun-4700mah.dtsi),
  [read helpers](https://github.com/PixelExperience-Devices/kernel_xiaomi_lmi/blob/d26c193dcd97812a9a565ac40fe5092cc9a18fbf/drivers/power/supply/qcom/fg-util.c),
  [GEN4 driver](https://github.com/PixelExperience-Devices/kernel_xiaomi_lmi/blob/d26c193dcd97812a9a565ac40fe5092cc9a18fbf/drivers/power/supply/qcom/qpnp-fg-gen4.c).

### Shared shadow-register retry defect: host proof only

Both read helpers increment `tries` in the while condition and then reject
`tries == MAX_READ_TRIES`. With a five-attempt limit, agreement first reached
on attempt five is rejected, while five consecutive disagreements leave
`tries` at six and are accepted. The shared defect is reproduced by compiling
the actual locked functions with simulated register reads, not by reimplementing
their control flow in Python.

The separate [unvalidated candidate](../../kernel/patches/diagnostics/lmi-fg-shadow-retry-unvalidated.patch)
changes only those two loop headers to an explicit zero-based for loop. SHA-256:
`24f723b585f586c8c05ef030f60439ef8ffb4cdfd236a394c7f13b6a69a45e7e`. Twenty original-function simulated cases reproduce the original
behavior; twenty patched-function cases verify agreement on attempts one through
five, rejection after five disagreements, and propagation of read errors.
Normal conversion constants, endian workaround and values are unchanged.

The [test](../../kernel/diagnostics/power/test-fg-shadow-retries.py) verifies the
external source SHA-256, applies the patch only to a temporary copy with no fuzz,
and requires that no other source text changes. The locked source, installed
kernel and all existing recipe patch sequences are unchanged. No complete
kernel build or hardware test was run. No observed live shadow mismatch has
been attributed to this defect; it neither changes charge-counter scaling nor
establishes the cause of the approximately 95 mA residual. This is a measurement
reliability candidate, not an autonomy fix or a reason to switch kernels.
