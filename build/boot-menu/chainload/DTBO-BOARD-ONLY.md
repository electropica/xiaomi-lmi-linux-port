# Board-only Qualcomm DTBO matching

## Observed error

The diagnostic handset boot (image SHA256
287645d2b55060b15006037c6fa3a91180954af85cf4286ded2daae14b9803f0)
shows stage `08 apply DTBO`, with `selected dtbo 7 (Qualcomm Technologies,
Inc. xiaomi lmi) vote too few`, followed by `apply dtbo failed` and
`prepare linux boot failed`. The operator subsequently sees UEFI setup again.
The bundle loaded, kernel decompression and base DTB selection returned success;
kernel execution has not occurred. The RNG warning is nonfatal in the pinned
random-seed installer, and the icon warnings do not identify this failure.

## Reproduced source defect

All twelve overlays in the pinned Android DTBO image have qcom,board-id but no
qcom,msm-id. The lmi overlay has board-id (37, 0). They are board overlays for
a base SoC DTB; missing SoC metadata does not encode an actual SoC ID of zero.
See dtbo-root-properties-20261021.json (metadata only, no firmware).

process_dtbo zero-initializes its info, then qcom_parse_id leaves soc_id zero
when msm-id is absent. qcom_check_dtb compares that zero to the platform's
nonzero SoC ID and returns a negative vote, including for the correct board.

patch-dtbo.py changes only automatic overlay matching: an absent msm-id
property with the specific NOTFOUND result and a well-formed board-id can
inherit the platform SoC ID/revision/foundry already used for base-DTB selection.
Board fields remain untouched and must still pass the original matching logic.
Explicit or malformed msm-id properties are not overwritten. No DTBO index,
model string or permissive ignore_dtbo_error setting is forced. Base DTB
matching and DTBO application logic are unchanged.

## Validation and remaining limits

The actual C voter and inserted inheritance block were replayed against all
twelve real board IDs with eight representative nonzero SoC/revision/foundry
profiles for board 37. Previously none passed; afterwards only lmi passes.
Explicit incompatible msm-id and malformed-property errors are not overridden.
These profiles are test fixtures, not measurements of the running firmware.
Four C units pass Clang 14 ARM64 syntax checking with generated flags/-Werror.
Fourteen-file patch/restoration and tamper rejection pass on a source fixture.

No dtbo1 firmware has yet been built or tested on the handset. A successful
host vote does not prove overlay application or Android kernel execution.
Keep the stage/error panel for the next possible failure. The build variant
ends in prepi-ffs3-dtbo1. Operator command remains:

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build --with-lineage
```

After compiling, qualify the new image/hash and use a new Windows RAM launcher.
Do not flash an experimental menu. If still in UEFI setup, a long Power reset
returns to installed Mobian as previously verified; no new image is required.

## Board-only DTBO correction compiled; handset test pending

The operator built dtbo1: 25997312 bytes, SHA256
969ee0c3d49083adfd17ea199575df55b211c66b5071d96fb24c8701fb82bed1.
Fourteen source hashes match, the lmi memory map is unchanged, and PrePi replay
passes on the rebuilt FD. Windows transfer and plan-only preflight passed.
test-lineage-dtbo-windows.py pins this image and now requires an explicit SSH
guard-completion marker before waiting for Fastboot; an absent USB link is no
longer mistaken for a possibly successful reboot. No phone command or flash was
performed in qualification. Actual DTBO application and Android handoff remain
pending; the diagnostic stage/error panel is retained.

## Android kernel and first-stage init confirmed; logical mount fix prepared

The dtbo1 test returned to Fastboot. Installed Mobian was recovered; private
archived console-ramoops shows the exact Lineage kernel running /init, then
a ten-second wait for physical system/vendor devices and InitFatalReboot with
bootloader target at about 12.3 seconds. This confirms Android kernel/first-stage
execution, not a completed Android boot. No experimental firmware was flashed.

All three pinned Android DTBs retain a physical ext4 vendor DT fstab; the pinned
ramdisk has the correct logical first-stage fstab, including erofs vendor.
Lineage prioritizes the DT table. The new Android-only stage-14 correction
removes that exact known legacy subtree in RAM, leaving the original ramdisk,
AVB policy, super metadata, GPT and installed boot unchanged. Unknown tables
are rejected. No command-line cleanup is included.

Actual C/libfdt tests on all three real DTBs plus the board-matched lmi overlay
pass, with every unrelated property unchanged. Wrong-OS and unexpected-path
guards, four-unit ARM64 syntax and fifteen-file exact restoration/tamper tests
pass. No fstab1 build or hardware test has yet occurred. See
build/boot-menu/chainload/ANDROID-FIRST-MOUNT.md. The operator command is unchanged;
new variant ends in prepi-ffs3-fstab1. Later Android startup issues may remain.
