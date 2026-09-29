# D-repro D-v43 boot/userspace compatibility contract

## Locked boot identity

The validated RAM boot is the 52,924,416-byte image whose SHA-256 is
`0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad`.
The running system reported:

```text
Linux PocoF2Pro 4.19.325-cip128-st12-perf-ga5b3099017ae-dirty
#2 SMP PREEMPT Sat Sep 5 20:22:53 UTC 2026 aarch64
```

This lock does not rebuild or replace that kernel.

## Filesystem identity and cmdline

The compatible filesystem identities are:

- `pmOS_boot`: `7bd723c2-51d6-4015-b28b-2b38191bf765`
- `pmOS_root`: `dba94dfe-0fb9-4f95-970e-22949f4e69dc`

The required cmdline contract includes at least:

```text
loop.max_part=7
pmos_boot_uuid=7bd723c2-51d6-4015-b28b-2b38191bf765
pmos_root_uuid=dba94dfe-0fb9-4f95-970e-22949f4e69dc
pmos_rootfsopts=defaults
androidboot.usbcontroller=a600000.dwc3
msm_drm.dsi_display0=qcom,mdss_dsi_j11_38_08_0a_fhd_cmd:
```

The validated boot does not depend on `pmos.debug-shell`.

The initramfs must expose the flashed userdata as a loop device, discover its
boot and root partitions by these UUIDs, mount the ext4 root, mount the boot
partition at `/boot`, preserve USB networking, and switch root into systemd.

## Interfaces supplied by the boot/kernel

Userspace requires the boot/kernel/device-tree combination to expose:

- downstream `msm_drm`, `/dev/dri/card0`, `/dev/dri/renderD128`, DSI-1 and
  mode `1080x2400x60x184345cmd`;
- `/dev/kgsl-3d0` for Turnip/KGSL and `/dev/ion` for the cross-device path;
- Qualcomm firmware loading for the A650 payload under
  `/lib/firmware/postmarketos`;
- QRTR, remoteproc/PIL and CNSS interfaces used by QCA6390;
- the Android/vendor mounts used by the Wi-Fi firmware preparation scripts;
- the USB gadget controller and `usb0` retained across switch_root;
- ADSP/PD-mapper interfaces used by the installed BTFM services.

Runtime confirmation established DRM, KGSL, ION, USB and CNSS (`ONLINE`, zero
crashes). ADSP-related services were active, but `/proc/asound/cards` contained
no sound card; functional audio is therefore not part of this contract.

## Responsibilities

The boot supplies kernel, device tree, initramfs, downstream hardware drivers,
cmdline and early userdata discovery. The userdata supplies Debian/systemd,
device permissions, firmware, splash release, seatd, Phoc/Phosh, GPU72,
NetworkManager, Wi-Fi helpers and applications.

An arbitrary boot is incompatible unless it preserves all UUID handling,
device nodes, ioctls, downstream DRM/KGSL/ION behavior, firmware search paths,
USB continuity and Qualcomm subsystem interfaces above. A matching kernel
version string alone is insufficient.

`/boot/boot.img` inside the userdata has SHA-256
`1fbfe7cbfd6d8a7faf444409291abb665f7458a36b21cdc3d4438302c66e7e99`.
It is an embedded artifact and is not the active D-repro RAM boot. Recipes and
reports must never substitute its identity for the validated boot SHA.
