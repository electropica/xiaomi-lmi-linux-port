# Mobian M1 QCA6390 Hastings HCI bring-up design — 2026-09-05

## Scope and verdict

This note began as the static design milestone following the
hardware-validated Qualcomm PDR/ADSP/NGD/BTFM SLIM path. The resulting V2
micro-backport has since passed a hardware RAM-boot safety matrix, but no HCI
controller has yet been created: the last observed M1 state still had an empty
`/sys/class/bluetooth` and no `hci0`.

```text
MINIMAL_BACKPORT_FEASIBLE=YES
```

At the time of the original design conclusion no Bluetooth kernel patch or
defconfig change had been applied. The reviewed V2 implementation now exists;
it deliberately makes no DT change and retains the non-serdev architecture.

## Hardware and stock architecture

The `lmi` Bluetooth controller is Qualcomm QCA6390, called `hastings` by the
stock Android stack. The stock QTI HAL identifies revision
`HASTINGS_VER_2_0` and contains `UartController`, `HciUartTransport` and IBS
handling.

The HCI transport is QUPv3 SE6:

```text
MMIO             0x998000
compatible       qcom,msm-geni-serial-hs
Linux device     /dev/ttyHS0
GPIO 16..19      CTS, RTS, RX, TX
wake IRQ         GPIO19
wakeup byte      0xFD
```

Xiaomi enables this UART in its SM8250 DT, but defines no Bluetooth serdev
child beneath it. Android correspondingly opens `/dev/ttyHS0` directly from
the vendor HAL.

Controller power is a separate downstream path:

```text
DT node          /vendor/bt_qca6390
compatible       qca,qca6390
driver           drivers/bluetooth/bluetooth-power.c
Android device   /dev/btpower
reset GPIO       21
SW_CTRL GPIO     124
supplies         five dedicated QCA6390 rails
```

For the first HCI bring-up, power remains external to `hci_qca`, matching the
separation in the downstream platform.

The stock Bluetooth partition contains:

```text
htbtfw10.tlv
htbtfw20.tlv
htnv10.bin
htnv20.bin
```

The Hastings 2.0 path in the Android HAL selects `htbtfw20.tlv` and
`htnv20.bin`.

## What BTFM SLIM does and does not do

The previously validated `btfmslim-driver` is the SLIM audio/FM side of the
combo device. Its probe establishes codec/DAI connectivity for Bluetooth
audio and FM; it does not allocate or register a Linux `hci_dev`. Successful
BTFM SLIM enumeration is therefore a prerequisite for audio integration, not
the event expected to create `hci0`.

HCI instead uses the separate GENI UART. D-v43 provides line discipline
`N_HCI=15` and protocol number `HCI_UART_QCA=8`. With the relevant kernel
options enabled, userspace can open and configure `/dev/ttyHS0`, apply N_HCI,
set the HCI UART flags, select the QCA protocol, and keep the descriptor open.
That path can register an HCI device without a serdev DT child.

## D-v43 gap

D-v43 contains `drivers/bluetooth/hci_qca.c`, `btqca.c` and `btqca.h`, including
the Qualcomm TLV/NVM machinery. Its SoC enum only covers `QCA_AR3002`,
`QCA_ROME` and `QCA_WCN3990`; it has no QCA6390/Hastings identity or Hastings
firmware-name selection.

The tested lmi kernel also lacks:

```text
CONFIG_BT_HCIUART
CONFIG_BT_HCIUART_H4
CONFIG_BT_HCIUART_QCA
```

while retaining:

```text
CONFIG_BT=y
CONFIG_SERIAL_MSM_GENI=y
CONFIG_MSM_BT_POWER=y
```

The old line-discipline path is not usable merely by enabling Kconfig.
`qca_setup()`, `qca_check_speeds()` and `qca_set_baudrate()` contain serdev
data accesses which are not safe when `hu->serdev == NULL`. A generic NULL
guard alone would still leave the wrong SoC identity and firmware selection.

## Minimal backport boundary

### A — indispensable for the first bring-up

- Add `QCA_QCA6390` to `enum qca_btsoc_type`.
- Teach `qca_uart_setup()` to select `qca/htbtfw%02x.tlv` and
  `qca/htnv%02x.bin` for QCA6390.
- Map Hastings 2.0 to `rom_ver=0x20`, selecting the stock `20` files.
- Make the non-serdev execution of `hci_qca` internally coherent, including
  setup, speed validation and baud changes.
- Supply `QCA_QCA6390` only through a dedicated lmi attach path; preserve the
  historical `QCA_ROME` fallback for other QCA line-discipline users.
- Enable `CONFIG_BT_QCA=y`, `CONFIG_BT_HCIUART=y`,
  `CONFIG_BT_HCIUART_H4=y` and `CONFIG_BT_HCIUART_QCA=y` while preserving
  `CONFIG_BT=y`, `CONFIG_SERIAL_MSM_GENI=y` and `CONFIG_MSM_BT_POWER=y`.
- Keep power sequencing external to `hci_qca` for this experiment.

The exact lmi-only selector is part of the micro-backport design task. It must
not infer QCA6390 for every non-serdev QCA UART.

### B — after the first controller bring-up

- Provide a persistent, supervised userspace attach process.
- Establish the production Bluetooth address path.
- Add focused diagnostics.
- Validate suspend/resume and IBS behavior.
- Make attach, shutdown and power cycling robust.

### C — explicitly outside the first backport

- A new Bluetooth serdev DT child or `CONFIG_BT_HCIUART_SERDEV`.
- Modern Bluetooth pwrseq support.
- Moving regulators or power control into `hci_qca`.
- ACPI support.
- Modern Qualcomm coredump infrastructure.
- QCA6390-specific modern shutdown machinery.
- Support for unrelated newer Qualcomm SoCs.
- Wholesale replacement of the downstream QCA stack with current mainline.

## V2 implementation and boot-safety validation

The implemented micro-backport adds `QCA_QCA6390`, the Hastings 2.0 firmware
names, QCA6390 response handling, and a coherent lmi-only non-serdev selector.
It enables `BT_HCIUART`, H4, QCA and `BT_HCIUART_QCA6390_LMI` while preserving
`SERIAL_DEV_BUS=n` and external controller power.

The first rebuilt images also revealed that the raw downstream source had
lost the project's historically validated `fc->source` safety net. Without
that independent VFS fix, legacy ext2/ext4 block mounts failed before their
filesystem drivers, making the affected boot failures non-discriminating for
Bluetooth. After restoring the two-line `do_new_mount()` fix, all three
increasingly complete variants RAM-booted through rootfs and userspace:

- HCI UART and H4 only;
- generic QCA with the lmi selector disabled;
- complete QCA6390 V2 with the lmi selector enabled.

The complete image used kernel SHA-256
`471aeec72355094754a82d478a9c4f8b4e8edb4b0a94368fb8fd594a776bbbfb`.
Its boot image, `D-repro-01-kernel-Dv43-qca6390-v2-complete-fcsource-boot.img`,
had SHA-256
`0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad`.
The operator reported normal behavior.

This proves only static integration boot-safety. Detailed evidence and the
full matrix are in
`notes/mobian-m1-qca6390-v2-boot-safety-validation-2026-09-06.md`.

## Open risks

The following remain untested and must not be presented as working:

- compatibility of D-v43's older TLV/NVM parser with the Hastings images;
- the exact initial/operational baud-rate transition on QUPv3 SE6;
- ordering between external QCA6390 power and N_HCI attach;
- IBS behavior on this downstream UART/kernel combination;
- clean shutdown, detach, suspend and resume.

## Next action

Prepare a controlled userspace N_HCI attach test on `/dev/ttyHS0`. It must
separate controller power, UART setup, HCI registration, version detection,
baud transition, PATCH/NVM download and IBS so the first failing stage is
observable. BlueZ functional testing follows only after `hci0` exists.
