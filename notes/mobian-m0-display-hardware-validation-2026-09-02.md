# Mobian M0 DISPLAY hardware validation — 2026-09-02

Device: Xiaomi Redmi K30 Pro / POCO F2 Pro (`lmi`).

## Established baseline

M0 BASE boots Debian 13 with systemd as PID 1. The RNDIS gadget and `usb0`
survive `switch_root`; `172.16.42.1/16` and root SSH authentication by public
key work. `/dev/dri/card0` exists and `DSI-1` reports `connected`.

## Systemd device-unit correction

`dev-dri-card0.device` remained inactive and timed out even though the device
node existed. Removing its `Requires=` and `After=` references from
`lmi-splash-release.service`, while retaining `After=systemd-udevd.service`,
allowed the known KMS splash release to complete and `seatd.service` to start.

## Weston failure and correction

Debian Weston 14.0.2 opened `/dev/dri/card0` through libseat/seatd, detected
atomic modesetting support, selected the Pixman renderer, and then reproducibly
terminated with SIGABRT in `weston_drm_format_array_add_format()`.
`modetest` showed duplicate fourcc values exposed by downstream `msm_drm`.

The source correction de-duplicates formats only in the legacy fallback of
`drm_plane_populate_formats()` used when no `IN_FORMATS` blob exists. It does
not alter modifier-aware format handling.

An AArch64 backend built with this patch was linked against
`libdisplay-info.so.2` and required at most `GLIBC_2.38`. Its SHA-256 was:

```text
546664f37bbc85475a089f4e6cc3aa1f9478093c2e2addd95cc225a37e848fd3
```

The original Debian backend observed on the phone had SHA-256:

```text
8618f07a6ca560641b8ccab5022c4db6b8e01e4d5d6b353f69ec69d930110709
```

For the experiment, the patched backend was transferred as
`/root/drm-backend-m0-patched.so` and bind-mounted temporarily over
`/usr/lib/aarch64-linux-gnu/libweston-14/drm-backend.so`; the original Debian
backend file on disk was not overwritten. After
`systemctl start weston-m0.service`, Weston reached a successful red display
on the physical panel.

## Result

**M0 DISPLAY is validated on hardware.** The validated chain is KMS splash
release, non-VT seatd, Weston 14.0.2 DRM backend with Pixman and kiosk shell,
connected DSI-1, and a physically observed red screen. The evidence supports
that the backend detects/supports atomic modesetting and that Weston reaches
the red display; it does not claim that every Weston atomic commit was
independently instrumented and proven.

No phone image, rootfs, package archive, private key, or compiled backend is
stored in Git.
