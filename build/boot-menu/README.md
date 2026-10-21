
## 2026-10-21: Android boots from the temporary menu

The operator confirmed a successful LineageOS start after selecting it in the
temporary menu. Native Windows ADB independently reported sys.boot_completed=1,
file-based encryption, and metadata encryption enabled. Tested image: 25993216
bytes, SHA256 71e226f1a8adaf5d0574d1311d686143694404f49ab62df5d343c8a36c3c5196.

Only header offsets 44 and 47 differ from the previous fstab1 image: the OS
version field now matches pinned Android 16 / September 2026. A successful stock
Android boot occurred between the failed and successful menu trials, so the
exact internal vold/keymaster cause remains unproven. No keys or encryption
policy were changed; no flash, wipe or partition change occurred in this trial.

The recipe now applies this header alignment automatically to Lineage menu
outputs and records the OS-version context in its artifact manifest. Host checks
reproduce the tested image from the previous output; shell/Python syntax pass.
No new firmware compilation was run. The existing WSL cached output still has
the old header; the tested derived image is distinct.

The menu remains temporary and MUST NOT be flashed. Mobian currently restarts
the installed boot image; it needs direct chainloading before a persistent menu
can safely replace that image. Touch input remains unqualified; buttons work.

# lmi handset boot-menu candidate

Dedicated recipe for the requested on-phone Android/Mobian menu: Mobian by
default after 15 seconds, without a PC once qualified and installed.

**Current status: the menu and Android kernel/first-stage init execute on the
handset. Android then aborts while waiting for physical system/vendor because
the legacy DT fstab shadows its logical ramdisk fstab. A host-qualified RAM-only
correction is ready for the operator build; see [ANDROID-FIRST-MOUNT.md](chainload/ANDROID-FIRST-MOUNT.md).
Full Android userspace and persistent menu installation remain unvalidated.**

## First build: display, input and countdown

From WSL, with the existing mmdebstrap and unshare tools:

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build
```

The script creates a separate Debian bookworm amd64 rootfs at
`/home/linuxagent/lmi-boot-menu-build/rootfs`. Bookworm provides Python 3.11
with distutils and Clang 14; the WSL host currently has Python 3.14 / Clang 21,
which are not a suitable assumed baseline for these older sources. Dependencies
are installed inside that rootfs, not into the existing Phosh or kernel builds.
Debian packages are not snapshot-pinned; record build.log and the final manifest.
Only Git source revisions are locked. No bit-for-bit reproducibility claim.

Source fetching and compilation occur only when the operator runs the command.
The build never invokes ADB/Fastboot or generates an installer ZIP. It uses a
private mount namespace with /dev including devpts; mounts disappear on exit.
The recipe is bound read-only. A failed bootstrap is preserved for inspection,
not automatically deleted. There is one source tree and one output directory.

Expected output:

```
/home/linuxagent/lmi-boot-menu-build/output/boot-lmi.img
/home/linuxagent/lmi-boot-menu-build/output/artifact-manifest.json
/home/linuxagent/lmi-boot-menu-build/output/build.log
```

After successful build, review the manifest and copy the image to Windows
Downloads. The first handset operation must be **temporary fastboot boot**, from
Windows, after product/hash verification. Do not flash this probe: its Mobian
entry cold-reboots the currently installed boot partition. Installing the probe
there would create a reboot loop. This folder intentionally has no flash helper.

The first menu offers:

- Mobian (restart installed OS), selected by default after 15 seconds.
- Fastboot.
- Lineage recovery.

This validates the UEFI display/input/countdown path and the reset handoff, not
Android chainloading. Android is not presented as a working choice. Touch or
selection may cancel the upstream automatic countdown; test the untouched case
separately. An unexpected black screen is a failed probe, not a reason to flash.

The probe bypasses on-disk SimpleInit config loading and persistence, installs
only explicit menu entries, and skips OS probing. Existing configs therefore
cannot override Mobian default via boot.current. It retains the upstream lmi BSP
unchanged, including its alioth ButtonsDxe/ACPI references; these are an explicit
hardware qualification concern, not evidence that alioth and lmi are identical.

## Why a direct two-image configuration is not ready

Both exact qualified OS boot images use Android header v2. The pinned SimpleInit
aboot reader consumes kernel/ramdisk/second only and does not handle the v2 DTB
field. Passing boot.img to it is not equivalent to ABL/Fastboot booting that
image. The wrapper version of the UEFI image is a separate issue: upstream lmi
uses header v1. Display, buttons, DTB/DTBO choice and downstream handoff all need
actual target validation. Kexec is absent from the current Mobian kernel.

`extract-payloads.py` validates both pinned original image hashes and strictly
extracts their kernel, ramdisk, DTB and complete command line. It changes no boot
image or target storage. Use a NEW private output directory:

```bash
python3 build/boot-menu/extract-payloads.py \
  --mobian /path/to/mobian-lmi-dualboot-boot-20261021.img \
  --android /path/to/boot.img --output /path/to/private-components
```

The next candidate should carry both sets of components in a RAM-backed FAT
asset volume exposed to UEFI, rather than rely on Android userdata decryption or
repartition again. This is a design to implement, not an installed mechanism.
Image padding need not be copied, but actual payload totals, FAT overhead,
UEFI wrapper size and allocation limits must be checked against the 128 MiB boot
partition before any persistence proposal. No DTB/DTBO index is guessed here.

## Qualification gates

1. Build success and pinned artifact identity.
2. Temporary boot: readable menu, working selection, untouched 15-second timeout,
   default return to Mobian, independent Fastboot/recovery rescue.
3. Implement RAM asset registration and explicit kernel/initrd/DTB handoff;
   preserve command lines, qualify Android DTBO selection and downstream reset.
4. Temporarily boot both OSes repeatedly, verify dedicated Mobian root and full
   Android access, hardware functionality and unchanged rescue access.
5. Only then prepare the persistent image, default policy and guarded installation.

The existing PC RAM-boot selector remains the working switching method meanwhile.
This recipe does not alter the installed boot, recovery, ABL, XBL or GPT.

## Source provenance

- [EDK2-MSM](https://github.com/edk2-porting/edk2-msm/tree/e1952621f419f8db60ed28271264e1b5184c571d),
  including configs/devices/lmi.conf, Platform/Xiaomi/sm8250/lmi.dsc,
  lmi.fdf.inc and Silicon/platform.sh.inc.
- [Pinned SimpleInit](https://github.com/BigfootACA/simple-init/tree/29e062805776db5ab7a61d07ef040d43aed71161),
  especially src/main/uefimain.c, src/gui/interface/core/bootmenu.c,
  src/lib/aboot.c, src/linux-boot/aboot.c and src/confd/uefi.c.

All direct submodules are recorded in sources.lock.json, fetched at gitlinks,
never updated with --remote. Proprietary upstream EFI binaries stay in the local
ignored external build directory; do not add them or generated images to Git.

## First operator build result

The October 21 operator build completed using Debian Clang 14.0.6 / Python
3.11.2. boot-lmi.img is 7059456 bytes, SHA256
f39e2c65a434a90ae3d8a11cfa2b40e6113f6eee27eb6e73bd5b54cdcbd713a1.
The image and source-patch manifest were independently re-read. The compact
firmware volume fits its 7 MiB region; linker RWX warnings did not abort the
build. This is build evidence, not proof that the target firmware runs.

The exact image was transferred to Windows Downloads as
`lmi-menu-smoke-20261021.img` and hash-verified. `test-menu-windows.py` defaults
to a host-only plan; `--execute` qualifies the existing dedicated Mobian endpoint
and installed RPMh boot prefix, reboots to Fastboot, checks lmi/partition size
and requests only a temporary boot. It contains no flash command. Run it from
Windows, not inside WSL. The observed installed RPMh boot remains unchanged;
return through its normal cold-boot path has not yet been observed after migration.

During the first probe, leave the screen untouched to evaluate the countdown.
Then report whether the menu appeared and whether Mobian returned. If the
screen remains black, do not keep retrying or flash the probe: return to
Fastboot and temporarily boot the already qualified dedicated Mobian image.

## First handset probe and revision 2 correction

The operator temporarily booted the first probe. The menu is visible. Touch
does not select/activate entries, but Volume changes focus and Power confirms;
the operator returned to Mobian by selecting its entry and Boot. SSH confirms
the dedicated root, running Phosh and charging after that normal boot. This
also qualifies the old installed RPMh boot's discovery of the new root layout.

The automatic path failed: source review identifies that bootmenu_add explicitly
excludes BOOT_REBOOT from auto-selection. The probe uses BOOT_REBOOT for Mobian,
so no default selection exists and bootmenu_load never starts the timer. This
was an integration error in revision 1, not an observation of a failed RTC or a
failed reboot handler. The physical button path proves the latter can run.

Revision 2 permits default auto-selection for the named Mobian reboot entry
only. Fastboot/recovery are still excluded from automatic selection. It also
enumerates Mobian, Fastboot, Recovery explicitly, independent of confd child
order. Exact before/after source hashes and patch-idempotence checks pass. The
seven boot-component parser tests still pass. Revision 2 has NOT been compiled
or handset-tested yet; rerun the same operator build command. The existing
Windows launch helper remains pinned to revision 1 until a new artifact hash is
reviewed and transferred. Do not use it to launch a rebuilt image with a new
hash. Touch support and Android chainloading remain separate pending work.

## Revision 2 compiled, handset verification pending

The operator completed the corrected build. The image is 7063552 bytes, SHA256
10f69a7693038b01244a8095c68240554e5717684218c87574ba8c36f5520bcc.
All three patched source hashes match the lock, including bootmenu.c. Windows
transfer was verified as lmi-menu-smoke-v2-20261021.img. The Windows test helper
now pins this revision and keeps its result separate from revision 1.
Untouched countdown and explicit menu order remain pending handset verification.
The final requested order is Mobian, LineageOS, Fastboot, Recovery. This probe
still contains only Mobian, Fastboot, Recovery: LineageOS chainloading is pending,
not hidden or qualified by this build. Touch input is not yet operational.

## Next candidate: LineageOS

Revision 2 automatic return after 15 seconds is operator-confirmed and backed
by SSH dedicated-root checks. See [LineageOS candidate](chainload/README.md) for
the next explicit build command, implementation and pending hardware gates.
