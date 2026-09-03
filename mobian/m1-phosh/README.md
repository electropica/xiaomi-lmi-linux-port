# Mobian M1 Phosh/Pixman image

This recipe derives a fresh M1 image from the validated M0 DISPLAY preflight
raw image. It does not use either historical M1 image as an input.

Run in the same complete subordinate-ID mapping used for M0. The separate
mount namespace keeps the AArch64 binfmt registration private:

```sh
unshare --mount \
  --map-users=0:1001:1 \
  --map-users=1:165537:65535 \
  --map-groups=0:1001:1 \
  --map-groups=1:165537:65535 \
  --setuid 0 --setgid 0 --fork \
mobian/m1-phosh/build-m1-phosh.sh \
  /path/to/Mobian-M0-userdata-rootfs-330-display-preflight.img \
  /path/to/rootfs-m0-display-work \
  /path/to/Mobian-M1-REPRO-userdata-phosh-4G.img \
  /path/to/Mobian-M1-REPRO-userdata-phosh-4G.android-sparse.img \
  /path/to/workdir
```

The direct package versions are pinned to those observed in the historical M1
experiment. APT still needs the recorded Debian/Mobian repositories to retain
those versions and resolve their dependencies; the resulting installed package
manifest must therefore be archived alongside a release build.

The build requires a non-empty `M1_MOBIAN_PASSWORD` environment variable. Its
value is removed from the exported environment before child processes run,
passed only to `chpasswd` over standard input, and cleared from the build
shell immediately afterwards. Neither the password nor its hash belongs in
Git or in a temporary file.

The session deliberately uses wlroots Pixman rendering. The D-v43 display DRM
node does not implement the MSM GPU UAPI needed by Freedreno, while Phoc with
Pixman has reached the DSI-1 modeset in a live hardware experiment.

## Hardware validation (2026-09-03)

M1 reached the Phosh lock screen on the Xiaomi lmi: the clear-KMS marker was
visible, Phoc acquired DSI-1 with the Pixman renderer, touch and swipe-up
worked, the passcode prompt unlocked, and the Phosh desktop displayed Files
and Settings.

Two D-v43/systemd compatibility workarounds are required. Although
`systemd-user-runtime-dir` requests a tmpfs owned by `1000:1000` with mode
`0700`, this downstream kernel produces `/run/user/1000` as `root:root` mode
`1777`. An `ExecStartPost` corrects and verifies the ephemeral mount before
`user@1000.service` may proceed. Also, `dev-dri-card0.device` remains inactive
even while the functional `/dev/dri/card0` node exists. The splash unit drops
that device-unit dependency and instead waits up to ten seconds for the real
character device before executing the validated clear-KMS script.

The initial credential is supplied externally by the operator and must be
changed after first login. The hostname is `PocoF2Pro`.

M1 generates the real `fr_FR.UTF-8` locale, records it as the system locale,
and sets the same language for the `mobian` AccountsService identity and Phosh
session. NetworkManager is installed to provide the GNOME Settings network
integration, but `usb0` is explicitly unmanaged so the validated static USB
network remains exclusively controlled by systemd-networkd.

The GNOME Bluetooth libraries are present, but BlueZ is not added yet. D-v43
uses the downstream Qualcomm BTFM SLIM/QCA6390 transport rather than a standard
HCI UART, and the M1 rootfs currently contains no identified Bluetooth
firmware or device-specific bring-up service. A hardware inventory is required
before choosing that userspace integration.

Battery reporting, clock synchronization, Virtual-1 behavior, and GPU
acceleration are intentionally outside this milestone.

## Wi-Fi integration

Manual QCA6390 bring-up is validated on hardware. The tracked systemd
automation preserves the exact successful order:

```text
read-only Android mounts -> stock firmware links -> qrtr-ns
-> forked stock cnss-daemon -> one fs_ready write -> eight seconds
-> one ON write -> bounded netdev wait -> NetworkManager
```

NetworkManager only `Wants` and orders itself after the WLAN attempt: a WLAN
failure does not prevent NetworkManager from starting. The existing
`10-m1-usb0-unmanaged.conf` keeps `usb0` under systemd-networkd throughout.

The kernel selects `qca6390/bd_j11gl.elf` dynamically. The automation exposes
the unchanged stock firmware tree and does not force `bd_j11.elf` or replace
the stock `bdwlan.elf`. Android system/vendor, the runtime APEX, modem firmware
and persist are consumed from read-only device mounts at runtime; none is
included in Git or in the M1 recipe.

The source-only property shim is compiled for AArch64 during the future M1
build. The proprietary `/vendor/bin/cnss-daemon` remains on the stock vendor
partition. No Wi-Fi connection profile or credential is part of the recipe.

The manual result is documented in
`notes/mobian-m1-wifi-hardware-validation-2026-09-03.md`. The systemd
automation has not yet been tested on hardware.
