# Evidence and source inventory

## Historical evidence (June 2026)

These paths identify the primary records used to establish the historical
D-v43 configuration. They were on the original workstation and were not
readable under these paths on the machine used to create this repository on
2026-09-23:

- `/home/julien/redmi-k30-pro-postmarketos/artifacts/images/pmos-lmi-v43-downstream-wlan-mac-persist-full-20260624.manifest`
- `/home/julien/redmi-k30-pro-postmarketos/artifacts/wsl-pmaports/pmbootstrap_v3.cfg`
- `/home/julien/redmi-k30-pro-postmarketos/notes/wifi-bringup-live-2026-06-24.md`

The records establish:

- `device-xiaomi-lmi=1-r104` and `linux-xiaomi-lmi=4.19.325-r8`;
- UI `shelli`, init system OpenRC, and user `lmi`;
- extra packages `openssh-server`, `iw`, `wpa_supplicant`, `docker`,
  `openrc-settingsd`, `vim`, and `htop`;
- successful Wi-Fi bring-up with `wlan0`, `p2p0`, and `wifi-aware0`, successful
  scans, CNSS `ONLINE`, `crash_count=0`, and the MAC read from `wlan_mac.bin`.

The historical artifact identities are recorded in `SHA256SUMS`. They are
reference identities only; the corresponding original APK/images are not
stored here and their hashes must not be attributed to September outputs.

## Frozen local inputs (September 2026)

- `/home/linuxagent/dv43-pmbootstrap-work/packages/edge/x86_64/postmarketos-initramfs-3.12.0-r1.apk`
  (`pkgver=3.12.0-r1`, `arch=noarch`, `commit=-dirty`)
- `/home/linuxagent/dv43-pmbootstrap-work/packages/edge/aarch64/device-xiaomi-lmi-1-r104.apk`
  (`pkgver=1-r104`, `arch=aarch64`, `commit=-dirty`)
- `/home/linuxagent/dv43-pmbootstrap-work/packages/edge/aarch64/linux-xiaomi-lmi-4.19.325-r8.apk`
  (`pkgver=4.19.325-r8`, `arch=aarch64`, `commit=-dirty`)
- `/home/linuxagent/dv43-openrc-reconstruction/pmbootstrap_v3.cfg`
- pmaports snapshot/work tree: `/home/linuxagent/pmaports-dv43-reference`
- pmbootstrap: `/home/linuxagent/pmbootstrap-3.10.1/pmbootstrap.py`

The September `r104` package contains the OpenRC services and D-v43 WLAN
chain, but not the PID1 instrumentation introduced in `r105`. Its `-dirty`
metadata and its different checksum prove that it is not the missing original
June package. Likewise, the reconstructed kernel package has the historical
version number but not a demonstrated historical binary identity.

`postmarketos-ui-shelli` was no longer available from current binary `edge`.
The user rebuilt `postmarketos-ui-shelli=3-r8` and
`postmarketos-ui-shelli-openrc=3-r8` from the local 2026-06-24 pmaports
snapshot. Local indexing first failed because the generated public signing
keys were not trusted. Adding the public keys to the relevant local trust
stores allowed `pmbootstrap index` to succeed. No private key, and currently
no public key, is versioned here.

## Final local package index

- `device-xiaomi-lmi=1-r104`
- `linux-xiaomi-lmi=4.19.325-r8`
- `postmarketos-initramfs=3.12.0-r1`
- `postmarketos-ui-shelli=3-r8`
- `postmarketos-ui-shelli-openrc=3-r8`

## Hardware validation record (2026-09-23)

The on-device observations in the dated milestone note were supplied directly
by the operator after flashing the reconstructed userdata image and temporarily
booting the reconstructed boot image. No phone command was run while preparing
this repository. The record includes PID 1, `uname`, OS identification,
installed package names, `rc-status`, USB-network reachability, TCP port 22,
and a successful SSH login as `lmi`.

The operator then supplied a second on-device record for the same reconstructed
userdata and boot artifacts. It covers the manual `lmi-wifi-start` invocation,
`iw dev`, CNSS state and crash count, and a successful scan with the BSS count.
SSID values were deliberately not recorded. The tested artifact identities
were:

- userdata SHA-256: `7e91267713551eeec7c1790d0a100358e23b6554753d67a5df075502a69a401c`;
- boot image SHA-256: `ecaa289c82840ae049ff846a5216937ffc68bd6d73b9c273dc11477c99be0075`.

## No-debug-shell boot validation record (2026-09-23)

The reversible builder is tracked as
`scripts/build-openrc-no-debug-shell-boot.sh`. Its SHA-256 is
`9a7d17522c113394c83092441e8a1e46d7af55d6c55ba3ef6feae0fa9687ba59`.
It is an exact copy of the environment-specific script executed by the owner;
its absolute paths intentionally describe the validated D-v43 work layout.

The owner's persistent build evidence was stored outside Git at
`/home/linuxagent/dv43-openrc-reconstruction/no-debug-shell/state-20260923T183544Z-16749`.
It includes complete pre-build backups, the generated `/boot` tree, and
`unpackbootimg` output. The extracted new cmdline exactly matches the expected
historical cmdline with only `pmos.debug-shell` removed. The restored historical
boot image was rechecked at its original SHA-256.

The owner then supplied the classic-fastboot console result and the live-system
validation record. The no-debug-shell image was launched with `fastboot boot`,
not installed persistently. The record covers automatic continuation into
OpenRC, closed TCP port 23, open TCP port 22, successful SSH access, and a live
`/proc/cmdline` without `pmos.debug-shell`. No credential is retained here.

## DRM/KMS display validation record (2026-09-25)

Targeted read-only inspection of the running OpenRC system established that
`DSI-1` was connected, advertised preferred mode `1080x2400`, and remained
disabled with no DRM client. The system had no framebuffer console. Shelli's
OpenRC service launched no graphical process.

The owner then ran the guarded one-shot test now tracked as
`scripts/test-dsi-modetest.sh`. `modetest` completed a modeset and several
colored rectangles were physically observed. This validates the CRTC,
scanout, DSI link, panel, and backlight, but not GPU/EGL, a compositor, Phosh,
or touch input. No credential, phone-derived secret, or large test log is
retained here.

Weston 16's DRM backend, desktop shell, libseat, seatd, and seatd-launch were
subsequently staged in temporary overlays only. The attempts restored every
affected path and installed nothing permanently. After correcting
`SEATD_VTBOUND`, Weston reached libseat and opened `card0`, but did not modeset:
DRM-master acquisition was denied in one path, the backend encountered its
`weston_drm_format_array_add_format` assertion, and Weston 16 rejected the
attempt to disable atomic modesetting. The temporary overlays, APKs, state
directories, and logs are intentionally not stored in Git.

## Offline display-stack reference (2026-09-25)

The source image was inspected read-only at:

- `/mnt/c/Users/julien/Downloads/archi-validation-02.img.android-sparse.img`
- size: `2960036280` bytes
- SHA-256: `84182b57edb7be8e49c29e0f0b472e9b6a54f7efa645ef99664dc0e004759f78`
- format: Android sparse v1.0; logical raw size `4551868416` bytes

Persistent analysis output was kept outside Git under
`/home/linuxagent/dv43-openrc-reconstruction/display-diagnostic/archi-validation-02-analysis/`.
The image contains Debian 13.6/systemd 257.13 and kernel 4.19.325 build
`#7-postmarketOS`. Its relevant display paths are Phosh/Phoc 0.46 and an
alternative Weston 14.0.2 Pixman/kiosk session using root seatd with
`SEATD_VTBOUND=0`, root Weston, and an atomic `lmi-splash-release` step for
CRTC 129/plane 58. VT/fbcon is intentionally absent.

The image filesystems had never been mounted according to their filesystem
metadata, so the image supplies design evidence, not hardware-validation
evidence. Its Debian/glibc binaries are not reusable directly on Alpine/musl.
No sparse/raw image, extracted rootfs, or binary from it is tracked here.

## Weston 14 display milestone (2026-09-26)

Weston 14.0.2 was rebuilt natively for Alpine/musl with DRM, Pixman, kiosk,
libseat and seatd under `/opt/weston14-lmi`. The r0 package SHA-256 is
`38b85fd8720aa99fa2e7d4eb05ffeb9d4b0828862170ea331c0861dc0c0322dc`; its
overlay SHA-256 is
`926dbe2646d077f7a1b4510f108e26bce0fcf43a94d00894498935f636a659c3`.

Weston 14 atomic commit failed with `EINVAL`. With `WESTON_DISABLE_ATOMIC=1`,
the legacy path selected DSI-1 on CRTC 184 and stayed black. The separate r1
source patch and recipe forced only DSI-1 to CRTC 129 after checking the
connector mask and CRTC availability. The resulting overlay SHA-256 is
`5f553036577dc87102a7956bd68bce87e3ff20de315b13c52a767b39cb58e814`; it
also stayed black. During Weston, DSI-1 was `enabled` but
`actual_brightness=0`. All temporary runs restored DSI-1, seatd and
`/run/seatd.sock`.

The source-only recipe, patch and wrappers are under
`scripts/weston14-crtc129/`. No Weston APK, overlay, source tarball, rootfs,
image, remote journal, temporary state or secret is tracked. Weston work is
intentionally suspended while OS and application work continues on the older
functional build.
