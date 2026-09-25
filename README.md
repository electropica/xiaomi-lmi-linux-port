# Xiaomi lmi / P1 reconstruction

This repository records evidence and reproducible procedures for the Xiaomi
`lmi` P1 reconstruction effort. It deliberately contains no APK, boot image,
root filesystem image, private signing key, password, or phone-derived secret.

## Current status — 2026-09-25

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
