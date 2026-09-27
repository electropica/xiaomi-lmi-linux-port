# Xiaomi lmi / P1 reconstruction

This repository records evidence and reproducible procedures for the Xiaomi
`lmi` P1 reconstruction effort. It deliberately contains no APK, boot image,
root filesystem image, private signing key, password, or phone-derived secret.

## Current status — 2026-09-27

The `archi-validation-02` Debian 13/Mobian userdata has now been booted on the
Xiaomi `lmi` with the validated D-repro D-v43 RAM boot. Phosh is visible and
usable. The live renderer journal confirms GLES2 through Zink, Vulkan Turnip,
KGSL and the Adreno 650 with OpenGL ES 3.2 Mesa 25.0.7. GNOME Console and
Calculator were exercised successfully. Chatty remains open but emits repeated
GStreamer diagnostics; that application issue does not invalidate the display
or GPU result.

The text-only reproduction lock is tracked under
[`reproduction/archi-validation-02-lock/`](reproduction/archi-validation-02-lock/README.md).
It records 1,086 exact packages, 65 persistent customizations, the GPU72
payload identities and the D-repro boot/userspace contract. The userdata can
be cloned exactly from the existing sparse image or used as the basis of a
functionally equivalent userspace without rebuilding the kernel. A bit-for-bit
source rebuild is not yet demonstrated.

The complete 1,086-package `.deb` cache is preserved through text-only
provenance manifests under
[`reproduction/archi-validation-02-lock/deb-cache/`](reproduction/archi-validation-02-lock/deb-cache/README.md).
The validated cache and its deterministic tar archive remain external to Git.

## D-v43 OpenRC status — 2026-09-26

The D-v43 configuration has been reconstructed as **Shelli + OpenRC** from
historical evidence and pinned local inputs. The installation completed and
the resulting root filesystem passed static checks. The reconstructed userdata
and boot images were then tested on the phone: OpenRC reached the full system,
USB networking returned, and SSH login as `lmi` succeeded. A subsequent manual
`lmi-wifi-start` run brought the QCA6390 to CNSS `ONLINE` with zero crashes,
created `wlan0`, `p2p0`, and `wifi-aware0`, and completed a radio scan that
found six BSS entries.

A follow-up boot image removes `pmos.debug-shell` from the kernel command line.
It was launched non-persistently with `fastboot boot` and reached OpenRC, USB
networking, and SSH without Telnet or `pmos_continue_boot`. The image was not
installed permanently.

The downstream DRM/KMS display path has now also been exercised directly.
`DSI-1` was connected with preferred mode `1080x2400`, and a guarded
`modetest` modeset produced several visible colored rectangles. This validates
the CRTC, scanout, DSI link, panel, and backlight. It does not validate
GPU/EGL acceleration, Weston, Phosh, or touch input.

This is a **functional, evidence-based reconstruction of the D-v43 OpenRC
configuration**, not a bit-for-bit reproduction. The original June 2026
device `r104` APK, boot image, and userdata image are no longer locally
available; Alpine/postmarketOS dependencies came from `edge` as it existed on
2026-09-23.

The previous systemd/PID1/statx investigation remains valid for the hybrid
rootfs it diagnosed, but that rootfs used `postmarketos-base-systemd` and
systemd `262_rc3` on downstream Linux `4.19.325`. It did **not** reproduce the
historical D-v43 system, which used OpenRC.

See:

- [D-v43 OpenRC reconstruction milestone](docs/2026-09-23-d-v43-openrc-reconstruction.md)
- [DRM/KMS display validation and compositor analysis](docs/2026-09-25-drm-display-validation.md)
- [D-v43 display milestone and Weston 14 boundary](docs/2026-09-26-d-v43-display-milestone.md)
- [Historical M1/GPU72 hardware validation](docs/2026-09-26-m1-gpu72-historical-validation.md)
- [Validated archi-validation-02 userspace lock](docs/2026-09-27-archi-validation-02-userspace-lock.md)
- [Versioned userspace reproduction lock](reproduction/archi-validation-02-lock/README.md)
- [Evidence and source inventory](SOURCES.md)
- [Reference checksums](SHA256SUMS)
- [Consolidated reconstruction/verification script](scripts/reconstruct-dv43-openrc.sh)
- [Reversible no-debug-shell boot builder](scripts/build-openrc-no-debug-shell-boot.sh)
- [One-shot DSI modeset test](scripts/test-dsi-modetest.sh)

Hardware validation now covers the complete OpenRC userspace, USB networking,
SSH access, autonomous continuation past initramfs, QCA6390 initialization,
and Wi-Fi scanning. The Wi-Fi result belongs to the preceding boot and was not
retested with the exact no-debug-shell image; it required a manual trigger.
Association, Wi-Fi DHCP, and Internet access remain untested. The display
hardware works, but the normal system remains black because Shelli provides a
plain console and no persistent DRM/KMS client performs a modeset. Weston 16
did not reach a modeset in temporary tests. Graphical userspace integration
and the earlier `powerkey` crash remain unresolved.

The 2026-09-26 milestone records a successful Alpine/musl Weston 14
reconstruction and a legacy test path. Weston 14 reached both its normal
atomic failure and a forced CRTC-129 legacy path, but both remained black;
DSI-1 became enabled while `actual_brightness` stayed at zero. Weston work is
intentionally suspended while OS and application work continues on the older
functional build.
