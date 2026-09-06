# Mobian M1 SDX55 DV121 SBL/Sahara milestone — 2026-09-06

## Scope

This note records the first hardware validation that carries the Xiaomi lmi
external SDX55M through ESOC power-up, PCIe enumeration and MHI/BHI SBL loading
into the BL/Sahara environment. It does not claim a complete Sahara transfer,
AMSS/mission mode, a functional cellular modem, voice, SMS or data.

The reference kernel source HEAD is
`3d6dacc48eda5acd59b40fedb33ae640e3164c1e`. The RAM-boot image used by the
operator was
`C:\Users\julien\Downloads\D-repro-01-kernel-Dv43-qca6390-v2-complete-fcsource-boot.img`;
runtime reported
`Linux PocoF2Pro 4.19.325-cip128-st12-perf-ga5b3099017ae-dirty`.

On this setup, a plain reboot enters recovery and loses SSH. Returning to
Mobian requires entering fastboot manually and RAM-booting the reference image
with the Windows tool at
`C:\Users\julien\Downloads\platform-tools\fastboot.exe`. `getvar` must not be
used outside fastbootd. Transfers between WSL and the operator go through
`C:\Users\julien\Downloads`.

## ESOC and helper architecture

The runtime identity is:

```text
compatible=qcom,ext-sdx55m
esoc_name=SDX55M
esoc_link=PCIe
esoc_link_info=0306_02.01.00
/dev/esoc-0
/dev/subsys_esoc0
```

The relevant kernel path is:

```text
subsys_device_open()
  -> subsystem_get()
  -> mdm_subsys_powerup()
  -> ESOC_PWR_ON
  -> mdm_do_first_power_on()
  -> SDX55 power-on
```

The initial helper incorrectly used one thread to open `/dev/subsys_esoc0`
and then call `ESOC_WAIT_FOR_REQ`. The open remains blocked in
`mdm_subsys_powerup()` while boot requests must be serviced, so the request
loop was never reached. DV119 registers the request engine first, waits in
`ESOC_WAIT_FOR_REQ` on the main thread, and performs the subsystem open in a
second thread. The validated DV119/DV120 ARM64 helper has SHA256:

```text
966a1810f7e43fc398e10d91fd7f3c5db25eb9d6485c3ecf67a09cbfec852bbf
```

## Xiaomi SDX55 firmware

The source ROM is:

```text
lmi_global_images_V14.0.1.0.SJKMIXM_20230317.0000.00_12.0_global
```

`images/NON-HLOS.bin` is FAT16. Its `image/sdx55m` directory was extracted to
`analysis/dv111-sdx55m-extracted` and contains 18 files:

```text
acdb.mbn
aop.mbn
apdp.mbn
apps.mbn
devcfg.mbn
efs1.bin
efs2.bin
efs3.bin
hyp.mbn
mdmddr.mbn
modemr.jsn
multi_image.mbn
multi_image_qti.mbn
qdsp6sw.mbn
sbl1.mbn
sec.elf
tz.mbn
xbl_cfg.elf
```

The MHI driver explicitly maps Qualcomm PCI device `0x0306` to
`sdx55m/sbl1.mbn`. `mhi_fw_load_handler()` obtains it with
`request_firmware()` and passes it to `mhi_fw_load_sbl()` for BHI transfer.
The extracted file, installed at `/lib/firmware/sdx55m/sbl1.mbn`, was verified
again after the current RAM boot:

```text
size=548056
sha256=0fd2fdaf19831c8ff482ca77ca236ee282101c9bdf5ab7b46dc4e24a484e84dc
```

The former `Error loading fw, ret:-2` was caused by this file being absent and
is no longer the active blocker.

## Sahara image table

The Qualcomm SDX55 helper maps 17 Sahara IDs:

| ID | Source |
|---:|---|
| 21 | `/vendor/firmware_mnt/image/sdx55m/sbl1.mbn` |
| 37 | `/vendor/firmware_mnt/image/sdx55m/multi_image.mbn` |
| 38 | `/vendor/firmware_mnt/image/sdx55m/xbl_config.elf` |
| 36 | `/vendor/firmware_mnt/image/sdx55m/multi_image_qti.mbn` |
| 41 | `/vendor/firmware_mnt/image/sdx55m/devcfg.mbn` |
| 25 | `/vendor/firmware_mnt/image/sdx55m/tz.mbn` |
| 23 | `/vendor/firmware_mnt/image/sdx55m/aop.mbn` |
| 8 | `/vendor/firmware_mnt/image/sdx55m/qdsp6sw.mbn` |
| 6 | `/vendor/firmware_mnt/image/sdx55m/apps.mbn` |
| 16 | `/dev/block/bootdevice/by-name/mdm1m9kefs1` |
| 17 | `/dev/block/bootdevice/by-name/mdm1m9kefs2` |
| 20 | `/dev/block/bootdevice/by-name/mdm1m9kefs3` |
| 29 | `/vendor/firmware_mnt/image/sdx55m/acdb.mbn` |
| 34 | `/dev/block/bootdevice/by-name/mdmddr` |
| 40 | `/vendor/firmware_mnt/image/sdx55m/apdp.mbn` |
| 33 | `/vendor/firmware_mnt/image/sdx55m/hyp.mbn` |
| 42 | `/vendor/firmware_mnt/image/sdx55m/sec.elf` |

The Xiaomi partition table contains `mdm1m9kefs1`, `mdm1m9kefs2`,
`mdm1m9kefs3` and `mdmddr`. A filename discrepancy remains unresolved: the
helper requests `xbl_config.elf`, while `NON-HLOS.bin` provides
`xbl_cfg.elf`. No alias or substitution is validated by this milestone.

## DV121 evidence

The DV118 baseline immediately before the experiment had no PCI `17cb:0306`,
no MHI `0306_*`, no previous helper, and did have both ESOC nodes and the
verified SBL1.

DV121 started helper PID 3951. After ten seconds its output was:

```text
DV119_HELPER_START
ESOC_PATH=/dev/esoc-0
SUBSYS_PATH=/dev/subsys_esoc0
ESOC_OPENED=YES
REQUEST_ENGINE_REGISTERED=YES
REQUEST_LOOP_START=YES
POWERUP_THREAD_START
ESOC_REQUEST=1
ESOC_REQ_IMG_RECEIVED=YES
```

The main thread was sleeping in `esoc_dev_ioctl`/`ESOC_WAIT_FOR_REQ`; the
power-up thread was in uninterruptible sleep in `mdm_subsys_powerup`. Hardware
state after power-up was:

```text
PCI device: /sys/bus/pci/devices/0002:01:00.0
PCI ID:     17cb:0306
driver:     mhi

MHI devices:
0306_02.01.00
0306_02.01.00_BL
0306_02.01.00_SAHARA

Sahara node:
/dev/mhi_0306_02.01.00_pipe_2
```

The Sahara node exactly matches the Qualcomm helper construction from
`esoc_link_info=0306_02.01.00` plus `MHI_PIPE_SAHARA="_pipe_2"`.

No Sahara image transfer was started, and neither `ESOC_IMG_XFER_DONE` nor
`ESOC_BOOT_DONE` was sent.

## Validated boundary

DV121 proves that the Xiaomi SBL1 is accepted by the MHI/BHI path far enough
to:

- power on and enumerate SDX55M as PCI `17cb:0306`;
- bind the MHI driver;
- enter the BL/Sahara execution environment;
- create the expected BL and Sahara MHI devices;
- expose `/dev/mhi_0306_02.01.00_pipe_2`;
- deliver `ESOC_REQ_IMG` to the registered request engine.

It does not prove:

- a complete Sahara image transfer;
- `ESOC_IMG_XFER_DONE` or `ESOC_BOOT_DONE`;
- transition to SDX55 AMSS/mission mode;
- working cellular registration, voice, SMS or data.

Bluetooth/QCA6390 is a separate workstream with its own documented HCI
validation and must not be described as fully resolved here.

## Next step

Prepare, without inventing a resolution for `xbl_config.elf` versus
`xbl_cfg.elf`, the complete SDX55 Sahara image-transfer sequence and the
subsequent ESOC notifications.
