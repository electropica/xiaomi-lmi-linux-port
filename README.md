# Xiaomi lmi / P1 reconstruction

This repository records evidence and reproducible procedures for the Xiaomi
`lmi` P1 reconstruction effort. It deliberately contains no APK, boot image,
root filesystem image, private signing key, password, or phone-derived secret.

## Current status — 2026-09-23

The D-v43 configuration has been reconstructed as **Shelli + OpenRC** from
historical evidence and pinned local inputs. The installation completed and
the resulting root filesystem passed static checks. The reconstructed userdata
and boot images were then tested on the phone: OpenRC reached the full system,
USB networking returned, and SSH login as `lmi` succeeded. A subsequent manual
`lmi-wifi-start` run brought the QCA6390 to CNSS `ONLINE` with zero crashes,
created `wlan0`, `p2p0`, and `wifi-aware0`, and completed a radio scan that
found six BSS entries.

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
- [Evidence and source inventory](SOURCES.md)
- [Reference checksums](SHA256SUMS)
- [Consolidated reconstruction/verification script](scripts/reconstruct-dv43-openrc.sh)

Hardware validation now covers the complete OpenRC userspace, USB networking,
SSH access, QCA6390 initialization, and Wi-Fi scanning. Wi-Fi still requires a
manual trigger in this test; association, Wi-Fi DHCP, and Internet access were
not tested. The display remains black, and boot still pauses in
`pmos.debug-shell` until `pmos_continue_boot` is run manually.
