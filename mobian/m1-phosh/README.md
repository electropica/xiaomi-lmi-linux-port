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

`gnome-keyring 48.0-1` is a direct input. Its D-Bus-activatable Secret Service
is required by the Phosh NetworkAgent to retrieve and prompt for Wi-Fi secrets.
The recipe does not force-start `gnome-keyring-daemon`; Debian's normal user
service and D-Bus activation remain authoritative. Debian also ships three
legacy GNOME autostarts for its `secrets`, `pkcs11`, and `ssh` components. The
recipe marks each `X-GNOME-HiddenUnderSystemd=true`, preserving the files while
preventing duplicate launches and GNOME Session notification timeouts when the
daemon is already managed by the systemd user service.

Development images use `0000` as the default `mobian` passcode. A non-empty
`M1_MOBIAN_PASSWORD` environment variable overrides that default when the
build is launched. The selected value is removed from the exported environment
before child processes run, passed only to `chpasswd` over standard input, and
cleared from the build shell immediately afterwards. The development passcode
must be changed before any real use; an operator-supplied password and its hash
must not be stored in Git or in a temporary file.

Fresh development images also install the tracked public diagnostic key
`codex-lmi.pub` in root's `authorized_keys`. Existing authorized keys are
preserved, duplicate key material is rejected, and the build verifies modes
`0700` and `0600`. Only the public key is tracked; this diagnostic access must
be removed or replaced before any real-world deployment.

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

The default development passcode is `0000`, unless the operator supplies a
non-empty `M1_MOBIAN_PASSWORD` override. It must be changed before real use.
The hostname is `PocoF2Pro`.

M1 generates the real `fr_FR.UTF-8` locale, records it as the system locale,
and sets the same language for the `mobian` AccountsService identity and Phosh
session. The recipe also installs a textual GSettings schema override making
`[('xkb', 'fr')]` the default input source, then compiles the schema cache in
the chroot. This requires no user D-Bus session and does not pre-create
`~/.config/dconf/user`. NetworkManager is installed to provide the GNOME
Settings network integration, but `usb0` is explicitly unmanaged so the
validated static USB network remains exclusively controlled by
systemd-networkd.

The GNOME Bluetooth libraries are present, but BlueZ is not added yet. The
validated BTFM SLIM path is the QCA6390 audio/FM side; it is not the HCI
transport. HCI instead uses QUPv3 SE6 through the GENI UART `/dev/ttyHS0` and
the N_HCI QCA protocol. The V2 non-serdev kernel path is hardware-validated as
boot-safe, and a controlled N_HCI Phase A created `hci0` and completed the
Hastings PATCH/NVM/Reset setup. Phase B then brought `hci0` UP and completed a
real bidirectional Read Local Version exchange. The stock Android BD_ADDR
provisioning path has also been statically traced through Xiaomi QMI service
`0xffe4`, message `0x0002`, Bluetooth NV operation `0x01bf`,
`/data/vendor/mac_addr/bt.mac` and
`persist.vendor.service.bdroid.bdaddr`. BlueZ, scan and pairing remain
unvalidated.

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
below. In the original v2/v3 images, UPower failed before exec because its
`PrivateUsers=yes` sandbox could not create a user namespace on D-v43 (`EINVAL`,
status `217/USER`). The narrow runtime relaxation subsequently validated in v5
is now included, but the kernel also reports an unsupported battery property,
so service startup is not treated as complete battery validation.

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
RTC remains wrong and timezone control is unresolved. In the original v3
image, UPower still failed its user-namespace sandbox while the kernel
separately reported an unsupported battery property; the later v5 runtime
validation below resolves only the service-start failure. Idle blanking
turns off `DSI-1` without killing Phoc, but physical Power-button wake has not
been validated. Touch/input lag of roughly 29--72 ms remains visible in logs.
Settings showed intermittent launch/UI behavior without a matching confirmed
segfault or coredump. SSH screenshot work is deferred, the default application
set is undecided, and `0000` was only discussed as a possible development
passcode—it is not selected or stored by the recipe.

The exact v3 artifact identities and hardware evidence are recorded in
`notes/mobian-m1-repro-v3-hardware-validation-2026-09-04.md`.

## Spontaneous display wake diagnosis (WAKE7--WAKE17, 2026-09-06)

Session-bus capture identified the recurring spontaneous display wake as a
userspace idle-policy path. `gsd-power` owned the relevant Mutter
`org.gnome.Mutter.IdleMonitor` watches. A `WatchFired` signal was immediately
followed by ScreenSaver, DisplayConfig and Presence changes and Phoc enabling
`DSI-1`; approximately 15 seconds later the display was disabled again.

The watch durations tracked the configured inactive timeout exactly. At 900
seconds, `gsd-power` installed 900000 and 450000 ms watches. Temporarily
changing both AC and battery timeouts to 1200 seconds changed them to 1200000
and 600000 ms, apart from short reevaluation variants. The separate 30000 ms
watch was mapped directly to a matching `WatchFired` ID, but was not sufficient
to reproduce the long-policy wake after the workaround.

Setting these keys in the real user-session dconf context removed the long
autosuspend watches:

```text
org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'
```

During a passive 700-second observation with both types set to `'nothing'`, no
spontaneous `DSI-1` enable/disable event or new `gsd-power` error occurred.
The final state restores both timeout values to 900 seconds and retains the two
`'nothing'` type values. No service, kernel wakeup source or modem state was
changed for that validation. This result establishes the causal userspace path
for this symptom, not a general conclusion about hardware wake sources or all
suspend/resume behavior. Full evidence is recorded in
`notes/mobian-m1-gsd-power-spontaneous-wakeup-validation-2026-09-06.md`.

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

## M1 REPRO v4 hardware validation (2026-09-04)

M1 REPRO v4, built from commit `d1469e8`, validated the persistent
`PAMName=login` and `XDG_SEAT=seat0` integration at automatic boot. Clear-KMS,
seatd, Phoc/Pixman, the lock screen, touch, swipe-up, passcode unlock and the
Phosh desktop continued to work. Logind created an active Wayland user session
on graphical `seat0` without a VT, and the Phosh Polkit agent registered for
that session.

NetworkManager registered and called the Phosh NetworkAgent. Monitoring the
fixed SecretAgent object path showed `SaveSecrets` and `GetSecrets`; the latter
failed because `org.freedesktop.secrets` was not activatable. The image had
`libsecret` but lacked `gnome-keyring`. Installing Debian
`gnome-keyring 48.0-1` made the Secret Service activatable, after which Wi-Fi
connection from GNOME Settings worked immediately without rebooting or
manually starting the keyring daemon. This disproves session filtering as the
cause of that SecretAgent failure.

The recipe now includes `gnome-keyring`, but an image rebuilt with this new
direct dependency still requires hardware validation. No Wi-Fi profile,
credential, permissive Polkit rule or forced keyring startup is included. See
`notes/mobian-m1-repro-v4-hardware-validation-2026-09-04.md`.

## M1 REPRO v5 hardware validation (2026-09-05)

M1 REPRO v5, built from commit `593676f`, validated integrated
`gnome-keyring 48.0-1` and the Wi-Fi Secret Service, but exposed two independent
startup delays. The enabled systemd user service had already started the
keyring daemon when three legacy `PreDisplayServer` autostarts ran with
`X-GNOME-Autostart-Notify=true`. Their `--start` processes found the existing
daemon but did not register with GNOME Session, which waited about 90 seconds.
Adding `X-GNOME-HiddenUnderSystemd=true` to all three entries removed that
timeout while retaining the daemon, its socket, `org.freedesktop.secrets`, and
functional GUI Wi-Fi secret handling.

UPower then accounted for two consecutive 25-second D-Bus activation waits.
Its Debian unit explicitly requested `PrivateUsers=yes`; systemd 257.13 failed
to construct that user namespace on D-v43 with `EINVAL` and status `217/USER`,
before executing `upowerd`. A device-specific drop-in changing only
`PrivateUsers=no` made UPower active and gave `org.freedesktop.UPower` a real
D-Bus owner. Every other sandbox directive remained effective. With both
runtime corrections, Phosh became ready in 1.65 seconds after its own start
and the lock screen appeared around 40 seconds after boot.

The recipe now carries both hardware-tested settings. A rebuilt image must
revalidate them before they are considered persistently delivered. Detailed
evidence and the v5 sparse artifact identity are recorded in
`notes/mobian-m1-repro-v5-hardware-validation-2026-09-05.md`.

## M1 REPRO v6 hardware validation (2026-09-05)

M1 REPRO v6 was freshly built from commit `d054ba8` and validated both startup
fixes as persistent recipe output. GNOME Session no longer waited for the three
legacy Keyring launchers, while the systemd user daemon and Secret Service
remained available. UPower ran with the device-specific `PrivateUsers=no`
drop-in and acquired `org.freedesktop.UPower` without the former `217/USER`
failure. None of the three old timeout messages appeared.

`gnome-session-manager@phosh.service` started in about 120 ms, UPower acquired
its D-Bus name in under one second, and Phosh reported ready after 1.60 seconds.
The active Wayland logind session remained on graphical `seat0`; lock screen,
touch and passcode unlock passed. On the fresh image, GNOME Settings displayed
the Wi-Fi password prompt, connected successfully through the Secret Service,
and NTP synchronized automatically after networking became available. No
tested profile, SSID or credential is stored by the project.

The visually observed lock screen arrived around 50 seconds. The difference
from the corrected v5 runtime boot is before `phosh-m0.service` and remains
unexplained. UPower startup is validated, but dynamic battery tracking is not:
the UI showed 100% and downstream power-supply recognition warnings remain.
The exact artifact identity and evidence are in
`notes/mobian-m1-repro-v6-hardware-validation-2026-09-05.md`.

## M1 REPRO v7 hardware validation (2026-09-05)

M1 REPRO v7, again built from commit `d054ba8`, preserved the v6 graphical,
session, GUI Wi-Fi, Secret Service, UPower and NTP results. Its measured
critical chain showed that WLAN initialization was actually on the path to
Phosh through NetworkManager, `network.target`, `systemd-user-sessions`, and
the lingering user manager. Clear-KMS finished much earlier on a separate
branch and was not critical on that boot. No boot dependency is changed here.

Battery capacity and UPower reporting were observed dynamically from 100% to
95% during about 39 minutes physically unplugged. UPower reported discharging
and on-battery, although downstream sysfs still inconsistently reported
`Charging` and USB present/online. Charging and reconnection transitions remain
untested.

The installed locale alone had left the input source at `[('xkb', 'us')]`.
Setting it to `[('xkb', 'fr')]` immediately changed Squeekboard to AZERTY and
persisted across a complete reboot. The recipe now expresses that validated
default as a compiled textual schema override rather than importing the
runtime user's dconf database. The fresh-image delivery of this new recipe
setting remains to be validated. See
`notes/mobian-m1-repro-v7-hardware-validation-2026-09-05.md`.

## M1 REPRO v8 xdg-user-dirs startup finding

The recipe-provided French input default was reproduced on hardware: the OSK
loaded its French resource and AZERTY was functional. The launch was delayed
by a separate D-v43 compatibility problem. GNOME Session started the Debian
`xdg-user-dirs.desktop` entry in its `Initialization` phase, then GLib failed
to watch the short-lived process with `waitid(..., pidfd=...)` returning
`EINVAL`. GNOME Session consequently kept the application pending until its
roughly 90-second phase timeout; Squeekboard started immediately after that
barrier expired.

`xdg-user-dirs-update` remains necessary to initialize the standard user
directories. The recipe therefore preserves the executable and its effect,
marks only the legacy GNOME autostart `X-GNOME-HiddenUnderSystemd=true`, and
runs the command through a device-specific systemd user oneshot ordered before
`gnome-session-pre.target`. It does not alter the global GNOME timeout or the
Squeekboard required component. This integration still requires validation on
a fresh rebuilt image.

## M1 REPRO v9 hardware validation (2026-09-05)

M1 REPRO v9 was freshly built from commit `e7e63ba` and validated the targeted
workaround. `xdg-user-dirs-lmi.service` executed successfully with status zero;
as a oneshot without `RemainAfterExit`, its subsequent inactive/dead state is
expected. The historical autostart produced no registration-timeout warning,
and all eight localized XDG directories were created for `mobian`.

Squeekboard appeared immediately after unlock, loaded `Resource: fr`, and was
directly usable as French AZERTY. Thus both the compiled input-source default
and its fresh-image delivery are now hardware-validated. The general
`waitid`/pidfd incompatibility of D-v43 remains; this workaround deliberately
addresses only `xdg-user-dirs`. The artifact identity and directory evidence
are recorded in
`notes/mobian-m1-repro-v9-hardware-validation-2026-09-05.md`.

## Post-v9 Bluetooth SLIM/PDR runtime validation (2026-09-05)

The first missing NGD prerequisite was confirmed to be Qualcomm Service
Registry Locator `64/1/1`. Without pd-mapper, D-v43's locator client waited its
`3000000` ms (3000-second) timeout and its SSR fallback occurred far too late
for a manually booted ADSP. Merely bringing the ADSP online could therefore
publish SLIM control service `769/1/0` without scheduling the domain-up path
needed for SLIM enumeration.

The stock Android `/vendor/bin/pd-mapper` was tested through a transient
systemd unit. A private read-only bind exposed the already mounted stock
firmware tree at its Android path; no stock file was modified or copied into
Git. The daemon published locator `64/1/1`, read the stock PDR maps, and
resolved `appsngd1` / `avs/audio` through `adspua.jsn` to
`msm/adsp/audio_pd`, instance 74. Only after these guards passed was the ADSP
booted once.

The ADSP reached `ONLINE` with zero crashes. QRTR then exposed `66/1/74` and
`769/1/0`, the audio process domain notified UP, NGD accumulated runtime-active
time, and SLIM created both `btfmslim_slave` and `btfmslim_slave_ifd`.
`btfmslim_slave` reported the `qcom,btfmslim_slave` DT identity and was bound
to `btfmslim-driver`. Phosh, touch, Wi-Fi and general stability passed the
operator's post-test check. The Bluetooth UI did not change spontaneously and
`/sys/class/bluetooth` remained empty, so HCI is deliberately not claimed.

The recipe installs no proprietary payload: the stock pd-mapper and PDR maps
are consumed from the existing read-only Android partitions. The implementation
consists of:

```text
lmi-android-wifi-mounts.service
  -> lmi-adsp-firmware-prepare.service
  -> qrtr-ns.service
  -> lmi-pd-mapper.service
       (private read-only firmware_mnt bind; locator/PDR readiness barrier)
  -> lmi-adsp-btfm.service
       (one guarded ADSP write; bounded ONLINE/QRTR/BTFM validation)
```

The pd-mapper unit starts with system-service privileges because it consumes
the Android executable exactly as in the validated experiment. That stock
daemon changes to numeric Android system UID/GID 1000, which is also the
`mobian` account on this rootfs; this identity collision is a known security
risk to revisit, not evidence of access to a graphical session. A private
mount namespace limits its stock firmware view to a read-only bind. No retry
policy is configured. A `/run/lmi-adsp/boot-attempted` no-clobber marker and
the ADSP state/crash guards prevent a second write by the tracked oneshot in
the same boot.

M1 REPRO v11 proved this path on a freshly flashed image. The firmware prepare
oneshot passed at 20.023 seconds; pd-mapper started at 20.089 seconds; the
locator, PDR mapping, guarded ADSP boot and BTFM binding all completed by
20.786 seconds. QRTR exposed `64/1/1`, `66/1/74` and `769/1/0`; ADSP was
`ONLINE` with zero crashes and one boot attempt; NGD accumulated runtime-active
time; and both BTFM devices appeared with the QCA6390 slave bound. Phosh,
unlock, French OSK, Wi-Fi and general stability remained functional.

HCI diagnosis may now proceed from this validated bound BTFM state, but
`/sys/class/bluetooth` remains empty and no HCI behavior is claimed. A
boot-time USB/RNDIS observation is also retained: SSH may occasionally require
physically disconnecting and reconnecting USB; no cause or fix is claimed
here. Runtime experiment evidence is in
`notes/mobian-m1-bluetooth-slim-pdr-runtime-validation-2026-09-05.md`.
Fresh-image evidence is in
`notes/mobian-m1-repro-v11-hardware-validation-2026-09-05.md`.

## QCA6390 Hastings HCI design (2026-09-05)

The empty `/sys/class/bluetooth` after successful BTFM SLIM binding is now
separated from the audio-side transport. Static review of D-v43 and the lmi
DT establishes that `btfmslim-driver` registers the SLIM codec/DAI path; it
does not create `hci0`. HCI is expected over QUPv3 SE6 (`0x998000`) using the
high-speed GENI UART exposed as `/dev/ttyHS0`. Xiaomi provides no Bluetooth
serdev child, matching the stock QTI HAL's direct UART attach model.

The retained first-bring-up design uses N_HCI (`15`) and the QCA protocol
(`HCI_UART_QCA=8`). A userspace attach process must open and configure
`/dev/ttyHS0`, select the line discipline, flags and QCA protocol, and keep the
file descriptor open. Controller power remains handled separately through
the existing `qca,qca6390` `bluetooth-power.c` device and `/dev/btpower` path.

D-v43 already has `hci_qca.c`, `btqca.c` and Qualcomm TLV/NVM parsing, but it
only models AR3002, Rome and WCN3990. The minimum kernel work is to add the
QCA6390 type, select `qca/htbtfw%02x.tlv` and `qca/htnv%02x.bin` (Hastings
2.0 maps to `rom_ver=0x20`), make the non-serdev path safe and coherent, and
enable `BT_QCA`, `BT_HCIUART`, H4 and QCA while retaining MSM GENI serial and
MSM Bluetooth power. The lmi-specific QCA6390 choice must not change the
historical Rome fallback for other line-discipline users.

The V2 micro-backport and required HCI UART configuration are now present.
Three RAM-boot variants containing the restored historical `fc->source` VFS
fix passed through rootfs and userspace: HCI UART/H4 only, generic QCA without
the lmi selector, and complete QCA6390 V2. Earlier failures built without that
VFS fix are non-discriminating for Bluetooth.

Phase A has since validated controlled N_HCI attach, `hci0` creation and the
real QCA6390 setup through stock Hastings PATCH/NVM download and final Reset.
The controller logged composite `soc_ver=0x02000200`; this is consistent with
the raw `soc_id=0x400a0200` expectation after the driver's 32-bit
`get_soc_ver()` calculation, and produces `rom_ver=0x20`. The 3 Mbaud and IBS
enable paths are inferred from successful control flow, not directly measured
runtime traffic.

Phase B retained one successful attach, waited for auto-off, brought `hci0`
UP, and bound a raw HCI socket. A Read Local Version (`0x1001`) after three
seconds idle returned status `0x00`, HCI/LMP version `0x0b`, Qualcomm
manufacturer `0x001d` and LMP subversion `0x27ec`; `CMD_TX` and `EVT_RX` each
advanced by one. This validates real bidirectional HCI traffic. IBS remains
indirectly inferred because debugfs counters were unavailable. The non-zero
BD_ADDR `00:00:00:00:5a:ad` enabled HCI operation. Its stock Android
provisioning path is now statically established: `/vendor/bin/nv_mac` reads
Bluetooth NV operation `0x01bf` through Xiaomi QMI service `0xffe4`, message
`0x0002`, writes the returned six bytes to `/data/vendor/mac_addr/bt.mac`,
and `init.mi.btmac.sh` publishes the converted address through
`persist.vendor.service.bdroid.bdaddr`. `HCIDEVDOWN` and N_HCI rollback passed
without destabilizing Phosh, RNDIS or Wi-Fi. A fresh repeated setup requires
a controlled `bt_power` cycle; retrying PATCH on the still-initialized
controller timed out. BlueZ, scan and pairing remain untested. Serdev DT conversion,
modern pwrseq, power
integration into `hci_qca`, ACPI, modern Qualcomm coredump/shutdown support
and a wholesale mainline rewrite remain outside the first test. See
`notes/mobian-m1-qca6390-hastings-hci-design-2026-09-05.md` and
`notes/mobian-m1-qca6390-v2-boot-safety-validation-2026-09-06.md`.

## External SDX55 modem ESOC/mission-mode validation (DV121--DV207)

The external modem is an SDX55M described by `qcom,ext-sdx55m` and connected
over PCIe with link information `0306_02.01.00`. Runtime exposes
`/dev/esoc-0` and `/dev/subsys_esoc0`. The Qualcomm request engine must be
registered before the SSR subsystem device is opened: the open blocks inside
`mdm_subsys_powerup()` while firmware boot requests are serviced. DV119 fixes
the original single-thread helper by keeping `ESOC_WAIT_FOR_REQ` in the main
thread and performing the subsystem open in a second thread.

The Xiaomi Android ROM's FAT16 `NON-HLOS.bin` contains 18 SDX55 files under
`image/sdx55m`. Its `sbl1.mbn` is 548056 bytes, SHA256
`0fd2fdaf19831c8ff482ca77ca236ee282101c9bdf5ab7b46dc4e24a484e84dc`.
With that file available at `/lib/firmware/sdx55m/sbl1.mbn`, DV121 caused the
modem to enumerate as PCI `17cb:0306`, bind to MHI, create the BL and Sahara
devices, expose `/dev/mhi_0306_02.01.00_pipe_2`, and deliver `ESOC_REQ_IMG` to
the registered userspace request engine.

Later diagnostics found a race in the ESOC run notification. A delayed
`ESOC_RUN_STATE` could replace `CRASH` with `RUN` before a pending SSR began;
the forced shutdown then skipped crash teardown and its next power-up blocked.
DV166 directly captured the single `ssr_wq` worker sleeping in
`mdm_subsys_powerup()`. Kernel patch B1 preserves `CRASH` and `PEER_CRASH` on
late run notification while retaining the completions needed to release the
original power-up and pending SSR.

The B1 kernel RAM-booted without destabilizing Mobian, Phoc, Phosh, USB or
Wi-Fi. A fresh controlled power-up reached BL/Sahara with `crash_count=0`.
The Xiaomi `xbl_cfg.elf` and remaining 16 mappings were then transferred once
with a validation client whose automatic Sahara RESET emission was disabled.
The transfer returned zero and produced QMI, RMNET, DIAG and IP_HW mission-mode
channels plus an SSCTL connection. A single nominal `ESOC_BOOT_DONE` released
`mdm_subsys_powerup()`, set the subsystem `ONLINE` and retained mission mode
with no new error.

The complete nominal SDX55 path under B1 is therefore hardware-validated. No
cellular registration, voice, SMS or data is claimed. The specific historical
`CRASH -> late RUN_STATE -> SSR` race has not yet been reproduced under B1.

DV191--DV207 subsequently audited the Qualcomm `remotefs_sahara` EFS path
offline. The exact Xiaomi `/vendor/bin/ks` was shown to write received EFS
regions to persistent `mdm1m9kefs*` destinations, so the historical EFS-sync
invocation was not executed. Static tracing also found no demonstrated clean
Sahara termination from simply closing the host MHI endpoint.

DV207 instead extends the isolated DV196 consume-all/write-none model with the
normal `RESET -> RESET_RESP` terminal sequence. RESET is permitted only after
exact consumption of every declared region, and protocol completion requires
a strict RESET_RESP. The 32-bit and 64-bit synthetic paths pass 290 tests with
zero failures in normal and ASan/UBSan builds. This remains offline validation:
no real EFS MHI probe is authorized and `REAL_PROBE=NOT_SAFE`.

Detailed evidence is in
`notes/mobian-m1-sdx55-dv121-sahara-milestone-2026-09-06.md`,
`notes/mobian-m1-sdx55-esoc-b1-validation-2026-09-06.md` and
`notes/mobian-m1-sdx55-dv207-remotefs-reset-offline-validation-2026-09-07.md`.
