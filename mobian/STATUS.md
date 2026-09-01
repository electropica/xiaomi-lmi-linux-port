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

## M0 DISPLAY — offline validated

Prepared and validated offline:

- KMS continuous-splash release with Debian `modetest`
- systemd orchestration
- seatd with `SEATD_VTBOUND=0`
- Weston 14.0.2
- Pixman renderer
- kiosk shell
- `DSI-1`
- `Virtual-1` disabled
- red background validation target

The DISPLAY ext4/raw/sparse images were built and sparse round-trip validated
bit-for-bit.

Hardware display validation is still pending.

## Repository policy

Generated `.img`, `.ext4`, Android sparse images, root filesystems, private
keys, caches and other build artifacts are intentionally excluded from Git.
