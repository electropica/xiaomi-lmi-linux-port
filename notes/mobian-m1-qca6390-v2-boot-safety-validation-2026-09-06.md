# Mobian M1 QCA6390 V2 boot-safety validation — 2026-09-06

## Scope

This note records the hardware RAM-boot bisect of the D-v43 QCA6390/Hastings
V2 kernel integration. It validates that the static integration is boot-safe.
It does not validate an N_HCI attach, create `hci0`, or claim functional
Bluetooth.

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

The bring-up is split into four distinct levels:

1. Static kernel integration and boot-safety — **PASS**.
2. Controlled userspace N_HCI attach on `/dev/ttyHS0` — **not tested**.
3. QCA6390/Hastings protocol bring-up — **not tested**.
4. BlueZ scan, pairing and real Bluetooth traffic — **not tested**.

Level 3 includes the real `qca_setup()` path, SoC/version response, baud-rate
transition, `htbtfw20.tlv` and `htnv20.bin` loading, TLV acknowledgements,
Command Complete handling and IBS. None should be inferred from the successful
boot alone.

## Conclusion and next action

```text
QCA6390_V2_STATIC_INTEGRATION_BOOT_SAFE=PASS
HASTINGS_PROTOCOL_BRINGUP_VALIDATED=NO
```

The next experiment is a controlled userspace N_HCI attach on `/dev/ttyHS0`,
with stage-specific observations and no assumption that BlueZ is relevant
before `hci0` exists.
