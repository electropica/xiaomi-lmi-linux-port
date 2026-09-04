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

The source-only property shim is compiled for AArch64 during M1 builds. The
proprietary `/vendor/bin/cnss-daemon` remains on the stock vendor
partition. No Wi-Fi connection profile or credential is part of the recipe.

The manual result is documented in
`notes/mobian-m1-wifi-hardware-validation-2026-09-03.md`. M1 REPRO v2
validated the systemd automation through WLAN netdev creation. M1 REPRO v3
then validated the same automation with integrated Debian `wpasupplicant`:
NetworkManager listed SSIDs and completed CLI WPA2 association, DHCP, DNS,
and Internet access. No network profile or credential is added to the recipe.

## M1 REPRO v2 host image validation (2026-09-04)

The M1 REPRO v2 image-production stage completed successfully using the
already-built rootfs. The final ext4, raw userdata, and Android sparse
identities are recorded in
`notes/mobian-m1-repro-v2-host-validation-2026-09-04.md`.

An earlier interrupted/manual finalization left a 4 GiB zero-filled file that
was not an ext4 filesystem (`file` reported `data` and the ext4 magic was
zero). It was rejected and is not a valid project artifact. The tracked recipe
uses fail-fast shell semantics and now also verifies ext4 size, type, UUID,
label, superblock magic, and `e2fsck` before creating or converting userdata.

The image was subsequently tested on hardware. See
`notes/mobian-m1-repro-v2-hardware-validation-2026-09-04.md` for the separate
automatic-start defect and the runtime package results.

## Corrections derived from the M1 REPRO v2 phone test

The M0 DISPLAY source unit already omits `dev-dri-card0.device`, but the M1
build had inherited an older copy from its source tree. An empty `Requires=`
or `After=` in the M1 drop-in did not remove that dependency. The recipe now
installs the corrected source unit explicitly and keeps only the bounded
`/dev/dri/card0` character-device wait in the M1 drop-in.

The recipe also installs the hardware-tested Debian packages
`wpasupplicant` and `systemd-timesyncd`. The former supplies NetworkManager's
missing supplicant; the latter synchronized successfully after Wi-Fi became
available. The hardware RTC remains incorrect before network synchronization.

Phosh itself remains functional with Pixman, but touch processing lag of
roughly 29--72 ms was observed in libinput/Phoc logs. Screen blanking after
idle is intentional: Phoc turns off DSI-1 while remaining alive, and a wake
through the mobian user D-Bus re-enabled the panel.

Two issues remained deliberately unresolved in the original M1 REPRO v2/v3
images. Their system service plus lingering user manager did not create a
conventional active logind session for Phosh. A broad temporary NetworkManager
Polkit rule proved CLI radio control but is not included. A later clean runtime
test resolved the session problem without such a rule; see the post-v3 section
below. UPower still fails before exec because its `PrivateUsers=yes` sandbox cannot
create a user namespace on D-v43 (`EINVAL`, status `217/USER`). No UPower
override is included until a narrow runtime test validates it; the kernel also
reports an unsupported battery property, so UPower is not assumed to be the
only battery issue.

## M1 REPRO v3 hardware validation (2026-09-04)

M1 REPRO v3 validated the three next-build corrections above on hardware:

- automatic display startup works with no `dev-dri-card0.device` dependency
  and only the bounded wait for the real `/dev/dri/card0` character device;
- integrated `wpasupplicant 2:2.10-24` supports automatic WLAN discovery and
  CLI WPA2 association through NetworkManager, followed by DHCP, DNS, and
  Internet access;
- integrated `systemd-timesyncd 257.13-1~deb13u1` synchronizes the system
  clock once the network is available.

The lock screen, touch, swipe-up, passcode unlock, and Phosh desktop were
observed again. This is not a validation of GPU acceleration, every Phosh
feature, or daily-use readiness.

Open observations were deliberately not corrected in the v3 image. Colored
rectangles appear briefly before Phosh and may be related to the development
continuous-splash path. As built, v3 still lacked a normal interactive logind
session and its Polkit-backed Wi-Fi UI actions did not work. The later runtime
validation below resolved that specific issue without a permissive rule. The
RTC remains wrong, timezone
control is unresolved, and UPower still fails its user-namespace sandbox while
the kernel separately reports an unsupported battery property. Idle blanking
turns off `DSI-1` without killing Phoc, but physical Power-button wake has not
been validated. Touch/input lag of roughly 29--72 ms remains visible in logs.
Settings showed intermittent launch/UI behavior without a matching confirmed
segfault or coredump. SSH screenshot work is deferred, the default application
set is undecided, and `0000` was only discussed as a possible development
passcode—it is not selected or stored by the recipe.

The exact v3 artifact identities and hardware evidence are recorded in
`notes/mobian-m1-repro-v3-hardware-validation-2026-09-04.md`.

## Post-v3 Phosh logind/Polkit runtime validation (2026-09-04)

Starting the unchanged v3 system once from a clean state with a temporary
runtime drop-in containing `PAMName=login` and `Environment=XDG_SEAT=seat0`
created an active logind `Class=user`, `Type=wayland` session on `seat0` with
`VTNr=0` and no TTY. `seat0` has `CanTTY=no` and `CanGraphical=yes`, confirming
that this path does not reintroduce the Debian `tty7`/`chvt` assumptions.
Phoc remained in the new `session-N.scope` and continued to use seatd, DRM and
Pixman successfully.

Phosh and GNOME Settings remained children of the persistent user manager and
retained its audit session, but this separation did not prevent correct Polkit
operation. The Phosh agent registered for the graphical session. Checks for
NetworkManager `wifi.scan`, `enable-disable-wifi`, and `network-control`
returned authorized for both the real GNOME Settings PID and its system D-Bus
name. UI radio disable/enable and activation of an existing WPA profile then
succeeded through association, DHCP and global connectivity.

`settings.modify.system` still correctly requires administrator
authentication. No permissive Polkit rule or `sudo`/`netdev` group change is
part of this recipe. A user-requested disconnect reported reason 39, and the
existing profile remains configured for autoconnect; no autoconnect defect is
claimed without further evidence.

The recipe now carries the validated PAM/seat configuration. Because the
original v3 image did not contain it, automatic boot with the persistent
integration must be revalidated after the next user-run build. Detailed
runtime evidence is recorded in
`notes/mobian-m1-phosh-logind-polkit-validation-2026-09-04.md`.
