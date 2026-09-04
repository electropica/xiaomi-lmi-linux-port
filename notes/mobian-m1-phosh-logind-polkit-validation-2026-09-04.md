# Mobian M1 Phosh logind/Polkit runtime validation — 2026-09-04

**RUNTIME HARDWARE VALIDATION PASSED**
**PERSISTENT RECIPE REQUIRES POST-BUILD HARDWARE REVALIDATION**

Target: POCO F2 Pro / Redmi K30 Pro (`lmi`) running M1 REPRO v3 with the D-v43
downstream kernel. The original v3 image did not contain this configuration.
A temporary drop-in under `/run/systemd/system` added only:

```ini
[Service]
PAMName=login
Environment=XDG_SEAT=seat0
```

From a clean state with no prior graphical session or pending GNOME user jobs,
one start of `phosh-m0.service` produced logind session 9 with UID 1000,
`Service=login`, `Desktop=phosh`, `Type=wayland`, `Class=user`, `Seat=seat0`,
`VTNr=0`, no TTY, and active state. Graphical `seat0` reported session 9 as its
active session while retaining `CanTTY=no` and `CanGraphical=yes`.

Phoc was the session leader in `session-9.scope`, had audit session 9 and the
expected XDG session/seat metadata, and continued to operate through seatd
with the validated DRM/Pixman path. The Phosh lock screen appeared normally.

Phosh and GNOME Settings were launched by the already-running per-user systemd
manager and retained audit session 1 under `user@1000.service`. This separation
did not prevent Polkit from working: the Phosh authentication agent registered
for `unix-session:9`. For the real GNOME Settings PID, and separately for its
real system-bus name, `pkcheck` returned 0 for:

- `org.freedesktop.NetworkManager.wifi.scan`;
- `org.freedesktop.NetworkManager.enable-disable-wifi`;
- `org.freedesktop.NetworkManager.network-control`.

GNOME Settings then successfully disabled Wi-Fi, re-enabled the radio, and
activated the existing WPA profile. Association, DHCP and
`CONNECTED_GLOBAL` followed. No credential or connection profile is recorded
here or added to the repository.

`org.freedesktop.NetworkManager.settings.modify.system` returned 2 for both
the PID and D-Bus subjects because administrator authentication is required by
the installed policy. A root authentication window observed in connection
properties corresponded to that separate administrative action, not to the
resolved scan/radio/session defect. No permissive Polkit rule and no
`sudo`/`netdev` membership change was used or added.

A UI-requested disconnect was recorded as NetworkManager reason 39, “Device
disconnected by user or client”. The existing profile had autoconnect enabled;
this evidence alone does not establish an autoconnect bug.

This experiment validates the PAM/logind/seat design and justifies tracking it
in `phosh-m0.service`. It does not validate automatic boot from a rebuilt image
containing that change. The next image must regress boot, display, touch,
unlock, seatd/DRM/Pixman, logind session properties, Polkit, Wi-Fi, USB SSH,
session cleanup and absence of duplicate graphical sessions.
