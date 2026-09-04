# Mobian M1 REPRO v3 hardware validation — 2026-09-04

**VALIDATED ON HARDWARE**

Target: POCO F2 Pro / Redmi K30 Pro (`lmi`) with the D-v43 downstream kernel.

## Tested artifacts

- raw userdata: `Mobian-M1-REPRO-v3-userdata-phosh-4G.img`
  - SHA-256: `492f46869e61957bc488863e33b6db9ed0bfdf5b1d7157c413f903d60912b213`
- Android sparse userdata:
  `Mobian-M1-REPRO-v3-userdata-phosh-4G.android-sparse.img`
  - SHA-256: `8758bf8f07555717e16dc847928ff3156ee58c0924bfc4bffd0d0af897c3f618`
- boot image: `D-repro-01-boot.img`

The sparse artifact was copied through Windows Downloads and its SHA-256 was
verified before flashing. Fastboot wrote all three sparse segments without an
error.

## Display and Phosh

Display startup required no SSH intervention. The tracked splash unit no
longer depends on the nonfunctional `dev-dri-card0.device`; the M1 drop-in only
performs a bounded wait for the real `/dev/dri/card0` character device.
Clear-KMS, seatd, Phoc with the Pixman renderer on `DSI-1`, the Phosh lock
screen, touch, swipe-up, passcode unlock, and the Phosh desktop all worked.

Several colored rectangles appeared briefly before the loading screen and
Phosh. Their exact origin is not established; the validated KMS chain was not
changed during this milestone.

Idle blanking deliberately turns off `DSI-1` while Phoc and Phosh remain
alive. User-session D-Bus can wake the display, but a clean physical
Power-button off/on/wake cycle has not yet been validated.

## Wi-Fi and networking

The automated QCA6390 systemd chain completed through firmware preparation,
CNSS/WLFW, `FW_READY`, qcacld probe, and creation of `wlan0`. Integrated Debian
`wpasupplicant 2:2.10-24` was installed and enabled with its D-Bus activation
alias. NetworkManager listed nearby SSIDs automatically. A CLI WPA2 connection
then obtained `192.168.4.121/24`, a default route via `192.168.4.1`, DNS, and
Internet access. No Wi-Fi credential or connection profile is tracked.

The Phosh Wi-Fi controls remain nonfunctional. The current system service runs
Phosh as `mobian` alongside a lingering user manager but not in a conventional
interactive logind session. Polkit therefore cannot associate Phosh normally
with a session. A permissive temporary Polkit rule proved that NetworkManager
radio control is possible, but that rule is not an acceptable fix and is not
tracked.

## Time

Integrated `systemd-timesyncd 257.13-1~deb13u1` contacted a Debian pool server
and synchronized the system clock automatically after networking became
available. The hardware RTC still reports an incorrect historical date, and
the timezone remains `Etc/UTC`; neither issue is fixed by NTP.

## Open observations

- UPower fails before execution because `PrivateUsers=yes` cannot establish
  user namespacing on D-v43 (`EINVAL`, service status `217/USER`). The kernel
  also reports an unsupported battery power-supply property, so the battery
  `?` is not attributed solely to UPower.
- Touch and passcode entry can feel slow; libinput/Phoc reported processing
  lag around 29–72 ms.
- Settings showed intermittent launch/UI behavior, but no matching segfault or
  coredump was found; this is not recorded as a confirmed crash.
- Screenshot attempts over the user D-Bus/portal did not produce a file and
  are deferred until session integration is improved.
- Default mobile applications remain to be selected.
- `0000` has only been discussed as a possible development passcode. It is not
  a selected default and is not stored in Git.

This milestone does not validate GPU acceleration, all Phosh controls,
battery reporting, the hardware RTC, timezone policy, suspend/resume, physical
Power-button wake, or daily-use readiness.
