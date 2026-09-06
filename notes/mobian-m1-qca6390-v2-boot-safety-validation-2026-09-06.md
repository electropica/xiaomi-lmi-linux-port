# Mobian M1 QCA6390 V2 boot-safety validation — 2026-09-06

## Scope

This note records the hardware RAM-boot bisect of the D-v43 QCA6390/Hastings
V2 kernel integration and the subsequent controlled Phases A and B. Static
integration is boot-safe; Phase A also validates N_HCI attach, `hci0` creation
and automatic Hastings PATCH/NVM/Reset setup. Phase B validates active `hci0`
and one real bidirectional HCI command. It does not claim functional BlueZ,
scan or pairing operation.

## Confounding VFS defect

The raw downstream source initially lacked the historically validated
`do_new_mount()` safety net:

```c
if (!err && name && !fc->source)
	fc->source = kstrdup(name, GFP_KERNEL);
```

Without it, the downstream `fs_context` backport lost the block-device source.
`vfs_get_tree()` returned `ENOENT` for `FS_REQUIRES_DEV` before ext2/ext4 ran.
Consequently, every candidate built without this fix is non-discriminating for
Bluetooth.

## Experimental matrix

| Kernel variant | VFS fix | Hardware result | Bluetooth interpretation |
| --- | --- | --- | --- |
| HCI UART + H4 only | absent | initramfs stopped before rootfs | Non-discriminating |
| Complete QCA6390 V2 | absent | failed before normal userspace | Non-discriminating |
| HCI UART + H4 only | present | rootfs, userspace, RNDIS and SSH passed | Generic HCI UART/H4 boot-safe |
| Generic QCA, lmi selector off | present | rootfs, userspace, Phosh, RNDIS and SSH passed | QCA linkage and `qca_init()` boot-safe |
| Complete QCA6390 V2 | present | complete boot; normal behavior reported | Complete static integration boot-safe |

The complete passing configuration contained:

```text
CONFIG_BT=y
CONFIG_BT_QCA=y
CONFIG_BT_HCIUART=y
CONFIG_BT_HCIUART_H4=y
CONFIG_BT_HCIUART_QCA=y
CONFIG_BT_HCIUART_QCA6390_LMI=y
# CONFIG_SERIAL_DEV_BUS is not set
```

Artifact identity:

```text
boot image  D-repro-01-kernel-Dv43-qca6390-v2-complete-fcsource-boot.img
boot SHA256 0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad
Image SHA256 471aeec72355094754a82d478a9c4f8b4e8edb4b0a94368fb8fd594a776bbbfb
```

## Validation boundary

The bring-up is split into seven distinct levels:

1. Static kernel integration and boot-safety — **PASS**.
2. Controlled userspace N_HCI attach on `/dev/ttyHS0` — **PASS**.
3. QCA6390/Hastings setup through version, PATCH, NVM and Reset — **PASS**.
4. Controlled `hci0` activation and bidirectional HCI command — **PASS**.
5. IBS sleep/wake — **indirectly inferred; no counter proof**.
6. Stock Android BD_ADDR provenance/provisioning mechanism — **statically validated**.
7. BlueZ scan, pairing and real Bluetooth traffic — **not tested**.

## Controlled N_HCI Phase A

Phase A opened `/dev/ttyHS0`, configured 115200 RTS/CTS, selected `N_HCI=15`,
flags `0x2` and `HCI_UART_QCA=8`, and obtained `hci0`. Automatic setup logged:

```text
Bluetooth: hci0: setting up qca6390
Bluetooth: hci0: QCA controller version 0x02000200
Bluetooth: hci0: QCA Downloading qca/htbtfw20.tlv
Bluetooth: hci0: QCA Downloading qca/htnv20.bin
Bluetooth: hci0: QCA setup on UART is completed
```

The stock blobs were verified before use:

```text
htbtfw20.tlv  SHA256 008e83a926ccf9ddb18d788552cbbf0c107faf9c99d206baa39860fc619d1ea0
htnv20.bin     SHA256 ad759c2a30d2c7e50a52c4423c29b2b29604e9e31cdfeee72781ca9f35bbccc5
```

The final setup message follows successful PATCH and NVM downloads and the
final HCI Reset. The clean rollback restored N_TTY and termios, removed
`hci0`, freed the UART and preserved Phosh, RNDIS and Wi-Fi.

The logged `0x02000200` is the composite `get_soc_ver()`, whereas
`0x400a0200` is the raw `soc_id` expectation. With `rome_ver=0x0200`, the
32-bit calculation `(soc_id << 16) | rome_ver` yields `0x02000200`; firmware
selection then derives `rom_ver=0x20`. This is not an endian issue or fallback.

The 3 Mbaud path ran before the successful version/PATCH/NVM/Reset exchanges,
and the IBS-enable path follows successful setup. Both remain inferences from
control flow rather than direct UART measurement or validated IBS traffic.

## Controlled HCI Phase B

A first repeated attach, attempted while `bt_power` remained ON after Phase A,
read the version but timed out at the first PATCH TLV segment. Closing N_HCI
does not reset the controller. A single controlled `bt_power` OFF/ON cycle
then disabled and re-enabled reset, SW_CTRL and the five QCA6390 rails. The
system remained stable and the next attach began from a clean controller.

The continuous retry completed Hastings setup. It logged one transient
`Frame reassembly failed (-84)`, followed by the expected version, PATCH, NVM
and final setup success; the transient did not block Reset, HCI activation or
later traffic.

After the two-second auto-off, `hci0` remained registered and reported DOWN:

```text
flags=0x00000000 up=0 type=0x03
bdaddr=00:00:00:00:5a:ad
features=ff:fe:8f:fe:d8:3f:5b:87
ACL_MTU=1024 ACL_PKTS=8 SCO_MTU=240 SCO_PKTS=4
```

`HCIDEVUP` passed and flags became `0x00000005` with `up=1`. A raw HCI socket
bound to dev 0. After three seconds idle, one explicit Read Local Version
command produced a matching Command Complete with opcode `0x1001`, status
`0x00`, and:

```text
hci_ver=0x0b hci_rev=0x0000
lmp_ver=0x0b manufacturer=0x001d lmp_subver=0x27ec
```

Across that explicit command, `CMD_TX` increased from 883 to 884 and `EVT_RX`
from 108 to 109; `ERR_TX` and `ERR_RX` remained zero. This is a real
bidirectional controller exchange, not a cached `HCIGETDEVINFO` result.

No IBS debugfs counters were available. A valid response after an idle period
longer than the two-second IBS timeout supports `IBS_FUNCTIONAL=INFERRED`, but
does not directly prove individual IBS sleep/wake exchanges. `HCIDEVDOWN`
passed. Terminating the sole attach restored N_TTY and termios, freed
`/dev/ttyHS0`, removed `hci0`, and preserved rfkill, Phosh, RNDIS, Wi-Fi and
normal temperatures. No scan, pairing or BlueZ operation occurred.

The observed BD_ADDR `00:00:00:00:5a:ad` is non-zero and sufficient for HCI
activation. Its stock Android provisioning mechanism has since been
statically reconstructed: Xiaomi's `/vendor/bin/nv_mac` reads Bluetooth NV
operation `0x01bf` using QMI service `0xffe4`, message `0x0002`, writes the
six-byte result to `/data/vendor/mac_addr/bt.mac`, and
`init.mi.btmac.sh` publishes the converted value through
`persist.vendor.service.bdroid.bdaddr`. No QMI request was executed as part of
that static investigation, so the value returned by operation `0x01bf` on
this individual handset remains runtime-unverified.

## Conclusion and next action

```text
QCA6390_V2_STATIC_INTEGRATION_BOOT_SAFE=PASS
N_HCI_ATTACH_VALIDATED=YES
HASTINGS_PROTOCOL_SETUP_VALIDATED=YES
HCI_DEVICE_UP_VALIDATED=YES
HCI_BIDIRECTIONAL_COMMAND_VALIDATED=YES
READ_LOCAL_VERSION_VALIDATED=YES
IBS_FUNCTIONAL=INFERRED
IBS_COUNTER_PROOF=NO
BD_ADDR_ANDROID_PROVISIONING_STATICALLY_VALIDATED=YES
BD_ADDR_QMI_SERVICE=0xffe4
BD_ADDR_QMI_MESSAGE=0x0002
BD_ADDR_NV_OPERATION=0x01bf
BD_ADDR_QMI_EXECUTED=NO
BLUEZ_FUNCTIONAL_VALIDATION=NO
```

The stock Android provenance/provisioning mechanism is now statically
established. The next step is to integrate the required address source on
Mobian before BlueZ scan and pairing validation.
