# D-v43 DRM/KMS display validation — 2026-09-25

## Result and validation boundary

The D-v43/OpenRC reconstruction has now produced visible output on the Xiaomi
`lmi` panel. A guarded `modetest` run performed a DRM/KMS modeset on `DSI-1`;
the operator observed several colored test rectangles on the physical screen.

This result validates the downstream display hardware path through the CRTC,
scanout plane, DSI link, panel, and backlight at `1080x2400`. It does **not**
validate GPU or EGL acceleration, Weston, Phosh, touch input, or a persistent
graphical session. The ordinary OpenRC boot still presents a black screen
because no long-lived client performs the modeset.

## State before the direct modeset

Targeted inspection of the autonomously booted OpenRC system established:

- `/sys/class/drm/card0-DSI-1/status` reported `connected`;
- the connector advertised `1080x2400` as its preferred mode;
- `DSI-1` was `disabled` and the panel's `actual_brightness` was `0`;
- no process held the DRM nodes and no client performed a permanent modeset;
- `/dev/fb0` and a usable `/proc/fb` entry were absent;
- the kernel configuration has no `CONFIG_VT`, `CONFIG_FB`, or
  `CONFIG_DRM_FBDEV_EMULATION`.

Shelli's role had previously been misread because its OpenRC service was
running. In this configuration Shelli is a plain-console UI package: its
service prepares supporting telephony/audio state but launches no graphical
process and no DRM/KMS client. The empty local start hook did not add one.
With neither fbcon nor a compositor, a connected but disabled connector and a
dark backlight were the expected idle state.

The missing framebuffer options do not prevent native DRM/KMS operation. They
remove the legacy framebuffer console/emulation path; a native KMS client can
still allocate scanout buffers and program the display.

## Reproducible DRM/KMS test

The exact one-shot test is tracked as
[`scripts/test-dsi-modetest.sh`](../scripts/test-dsi-modetest.sh), SHA-256
`cc7b0989454984e0d49c646d5033263755478954cb6ec56157ea78dbd423856a`.
It refuses to proceed unless the expected device, connector, mode, and initial
disabled state are present. It runs as the unprivileged `lmi` user, requests
connector `29` on CRTC `129` with mode
`1080x2400x60x184345cmd`, and does not write backlight controls or persistent
configuration.

During the test, `modetest` acquired the DRM resources and displayed several
colored rectangles. This is direct physical evidence that the initial black
screen was not caused by a dead panel or an unusable downstream kernel
pipeline.

The numeric DRM object IDs are properties of the validated boot and are not
assumed stable across a different kernel or device-tree build. The script
therefore inventories and checks them before acting.

## Temporary Weston 16 investigation

Weston 16 components absent from the validated Shelli rootfs were staged only
for isolated, reversible tests: `weston-backend-drm`,
`weston-shell-desktop`, `libseat`, `seatd`, and `seatd-launch`. They were not
registered with APK, no service or runlevel was changed, and no component was
installed permanently. Each attempt reported restoration of the original
system paths and left no temporary Weston or seatd process running.

The investigation progressed far enough to distinguish setup failures from
Weston/backend incompatibility:

- after passing `SEATD_VTBOUND=0` to the actual seatd process, Weston obtained
  a libseat seat and opened `/dev/dri/card0`;
- one path then failed to acquire DRM master with `Permission denied`;
- Weston 16 also aborted in `weston_drm_format_array_add_format` on an
  assertion reached while enumerating the downstream DRM formats;
- Weston 16 refused the attempted option to disable atomic modesetting, so it
  could not be used to test a legacy fallback path.

Weston never performed a modeset and produced no visible output. These failures
do not contradict the successful direct KMS test: they concern compositor,
seat/master, and backend compatibility with this downstream DRM driver.

## Offline comparison image

The following untracked reference image was analyzed read-only and was never
converted on the Windows filesystem:

| Property | Value |
| --- | --- |
| Source | `/mnt/c/Users/julien/Downloads/archi-validation-02.img.android-sparse.img` |
| Size | `2960036280` bytes |
| SHA-256 | `84182b57edb7be8e49c29e0f0b472e9b6a54f7efa645ef99664dc0e004759f78` |
| Container | Android sparse v1.0 |
| Logical raw size | `4551868416` bytes |
| Userspace | Debian 13.6, systemd 257.13 |
| Kernel artifacts | Linux 4.19.325, build `#7-postmarketOS` |

Filesystem metadata showed a constructed image with a mount count of zero;
no internal record demonstrated that it had ever booted or displayed output.
Its name is therefore not treated as hardware-validation evidence.

The image nevertheless contains a useful design reference:

- Phosh 0.46 and Phoc 0.46 as the primary mobile stack;
- an alternative Weston 14.0.2 path using the Pixman renderer and kiosk shell;
- seatd 0.9.1 run as root with `SEATD_VTBOUND=0`, followed by Weston as root;
- `lmi-splash-release`, which uses atomic `modetest` operations to release
  CRTC `129` and plane `58` before the compositor starts;
- an intentional absence of VT/fbcon, matching a native DRM-only design.

The reference binaries are Debian/glibc binaries and cannot be copied into the
Alpine/musl D-v43 rootfs. The image instead supports a source-level direction:
the continuous splash may retain DRM state, seatd must not bind a nonexistent
VT, and an older compositor/backend combination may better fit the downstream
4.19 DRM implementation.

## Conclusion and next direction

The display hardware and native KMS path are validated. The unresolved layer
is userspace integration: ownership/release of DRM master and selection of a
compositor compatible with the downstream driver.

The next argued path is an isolated, native Alpine/musl Weston 14 build using
Pixman and the kiosk shell, a root seatd instance with `SEATD_VTBOUND=0`, and a
guarded release of the continuous splash before Weston starts. That path has
not been built or validated and is not part of this milestone.

Still open:

- GPU/EGL acceleration;
- a persistent Weston or Phosh session;
- touch input;
- the previously observed `powerkey` crash;
- Wi-Fi association, DHCP, and Internet access.
