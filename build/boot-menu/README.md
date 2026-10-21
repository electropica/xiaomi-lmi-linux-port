# lmi handset boot-menu candidate

Dedicated recipe for the requested on-phone Android/Mobian menu: Mobian by
default after 15 seconds, without a PC once qualified and installed.

**Current deliverable: operator-buildable temporary menu probe. It is not yet
a persistent dual-OS boot manager. No firmware has been built or tested here.**

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
