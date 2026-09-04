# Mobian status

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

The systemd implementation under `mobian/m1-phosh/wifi` and the integrated
Debian `wpasupplicant` are now validated on hardware in M1 REPRO v3. The image
completed firmware bring-up, `FW_READY`, qcacld probe, WLAN creation,
automatic SSID listing, CLI WPA2 association, DHCP, DNS, and Internet access
while preserving USB SSH. No Wi-Fi profile or credential is tracked. See
`notes/mobian-m1-wifi-hardware-validation-2026-09-03.md`.

## M1 REPRO v2 IMAGE — HARDWARE-TESTED / CORRECTIONS REQUIRED

The reproducible M1 Phosh/Wi-Fi rootfs and phone images were built and
validated on the host. The final ext4 has the expected `pmOS_root` label and
UUID, passes `e2fsck -fn`, and the Android sparse image round-trips bit-for-bit
to the final raw image. Package installation, service enablement, Phosh/Pixman
configuration, the AArch64 property shim, and the absence of proprietary
Android payloads in the image were checked.

This exact image subsequently booted on the phone. Its low-level systemd Wi-Fi
automation succeeded, and its Phosh/Pixman stack worked when the splash unit
was started without its stale `dev-dri-card0.device` dependency. Automatic
display startup was blocked by that inherited dependency; Wi-Fi association
needed runtime installation of `wpasupplicant`; and time synchronization
needed runtime installation of `systemd-timesyncd`. Those findings produced
the recipe corrections subsequently validated in v3. See
`notes/mobian-m1-repro-v2-hardware-validation-2026-09-04.md`.

## M1 REPRO v3 — VALIDATED ON HARDWARE

The v3 userdata image booted on Xiaomi `lmi` with D-v43 and reached Phosh
automatically without SSH intervention. The corrected splash unit has no
`dev-dri-card0.device` dependency; its bounded wait for the real character
device allowed clear-KMS, seatd, Phoc/Pixman on `DSI-1`, the lock screen, and
the unlocked Phosh desktop to start normally.

The integrated low-level QCA6390 automation and `wpasupplicant 2:2.10-24`
provided WLAN discovery, scanning, CLI WPA2 association, DHCP, routing, DNS,
and Internet access. Integrated `systemd-timesyncd 257.13-1~deb13u1`
synchronized the system clock after networking became available; this does
not repair the incorrect hardware RTC.

After the v3 image validation, a clean runtime experiment additionally
validated `PAMName=login` with `XDG_SEAT=seat0`: logind created an active
Wayland `Class=user` session on graphical `seat0` with `VTNr=0`, Phoc remained
functional through seatd, and the Phosh Polkit agent registered for that
session. NetworkManager scan, radio and network-control authorization passed
for the real GNOME Settings PID and D-Bus name, and Wi-Fi controls worked in
the UI. This setup is now tracked by the M1 recipe but still requires
post-rebuild hardware validation; it was not present in the original v3
image. `settings.modify.system` correctly remains an administrative action.

That persistent session setup was subsequently validated in v4. Still open
are timezone control, UPower/battery reporting, colored boot rectangles,
power-button suspend/wake, screenshot integration, touch/UI latency, observed
Settings launch instability, and the eventual default application set.
Administrative system-connection editing continues to require its expected
authentication rather than a policy bypass. See the v3 hardware note and
`notes/mobian-m1-phosh-logind-polkit-validation-2026-09-04.md`.

## M1 REPRO v4 — VALIDATED ON HARDWARE / KEYRING INTEGRATION TO REVALIDATE

M1 REPRO v4 was built from commit `d1469e8`; its Android sparse userdata
SHA-256 is `84361c4d7a1bced22046e8359d17865a55983ab730a15bd0489ed98d40fa8c92`.
It booted automatically into the validated clear-KMS, seatd, Phoc/Pixman and
Phosh path. The persistent PAM/seat configuration created an active Wayland
logind user session on graphical `seat0` without a VT, and the Phosh Polkit
agent registered correctly. The lock screen, touch, swipe-up, passcode unlock
and desktop remained functional.

The remaining Wi-Fi GUI failure was not caused by Phosh's process retaining
the lingering user manager's audit session. NetworkManager registered the
Phosh NetworkAgent and sent `SaveSecrets` and `GetSecrets` on the fixed
SecretAgent D-Bus path. Phosh returned
`org.freedesktop.NetworkManager.SecretAgent.Failed` because
`org.freedesktop.secrets` was unavailable: v4 contained `libsecret` but not
`gnome-keyring`. Installing Debian `gnome-keyring 48.0-1` at runtime supplied
the activatable Secret Service, and GNOME Settings Wi-Fi connection worked
immediately without reboot or manual daemon startup.

The recipe now pins `gnome-keyring 48.0-1`. Its presence and automatic Secret
Service activation remain to be validated in the next rebuilt image. No
credential, connection profile, permissive Polkit rule or forced daemon start
is tracked. Detailed evidence is in
`notes/mobian-m1-repro-v4-hardware-validation-2026-09-04.md`.

## M1 REPRO v5 — RUNTIME STARTUP FIXES VALIDATED / REBUILD REQUIRED

M1 REPRO v5 was built from commit `593676f`; its Android sparse userdata
SHA-256 is `b4adb244c686dcbbc1c10cce9087c792f69b8410080995893336ddd1f6a3f142`.
It retained the validated automatic display, PAM/logind/seat, Phosh, touch and
GUI Wi-Fi paths, including first-time PSK entry through the Secret Service.

The integrated keyring package initially added a roughly 90-second delay:
three legacy XDG autostarts requested GNOME startup notification after the
systemd user service had already started the same daemon. Runtime overrides
adding `X-GNOME-HiddenUnderSystemd=true` to the `secrets`, `pkcs11`, and `ssh`
entries removed the timeout while preserving `org.freedesktop.secrets` and GUI
Wi-Fi operation.

UPower separately delayed Phosh by two 25-second D-Bus timeouts because
systemd 257.13 could not create the `PrivateUsers=yes` user namespace on D-v43
and exited with `217/USER` before starting `upowerd`. A drop-in changing only
`PrivateUsers=no` started UPower successfully; all other sandboxing remained.
With both corrections applied, Phosh reported ready after 1.65 seconds and the
lock screen appeared at roughly 40 seconds from boot.

Both hardware-tested corrections are now represented in the recipe but still
require validation from a rebuilt image. Detailed evidence is in
`notes/mobian-m1-repro-v5-hardware-validation-2026-09-05.md`.

## M1 REPRO v6 — VALIDATED ON HARDWARE

M1 REPRO v6 was freshly built from commit `d054ba8`; its Android sparse
userdata is 1,881,808,716 bytes with SHA-256
`b6e7c3bbb57e4edd1f17c829ded37b7c8ce94b883329d34d983cb05f44a30a00`.
The build completed with a clean filesystem check, the Windows transfer hash
matched, and all three sparse userdata segments flashed successfully.

This image reproduces both persistent startup corrections. The three GNOME
Keyring autostarts no longer cause their roughly 90-second registration
timeout, while the systemd user daemon and `org.freedesktop.secrets` remain
available. The UPower drop-in reports `PrivateUsers=no`; `upower.service`
starts successfully without `217/USER`. GNOME Session started in about 120 ms,
UPower acquired its D-Bus name in under one second, and Phosh reported ready
in 1.60 seconds.

The active Wayland logind session remained attached to graphical `seat0` with
no VT. The lock screen, touch and passcode unlock worked. From a freshly
flashed image, GNOME Settings displayed the Wi-Fi secret prompt, accepted a
user-entered credential, connected successfully, and allowed automatic NTP
synchronization. No SSID, profile or credential is tracked.

The observed lock screen appeared around 50 seconds from boot. The difference
from the corrected v5 runtime boot occurred before `phosh-m0.service` and is
not attributed to Keyring or UPower. Dynamic battery tracking remains
unvalidated despite Phosh displaying 100%; `getty@tty1.service`, colored
clear-KMS rectangles, French OSK layout, GPU acceleration and modem/SIM remain
open. See `notes/mobian-m1-repro-v6-hardware-validation-2026-09-05.md`.

## Repository policy

Generated `.img`, `.ext4`, Android sparse images, root filesystems, private
keys, caches and other build artifacts are intentionally excluded from Git.
