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
