# Direct Mobian with an external input ramdisk — candidate only

Status: preparation and host/ARM64 syntax checks pass. No firmware build or
handset validation has been performed for this candidate. Never flash it until
direct Mobian provenance and all menu outcomes are confirmed by temporary boot.

## Why a new candidate is necessary

The resetguard1 historical 32-MiB firmware starts LineageOS and successfully
selects Fastboot/Recovery; its Mobian entry restarts the installed boot partition.
That entry cannot provide permanent installation over the same boot partition.
The newer 64-MiB dual-direct firmware failed its LineageOS handoff. The firmware
size change is a suspected factor, not a proven cause.

This candidate keeps the historical Android asset volume and 32-MiB FD layout.
It supplies only Mobian components through the Android boot container's outer
ramdisk. No OS components are read from filesystem paths or new partitions,
and no partition layout is changed. Exact image hashes remain pinned.

## Implementation

- Export baseline `78e8328dfb09bbbce109bd0a4accf8561d44af94` to a content-addressed
  recipe directory. Keep the tested reset-service preservation wrapper.
- Extract kernel, initrd, DTB and command line from the locked adapted Mobian
  boot image into a bounded five-entry bundle. The fifth entry identifies the
  format. Embed its exact byte length and whole-bundle CRC32 in the loader;
  each component also retains the existing CRC checks. CRC guards accidental
  damage, not malicious firmware replacement; the final image needs SHA256
  verification in the manual launcher.
- Read `/chosen/linux,initrd-start` and `linux,initrd-end` as big-endian 32- or
  64-bit cells. Reject empty, reversed, overflowing or over-64-MiB ranges.
  Do not reuse the pinned `fdt_get_initrd`: it reads cells in native byte order
  and rejects `start <= end`, so it cannot provide the needed valid-range check.
- Before DXE allocations, reserve the page-aligned range only if it lies wholly
  within one conventional platform descriptor, outside early UEFI memory and
  the original FD. Split its HOBs into conventional prefix, reserved middle and
  conventional suffix. Preserve the original MMU map and 32-MiB FD descriptor.
  An absent/invalid/unprotectable range does not change the map; the Mobian loader
  then refuses it. The Android entry retains its existing FV loader.
- Before reading payload bytes, the Mobian loader checks the runtime memory map
  still covers the whole range as reserved. It checks exact size and CRC, then
  uses the existing bounded component loader and copies selected OS data into
  its normal kernel/initrd/DT buffers.
- Switch only Mobian to `BOOT_LINUX`; skip Android fstab surgery for Mobian.
  Reserve the complete ARM64 Image runtime extent for Mobian only. Keep the
  existing Android path. Append `lmi_menu=outer-v1` to Mobian's command line
  so a reset to the installed Mobian boot cannot be mistaken for direct handoff.
- Repackage the menu's v1 boot image with the Mobian bundle as its outer ramdisk.
  Preserve the kernel bytes and boot-header OS version; update ramdisk size and
  the standard boot-id SHA1. Both 2048- and 4096-byte pages are supported.

The pinned Mobian bundle is 54,657,037 bytes. Packing it with the existing
resetguard1 reference in memory gives an 80,654,336-byte container, below the
134,217,728-byte boot-partition limit. This is a container test, not a new
firmware image or proof that ABL will place the incoming ramdisk as required.

## Checks completed

- Actual shared C range parser: endian/width/alignment/containment/overflow.
- Actual early reservation helper: contiguous non-overlapping HOBs, reserved
  memory type, and rejection of malformed or protected input.
- Actual loader range/source functions: reservation proof before payload CRC,
  and refusal of unreserved, malformed or CRC-mismatched inputs.
- Actual 12-file overlay: exact restoration, and refusal to restore any files
  after an unreviewed source edit.
- v1 container: kernel preservation, ramdisk replacement, boot-id digest,
  both page sizes and truncated-input rejection; real locked input size test.
- Five actual ARM64 units pass syntax with the existing generated build flags:
  menu main, boot dispatch, component loader, Linux preparation and memory PEI.
- Snapshot shell files pass `bash -n`. No active cache source was modified
  during these checks; ARM64 checks used transient read-only mount overlays.

## Operator build

```sh
sudo python3 -B /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/external-mobian/build-external.py --build
```

This builds only the menu firmware using the existing isolated cache. It does
not rebuild Linux or Mobian, contact the phone, flash, or install anything.
Expected final marker:

```text
OUTER_MOBIAN_MENU_BUILD_COMPLETE_NOT_FOR_FLASHING
```

Output: `/home/linuxagent/lmi-boot-menu-build/output/boot-lmi-outer-mobian-test.img`,
with `outer-mobian-artifact-manifest.json` recording component, overlay and reset
guard provenance. The historical source manifest describes the baseline;
`outer-source-manifest.json` supersedes entries changed by this overlay.
The next invocation restores the qualified overlay before restoring the baseline.
Unexpected edits stop restoration. Interrupted builds require inspection.

## Required handset validation

1. Qualify actual source hashes, FD size and BootShim/FD payload, outer ramdisk
   bytes/CRC/SHA256, boot header and final size before transfer.
2. Temporary boot only; let the 15-second default choose Mobian.
3. Confirm `lmi_menu=outer-v1` in the running kernel command line, the dedicated
   Mobian root, and working interface. An ordinary return to Mobian is insufficient.
4. Re-test LineageOS, Fastboot and Recovery on this exact image.
5. Only then prepare a permanent installation and recovery command for the
   verified artifact. Until then retain the existing boot partition.

Font/rendering changes and battery-policy changes are outside this comparison.
