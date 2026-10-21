# Android kernel and init reached; legacy DT fstab shadows logical partitions

## Handset evidence

The dtbo1 RAM image (SHA256
969ee0c3d49083adfd17ea199575df55b211c66b5071d96fb24c8701fb82bed1)
reboots to Fastboot after LineageOS selection. The operator restarted installed
Mobian. Archived console-ramoops was copied privately to the host; unlike the
older pmsg record, it contains the Android kernel startup and first-stage abort.

The console shows Lineage kernel 4.19.325-cip131-st15-perf-g71b13e62f057,
`Run /init as init process`, and `init first stage started!`. It waits ten seconds
for physical system/vendor devices, reports `Failed to create devices required
for first stage mount`, then InitFatalReboot signal 6 and a restart command of
bootloader at approximately 12.3 seconds. This demonstrates kernel and Android
first-stage init execution, not a completed Android userspace boot. No kernel
panic is needed to explain the observed Fastboot return.

## Input/source comparison

All three DTBs in the pinned Android boot contain an active legacy
/firmware/android/fstab/vendor entry pointing to a physical by-name/vendor,
with ext4 and wait,avb. The pinned ramdisk's system/etc/fstab.qcom instead
defines system/system_ext/product/vendor/odm as logical first-stage mounts,
including vendor as erofs. The current super layout uses logical partitions.

[LineageOS 23.2 first_stage_mount.cpp](https://raw.githubusercontent.com/LineageOS/android_system_core/lineage-23.2/init/first_stage_mount.cpp)
reads the DT fstab first and falls back to the ramdisk fstab only when the DT
read fails. Its device discovery excludes logical partitions from physical
uevent polling. This explains the physical system/vendor wait when the legacy
table takes precedence. The [AOSP dynamic-partition requirements](https://source.android.com/docs/core/ota/dynamic_partitions/implement)
explicitly require fstab entries in the ramdisk rather than DT/DTBO.

Flags such as loop.max_part=7 also exist in the original Android boot header;
their presence alone is not evidence of Mobian command-line contamination.
Command-line cleanup is deliberately not part of this correction.

## Minimal RAM-only change

lmi-android-fstab.h is called after Linux preparation and before execution at
diagnostic stage 14. It requires the Android configuration tag, a valid FDT,
android,fstab compatibility and the exact known legacy physical vendor path.
It removes only /firmware/android/fstab from the in-memory Android DT. An
unexpected table is rejected rather than removed. An absent table is harmless.
The pinned ramdisk, AVB rules, partitions, super metadata and installed boot
are unchanged. Existing diagnostics remain available for pre-handoff errors.

## Host validation and next step

test-android-fstab.py compiles the actual C function and calls it with libfdt
on each of the three real base DTBs after applying the unique board-37 overlay.
All other properties remain byte-identical at the property level. Other OS
tags and unexpected vendor paths are rejected without mutation; repeat calls
are harmless. The original ramdisk's logical ext4 system and erofs vendor
first-stage entries are checked. Four C units pass Clang 14 ARM64 syntax checks
with generated flags/-Werror, and fifteen-file restoration/tamper tests pass.

This fstab1 correction is not yet built or hardware validated. The expected
next observation is logical-partition creation and progress past the previous
first-stage abort; additional Android startup issues may remain.

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build --with-lineage
```

The manifest variant ends in prepi-ffs3-fstab1. Qualify the resulting image and
use a fresh Windows temporary launcher. No experimental menu is ready to flash.

## Android logical-fstab image compiled; handset test pending

The operator built fstab1: 25993216 bytes, SHA256
eae891e3bbe03d2b15857a11319000da4eca81adac009d093126593bb548ad1f.
All fifteen source hashes match, the lmi memory map is unchanged and PrePi
replay passes on the rebuilt FD. Windows transfer and plan-only launcher
preflight passed. test-lineage-fstab-windows.py pins this exact image and
requires the SSH guard-completion marker before waiting for Fastboot.
No phone command or flash was performed during qualification. The removal of
the legacy DT table and progress past first-stage logical mounting remain
pending handset observation; Android userspace is not yet validated.

## Recovery user-init failure: direct stock-Android control prepared

fstab1 reaches recovery with init_user0_failed. The original Android failure
trace has been replaced by recovery activity; the exact data-initialization
failure is unknown. Mobian is restored. Read-only checks confirm separate
partitions; raw userdata can be encrypted, so its signature does not establish
corruption. Cache logs were captured with a temporary ro,noload mount, removed
afterwards. No wipe, flash or partition change was performed.

A Windows helper for the exact stock Lineage RAM boot passes plan-only image
verification. This will distinguish a menu-specific failure from normal Android
startup failure. See build/boot-menu/chainload/ANDROID-DATA-CONTROL.md. No new
build required. Execution and full Android startup remain pending. Security
context/key-management differences are hypotheses, not established causes.
