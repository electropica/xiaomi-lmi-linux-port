# lmi Android/Mobian dual-boot candidate

This is an operator-run build recipe, not an installed or hardware-validated
dual boot. It does not contact a handset, repartition, format, flash or reinstall
Android. No new kernel compilation is needed. The existing RPMh kernel, DTB,
second stage and recovery DTBO segments are retained byte-for-byte; only one
initramfs function changes. Host tests check these invariants and boot ID.

## Proposed arrangement

- Keep Android's existing system/vendor/firmware layout. Android uses a smaller
  `userdata`, with its normal F2FS/encryption policy and its own boot image.
- Reserve a **separate 16 GiB physical partition named `mobian`** at the end of
  the current userdata range. It contains the existing nested boot/root format.
- Mobian's dedicated boot waits only for `mobian`, checks exact container size
  and both filesystem UUIDs, then hands the bounded loop to the existing boot
  sequence. Missing/wrong storage halts; there is no fallback to Android data.
  Normal root expansion remains limited to the dedicated loop/container.
- First version: Windows PC selects either OS using `fastboot boot`. There is
  no newly developed on-phone boot menu, no A/B assumption and no replacement
  of the Lineage recovery. The operator subsequently requested Mobian as the
  default and an autonomous handset menu with a 15-second timeout. Those default
  boot/menu changes are not yet installed. See [the qualification boundary](BOOT-MENU.md).

The live GPT has 4096-byte logical sectors and 64 entries; userdata is entry
34 and last. A text-only proposal keeps its start, reduces its end, and adds
entry 35. **Do not apply an old plan without a fresh GPT validation.** Android
OTA/factory-reset preservation of a custom partition is not yet validated.

The operator explicitly selected a fresh build instead of backing up today's
installation. Migration therefore discards today's Mobian local data/settings
and any Android data; package/feature reconstruction is not personal-data
recovery. No destructive command is supplied or executed by this build.

## Full current image

`build.sh` invokes the maintained `build/build-complete-lmi.sh` entry point,
including the qualified homedrag7 Phosh, matching Phoc, GSD, NPU policy,
application/audio/torch layers and complete Snapshot bundle. All normal recipe
input guards remain. It does not reuse an old userdata as if it contained the
latest runtime package changes. Existing firmware and source inputs stay private.

Run from Julien's WSL terminal after host validation:

```sh
bash /mnt/c/Users/julien/Documents/ChatGPT/Mobian/work/dualboot-candidate/build.sh
```

Outputs in the repository's ignored output directory:

- `mobian-lmi-dualboot-20261021.img.android-sparse.img`: install ONLY to the new
  dedicated `mobian` partition, never to Android userdata.
- `mobian-lmi-dualboot-20261021-boot/mobian-dualboot-boot.img`.
- Boot hashes and a **design-only** layout plan; neither is permission to flash.

If the full image completed but artifact finalization failed, use
`bash /home/linuxagent/xiaomi-lmi-linux-port/build/dualboot/finish.sh` instead
of repeating the complete build. This checks the existing image identities and
uses sudo only for writing the new boot-artifact folder under root-owned output/.
It never changes ownership or permissions of the existing output tree.

The full image is initially about 4.6 GB; its root expands inside the dedicated
16 GiB container on first boot using the existing initramfs logic. The two
filesystem UUIDs are checked on the generated image before publishing the boot.

## Autonomous selection after installation qualification

`switch-os.py` is a Windows controller, not a daemon. Once both OS boots and
accesses have been validated, configure the paths of Windows adb/fastboot,
both pinned boot hashes, and the existing WSL SSH key. Root/ADB authorization
must be configured once. Never copy credentials into the public repository.

The controller refuses execution while `dualboot_installation_validated` is
false. Before allowing autonomous Mobian departure, qualification must also
create `/etc/lmi/dualboot-installation-validated` with exactly
`lmi-dualboot-v1` on the verified dedicated root. Do not add the marker to an
unvalidated image or the present userdata installation.

The controller checks image hashes, exactly one device, `product=lmi`, uses
bounded waits, asks the running OS to enter Fastboot, boots the selected image,
then waits for Android boot completion or the Mobian marker. **It never calls
flash, erase, format or set_active.** Failure ends the operation rather than
cycling images or reinstalling an OS. PC, cable and working USB access are
required; unplugged battery tests preclude autonomous selection until replug.

## Before any migration

Build success alone is insufficient. Qualify current recovery tooling, fresh
primary/backup GPT, free entry/range, Android metadata/encryption initialization,
artifact transfer/hashes and both boot paths. Prepare the exact manual migration
and a return-to-single-OS procedure separately. Recovery boot and the first
Android setup will require operator participation. No claim of no-interaction
installation or validated OTA behavior is made.
