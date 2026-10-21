# Dedicated Mobian first boot — October 21, 2026

The operator manually executed the qualified GPT migration and reported its
readback-success message. After a recovery restart, target reads confirmed
mobian at /dev/block/sda35, 17179869184 bytes, and userdata at 225677672448 bytes.
The operator then performed recovery Format data/factory reset. Both block-device
sizes remained unchanged afterward; no block-backed filesystem was mounted in
the inspected recovery. The old Mobian userdata installation was discarded as
explicitly selected by the operator. No claim of an independent F2FS superblock
validation is made; blkid is not available in that recovery.

The operator's guarded Windows flash wrote only mobian, all five sparse chunks
reported OKAY, then requested a temporary boot of the pinned adapted Mobian boot.
Native Fastboot warned that it skipped copying an AVB footer for the sparse
image; all writes completed, and the subsequent actual dedicated-root checks
below succeeded. No boot, recovery, super or other partition was flashed by that
operation. Default boot policy is not established by fastboot boot.

SSH qualification confirms root /dev/loop0p2 is backed by /dev/sda35, the dedicated
16 GiB container. The expanded ext4 filesystem reports 16587722752 bytes total
and 12168536064 available to unprivileged use. Android userdata is not mounted.
The kernel remains 4.19.325-cip128-st12-perf-ga5b3099017ae-dirty. Installed packages:

- Phosh and common: 0.46.0-3+deb13u1+lmigaugewake3+homedrag7.
- Phoc: 0.46.0-1+lmishelldnd1.
- GSD and common: 48.1-1+lmiquietgauge3.

dpkg audit is empty, the graphical session is active, charging resumed, the
RTC alarm is empty, there is no pending NPU restoration state, and the normal
battery suspension timeout is 900 seconds. The operator reports successful boot
and normal handset behavior. Audio, camera and long standby are not newly
revalidated by this first-boot check.

Android's first boot in the resized-data layout remains pending. An attempted
Mobian-to-Fastboot request was blocked by its preliminary shell comparison and
returned exit 1 before reboot; no write occurred. Mobian remains running.

The operator now requests an autonomous handset Android/Mobian menu, 15-second
timeout, Mobian default. It supersedes the original Android-default proposal.
No menu/default change has been installed, and the PC selector remains locked.
The active kernel reports CONFIG_KEXEC unset. [Menu qualification notes](../../build/dualboot/BOOT-MENU.md)
separate the requested behavior from unvalidated source leads. The prepared
Android-default flashing helper now rejects execution without an additional
explicit Android-default override; it has not been executed.
