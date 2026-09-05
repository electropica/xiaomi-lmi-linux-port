# Mobian M1 QCA6390 Hastings HCI bring-up design — 2026-09-05

## Scope and verdict

This note records the static design milestone following the hardware-validated
Qualcomm PDR/ADSP/NGD/BTFM SLIM path. It does not claim that an HCI controller
has been created: M1 REPRO v11 still had an empty `/sys/class/bluetooth` and no
`hci0`.

```text
MINIMAL_BACKPORT_FEASIBLE=YES
```

No Bluetooth kernel patch, defconfig change or DT change had been applied when
this conclusion was recorded.

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

## Open risks

The following remain untested and must not be presented as working:

- compatibility of D-v43's older TLV/NVM parser with the Hastings images;
- the exact initial/operational baud-rate transition on QUPv3 SE6;
- ordering between external QCA6390 power and N_HCI attach;
- IBS behavior on this downstream UART/kernel combination;
- clean shutdown, detach, suspend and resume.

## Next action

Design the first micro-backport as a small, separately reviewable kernel and
configuration change. Do not start a build simultaneously: first verify the
selector isolation, NULL-safe non-serdev flow, firmware-name construction and
Kconfig dependency closure statically.
