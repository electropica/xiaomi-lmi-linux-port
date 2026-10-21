# Compact Android-only candidate after the pre-menu failure

## Current: compact candidate also failed; PrePi FFS3 correction ready

The compact image a6b4e95476d8161ea89034915029d3fbc536e4f278ecb753e274ba800befe267
also stayed black before any menu. The operator recovered installed Mobian by
holding Power. Its launcher is retired and refuses execution before phone contact.
No experimental image was flashed. Neither failure tested the Android handoff.

The compiled FD contains a 25024772-byte firmware-volume file using the PI
EFI_FFS_FILE_HEADER2 format (32-byte header, LARGE_FILE attribute, Size[3] zero).
The pinned EmbeddedPkg PrePi reader only handles 24-byte file headers: it computes
checksum 165 instead of zero, ignores ExtendedSize and starts the body eight bytes
too early. This is a reproducible startup defect before DXE or the menu; it does
not establish that no later startup defect remains.

patch-prepi.py adds bounded large-file traversal, complete-header checksums and
correct section/file-info offsets against an exact upstream SHA256. Existing
SECTION2 support is retained. The source manifest now restores Common/edk2 edits
as well as the superproject and SimpleInit; unfamiliar changes stop restoration
before any file is changed.

Host validation: the actual old C reader rejects the compiled compact FD; the
patched reader finds its large file and correct content boundary. Ordinary files,
truncated/overflowing/invalid sizes, eleven-file exact restoration and tamper
rejection pass. Clang 14 ARM64 syntax checking of the full patched FwVol.c passes
with the existing generated compiler flags and -Werror. See
prepi-host-replay-20261021.json and test-prepi.py. No new firmware build or phone
test has been run for this correction. Use the operator build command below;
wait for a newly verified artifact and launcher before any temporary boot.

The first complete candidate, SHA256
2d4284b5fc26fb8e90c529eb714e5d9076b8b01331bc707d00758dd94335ef11,
stayed black **before the menu appeared**. ADB, Fastboot and SSH were absent.
A long Power press returned to unchanged installed Mobian; SSH confirmed root
loop0p2, running Phosh and normal battery status. No pstore record was present.
The LineageOS entry had not been selected or executed. Its Windows helper is
retired and refuses --execute before contacting the phone.

That candidate embedded both OSes, expanded FD to 128 MiB and changed the memory
map. The exact failure location within startup remains unproven. The compact
candidate removes unused Mobian assets and leaves the working upstream lmi map
byte-for-byte unchanged. Five Android components total **61906944 bytes**.
FD is limited to the original 32 MiB reservation, 0xCE000000..0xD0000000; FDF
block count/region and BootShim size agree. A volume that does not fit must stop
the build, not silently enlarge the reservation. This is a controlled reduction,
not a proven fix yet.

## Operator command

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build --with-lineage
```

The same isolated environment and source cache are reused. Exact old patches
are restored before compact changes are applied; unfamiliar edits stop the
operation. No rootfs/kernel build, partition write or phone contact occurs.
Expected marker: LINEAGE_RAM_HANDOFF_BUILD_COMPLETE_NOT_FOR_FLASHING.

The private inputs are already staged under the external build directory:

- android.img: SHA256
  9d7dd4823860f7ad73c82542669620b2cee1ca466789958175be63bb77e85411.
- android-dtbo.img: full installed 32 MiB partition SHA256
  45f0989700c68afcd817a6a4569ba67225cf128e3eedd35a658bad384632eec4.

The builder no longer requires or bundles Mobian's boot components. Output is
output/boot-lmi-lineage-test.img and output/lineage-artifact-manifest.json. The
manifest identifies android-only-original-memory-map-32MiB-FD-prepi-ffs3. A fresh Windows
transfer/helper is needed after verifying the new artifact; do not reuse the
retired helper or flash any experimental candidate.

## Unchanged handoff and remaining gates

The exact pinned Android kernel, initrd, DTB, command line and installed DTBO are
carried in a bounded, CRC-checked FV section. DTBO has 12 overlays, 5514578
meaningful bytes; only padding is trimmed, and no overlay index is guessed.
GetSectionFromAnyFv returns protected allocated memory. Qualcomm hardware-info
matching and the non-EFI ARM64 handoff remain experimental until actual Android
startup is observed. Overlay errors remain fatal.

Menu order is Mobian, LineageOS, Fastboot, Recovery. Mobian still cold-reboots
the existing installed Mobian boot and is the 15-second default. This is not a
persistent menu: flashing it into boot would loop. Direct Mobian chainloading
and persistent installation remain later steps. Volume/Power work in the small
validated probe; touch does not.

Compact actual-input bundle creation, C parser malformed-input/bounds tests,
source patch/restoration, unchanged-map checks and shell syntax pass on the host.
The EFI adapter previously passed targeted Clang 14 ARM64 syntax checking with
the generated flags and -Werror. The larger predecessor compiled and failed
before the menu. The first compact firmware also failed before the menu; the
FFS3-corrected version remains pending compilation and handset validation.

## FFS3-corrected candidate compiled; temporary handset test pending

The operator build completed. Image: 25993216 bytes, SHA256
eea24170b1d63bb4028b94c66437db9a1add3a4b67a5616e88ca15b1547b2f6e.
All eleven source hashes match the manifest, including corrected PrePi; the lmi
memory map is unchanged. Old/patched C replay against the newly built FD again
reproduces the old rejection and corrected traversal/content boundary. Windows
image transfer and plan-only launcher preflight passed. The new launcher is
test-lineage-ffs3-windows.py; both earlier experimental launchers remain retired.
Handset menu display, Android handoff and persistent installation are not yet
validated. No phone command or flash was performed during these checks.

## Menu confirmed; LineageOS selection returns to UEFI setup

The operator explicitly confirmed the FFS3-corrected menu appears. Selecting
LineageOS then displays EDK2 setup (Device Manager / Boot Manager / Boot
Maintenance Manager), not Android. Installed Mobian has been restarted and
remains usable. No experimental firmware was flashed. Kernel execution is not
demonstrated and the exact returned error is not yet known.

A diagnostic-only recipe update records the last attempted launch stage and
shows the latest six warnings/errors from RAM for up to 120 seconds on a
returned failure. All three C units pass Clang 14 ARM64 -Werror syntax checks;
thirteen-file exact restoration and tamper rejection pass. No diagnostic build
or handset test has yet occurred. See chainload/HANDOFF-DIAGNOSTIC.md under
build/boot-menu. Next operator build uses the same --build --with-lineage command;
the manifest variant ends in prepi-ffs3-diag1. This is instrumentation, not a
claimed Android boot fix. No flash, kernel rebuild or partition change required.
