# Mobian M1 QCA6390 Hastings HCI bring-up design — 2026-09-05

## Scope and verdict

This note began as the static design milestone following the
hardware-validated Qualcomm PDR/ADSP/NGD/BTFM SLIM path. The resulting V2
micro-backport has since passed both a hardware RAM-boot safety matrix and a
controlled Phase A N_HCI attach. That attach created `hci0` and completed the
automatic QCA6390 PATCH/NVM/Reset setup. Controlled Phase B has also brought
`hci0` UP and validated one real bidirectional HCI command. BlueZ operation,
scan and pairing remain outside the validated boundary.

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

## Controlled Phase A validation

The first real attach used `/dev/ttyHS0` at 115200 with RTS/CTS, applied
`N_HCI=15`, flags `0x2` and `HCI_UART_QCA=8`, and kept the descriptor open.
It created `hci0` and produced:

```text
Bluetooth: hci0: setting up qca6390
Bluetooth: hci0: QCA controller version 0x02000200
Bluetooth: hci0: QCA Downloading qca/htbtfw20.tlv
Bluetooth: hci0: QCA Downloading qca/htnv20.bin
Bluetooth: hci0: QCA setup on UART is completed
```

The exact stock artifacts used were:

```text
qca/htbtfw20.tlv  008e83a926ccf9ddb18d788552cbbf0c107faf9c99d206baa39860fc619d1ea0
qca/htnv20.bin     ad759c2a30d2c7e50a52c4423c29b2b29604e9e31cdfeee72781ca9f35bbccc5
```

The final message is reached only after successful PATCH and NVM downloads
and a successful final HCI Reset. Cleanup restored N_TTY and termios, closed
the descriptor, removed `hci0`, and left the system stable.

`0x02000200` is the composite `get_soc_ver()` value, not the raw Hastings
`soc_id` expectation `0x400a0200`. With `soc_id=0x400a0200` and
`rome_ver=0x0200`, 32-bit arithmetic gives
`(soc_id << 16) | rome_ver = 0x02000200`. The firmware-name calculation then
gives `rom_ver=0x20`. This is neither an endian conversion nor a fallback.

The code traverses the 3 Mbaud transition before the successful version and
download exchanges, and enables IBS after `qca_uart_setup()` succeeds. The
UART rate was not independently measured.

## Controlled Phase B validation

A repeated attach without a hardware reset timed out during PATCH because the
controller remained powered in its previously initialized state. A controlled
`bt_power` OFF/ON cycle then toggled reset, SW_CTRL and all five QCA6390 rails.
From that clean state, one continuous attach completed Hastings setup and
Phase B. One transient `Frame reassembly failed (-84)` did not block any later
step.

After auto-off, `hci0` reported DOWN with type `0x03`, features
`ff:fe:8f:fe:d8:3f:5b:87`, ACL MTU/count `1024/8`, SCO MTU/count `240/4`, and
BD_ADDR `00:00:00:00:5a:ad`. `HCIDEVUP` passed. A raw socket bound to dev 0
then sent exactly one Read Local Version command (`0x1001`) after three seconds
idle and received Command Complete status `0x00`:

```text
hci_ver=0x0b
hci_rev=0x0000
lmp_ver=0x0b
manufacturer=0x001d
lmp_subver=0x27ec
```

`CMD_TX` changed from 883 to 884 and `EVT_RX` from 108 to 109, while both error
counters remained zero. This proves real bidirectional HCI traffic rather than
a cached kernel query. IBS debugfs counters were unavailable; success after
an idle interval longer than the two-second timeout makes IBS functionality an
inference, not direct sleep/wake proof. `HCIDEVDOWN`, N_TTY/termios restoration
and detach all passed, leaving no `hci0` or tty owner and preserving Phosh,
RNDIS and Wi-Fi.

## Open risks

The following remain untested and must not be presented as working:

- direct measurement of the operational UART rate;
- direct IBS sleep/wake counter evidence;
- provenance and production provisioning of BD_ADDR `00:00:00:00:5a:ad`;
- BlueZ, scan, pairing, connections and real Bluetooth data traffic;
- clean shutdown, detach, suspend and resume.

## Next action

Determine the provenance and correct production provisioning of the observed
BD_ADDR before enabling BlueZ or attempting scan and pairing.
