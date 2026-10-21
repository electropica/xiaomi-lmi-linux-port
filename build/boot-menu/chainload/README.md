# Experimental LineageOS entry after the validated menu probe

**Current status: Android kernel/init execution is confirmed. fstab1 reaches
recovery with init_user0_failed; the exact data-initialization error is unknown.
A no-flash direct stock-Android control is prepared; see
[ANDROID-DATA-CONTROL.md](ANDROID-DATA-CONTROL.md). Full Android startup and
persistent menu installation remain unvalidated.**

Revision 2's untouched 15-second default and return to Mobian are now confirmed
by the operator; SSH confirms root /dev/loop0p2 and running Phosh after return.
Volume/Power navigation works. Touch does not select/activate entries yet.

This next candidate adds **LineageOS in second position**. It is a host-tested
implementation, not a firmware build or a successful Android handoff yet.
It remains temporary-only: the Mobian default entry cold-reboots the existing
Mobian boot. Do not install it into boot, which would loop back into the menu.

## Operator build

The per-device private inputs have already been hash-qualified and staged under
`/home/linuxagent/lmi-boot-menu-build/inputs`. For this handset only, run in WSL:

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build --with-lineage
```

This reuses the existing isolated Bookworm environment. No rootfs/kernel/Android
build, GPT write, phone connection or flash is performed by the recipe. It does
relink/repack the experimental UEFI image. Expected final marker:
`LINEAGE_RAM_HANDOFF_BUILD_COMPLETE_NOT_FOR_FLASHING`.

Output is `output/boot-lmi-lineage-test.img` and
`output/lineage-artifact-manifest.json` under the external build directory.
Do not reuse the old Windows helper: it deliberately pins revision 2 until the
new image has been inspected and transferred.

For another device/reproduction, inputs must be supplied explicitly as
`android.img`, `mobian.img`, `android-dtbo.img`, with the exact hashes below.
These are private local inputs; neither images nor proprietary EFI binaries
belong in this Git repository.

## Loading and memory design

Both pinned images use Android boot header v2. The offline extractor takes the
exact kernel, initrd, DTB and complete command line from each image. It does not
feed these images to the older SimpleInit parser that omits the v2 DTB field.
An additional read-only copy of this handset's installed Android DTBO partition
was captured and hash-verified. Its table has 12 overlays and 5514578 meaningful
bytes; all entries are bounds-checked. Only trailing partition padding is
excluded. Header, overlay contents and IDs are unchanged. No index is guessed.

The combined bounded asset bundle is **116559872 bytes**. Components carry
offsets, lengths, CRC32 and a host SHA256 manifest. The firmware checks table
bounds, non-overlap, unique names and selected-component CRCs before loading.
The whole future boot image must still fit the 128 MiB boot partition.

The bundle is embedded as a RAW section in a firmware volume and retrieved via
EDK2's GetSectionFromAnyFv. The initial ramdisk approach was rejected before
building or booting it because the upstream fixed memory map does not reserve
an arbitrary ABL ramdisk against DXE allocation.

To protect the expanded firmware, the experimental FD size is 128 MiB at
0xCE000000. Its reserved map ends at 0xD6000000; the following conventional RAM
starts there and keeps its original upper endpoint. FDF block count, FDF region,
BootShim size and lmi memory descriptor are changed together. These are host
invariants, not proof that the expanded firmware starts on the device.

Only the LineageOS entry uses the new loader in this candidate. The config uses
FROM_POINTER for the verified kernel, initrd, DTB and DTBO and invokes the
existing non-EFI ARM64 handoff. The pinned image command line is preserved;
ABL's dynamic FDT command line/memory information is also retained. Qualcomm
DTB/DTBO matching uses upstream hardware-info protocols, and overlay failures
remain fatal. Protocol availability, correct overlay choice, downstream kernel
entry and Android startup all require target validation. Mobian's components
are included for the later direct Mobian path but are not used by its current
cold-reboot entry.

No on-disk config loading/persistence or OS scanning is introduced. The recipe
restores only its exact known source changes on subsequent runs; any unfamiliar
edit stops restoration before changes are made. Host source checks use a
temporary fixture and leave the actual upstream checkout unmodified.

## Inputs and validation boundary

- Android boot SHA256:
  9d7dd4823860f7ad73c82542669620b2cee1ca466789958175be63bb77e85411.
- Adapted Mobian boot SHA256:
  75bb65facbd4146d4a1e668039ef52433ef90c2b6bdb07f2c59980caf3191374.
- Full installed 32 MiB DTBO partition SHA256:
  45f0989700c68afcd817a6a4569ba67225cf128e3eedd35a658bad384632eec4.

Actual-input bundle construction, C parser bounds tests (including malformed
and overlapping rows), source patch/restoration and map endpoint checks pass on
the host. Shell syntax checks and the seven original image-parser tests pass.
The EFI adapter has not yet been compiled; no claim of a bootable LineageOS
entry is made until operator compilation and actual Android startup succeed.

After a successful build, first temporarily boot from Windows, verify the menu
still times out into Mobian, then repeat and choose LineageOS using Volume and
Power. Inspect Android boot completion and ADB before claiming success. The
existing Fastboot path and qualified direct images remain the rescue method.
