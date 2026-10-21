# Compact Android-only candidate after the pre-menu failure

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
manifest identifies android-only-original-memory-map-32MiB-FD. A fresh Windows
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
before the menu. The compact firmware is not yet compiled or target-tested.

## Compact candidate compiled; temporary handset test pending

The compact build completed: 25993216 bytes, SHA256
a6b4e95476d8161ea89034915029d3fbc536e4f278ecb753e274ba800befe267.
The compressed volume uses 25070792 of 33554432 bytes. All ten modified-source
hashes match the manifest, and the upstream lmi memory map is independently
byte-identical. Windows transfer and host-only launcher preflight passed.
The new test-lineage-compact-windows.py pins this specific image; the older
failed candidate's launcher remains disabled. No compact handset boot has yet
occurred and no persistent boot change is made.
