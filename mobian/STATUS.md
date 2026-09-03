# Mobian M0 status

## M0 BASE — validated on hardware

Validated on Xiaomi `lmi` hardware with the downstream D-v43 kernel.

Confirmed:

- Debian GNU/Linux 13 (trixie)
- systemd as PID 1
- root filesystem on `/dev/loop0p2`
- USB RNDIS preserved across switch_root
- `usb0` configured as `172.16.42.1/16`
- SSH root login by public key
- kernel `4.19.325-cip128-st12-perf`

The M0 BASE image is intentionally not stored in Git.

## M0 DISPLAY — VALIDATED ON HARDWARE

Validated on Xiaomi `lmi` hardware:

- KMS continuous-splash release with Debian `modetest` works
- seatd with `SEATD_VTBOUND=0` works
- Weston 14.0.2 DRM/Pixman with kiosk shell works
- `DSI-1` drives the physical panel
- a red background is physically visible
- downstream `msm_drm` requires the tracked Weston workaround that
  de-duplicates indistinguishable formats in the legacy no-`IN_FORMATS`
  fallback

See `notes/mobian-m0-display-hardware-validation-2026-09-02.md` for the exact
experimental evidence and backend identities.

## M1 PHOSH — VALIDATED ON HARDWARE

The M1 graphical session and basic Phosh interaction were validated on Xiaomi
`lmi` hardware. The clear-KMS marker was visible, Phoc acquired `DSI-1` with
the Pixman renderer, and the Phosh lock screen appeared. Touch input and the
swipe-up gesture worked, the passcode prompt allowed the session to be
unlocked, and the Phosh desktop was then displayed with its applications and
icons.

This milestone validates the graphical bring-up and basic Phosh interaction.
It does not validate GPU acceleration, every Phosh function, or readiness for
daily use.

## M1 WIFI — VALIDATED ON HARDWARE

Manual bring-up on `lmi` with D-v43 completed the QCA6390 CNSS/WLFW sequence,
created `wlp1s0`, scanned nearby BSS entries, associated with WPA2, obtained a
DHCP lease and default route, and preserved the independent `usb0` SSH path.
The kernel dynamically selected `bd_j11gl.elf`; it must not be overridden with
the older historical `bd_j11.elf` default.

The systemd implementation of the validated ordering is now tracked under
`mobian/m1-phosh/wifi`, but remains **not yet hardware-validated**. See
`notes/mobian-m1-wifi-hardware-validation-2026-09-03.md`.

## Repository policy

Generated `.img`, `.ext4`, Android sparse images, root filesystems, private
keys, caches and other build artifacts are intentionally excluded from Git.
