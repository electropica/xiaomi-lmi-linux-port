# Mobian M1 REPRO v2 host image validation — 2026-09-04

## Status

**M1 IMAGE BUILT / HOST VALIDATION PASSED**

This section records the state before the phone test. The exact image was
subsequently tested; its results and required corrections are recorded in
`notes/mobian-m1-repro-v2-hardware-validation-2026-09-04.md`.

## Rejected intermediate

The first finalization attempt did not produce a valid ext4 filesystem. The
4 GiB zero-filled file reported only `data`, and its ext4 magic bytes at offset
1080 were `00 00`. It was rejected and must not be identified or distributed
as a usable image. No retained log proves a more specific cause than an
interrupted/manual finalization path; the tracked fail-fast recipe would stop
at `mkfs.ext4` or `e2fsck` before userdata conversion.

## Validated artifacts

The existing package installation was reused without rebuilding the rootfs.

```text
ext4: /home/linuxagent/pmos-d-repro-01/Mobian-M0/m1-repro-v2-build-r2/Mobian-M1-REPRO-pmOS_root.ext4
size: 4294967296
sha256: 4c48977bb25c4ef8ad85b56f97cf0f387aee67c4dbdf84518b875dd251e817ae
type: Linux ext4
label: pmOS_root
uuid: dba94dfe-0fb9-4f95-970e-22949f4e69dc
superblock magic: 53 ef
e2fsck -fn: PASS

raw: /home/linuxagent/pmos-d-repro-01/output/Mobian-M1-REPRO-v2-userdata-phosh-4G.img
size: 4551868416
sha256: 7f27d670df1859fbd4e92df347035b00070d4790abc8a5cc21ade00dcf8fc31b

Android sparse: /home/linuxagent/pmos-d-repro-01/output/Mobian-M1-REPRO-v2-userdata-phosh-4G.android-sparse.img
size: 1860927308
sha256: c2495b55daf77fdefff213cc64d37eab2101b52fea7d0ca0b96c43310b9af23a
```

The final stage completed ext4 creation and checking, GPT expansion, rootfs
injection, `img2simg`, `simg2img`, bit-for-bit raw round-trip comparison, and
the final filesystem check, ending with `M1_IMAGE_STAGE_PASS`.

Rootfs checks confirmed NetworkManager, qrtr-ns, seatd and Phosh enablement;
the pinned M1 packages including `qrtr-tools` and `unzip`; the AArch64 property
shim; Pixman/DRM Phoc configuration; Virtual-1 disablement; and preservation
of `usb0` outside NetworkManager. No proprietary cnss-daemon, Android APEX, or
QCA6390 firmware payload was embedded.
