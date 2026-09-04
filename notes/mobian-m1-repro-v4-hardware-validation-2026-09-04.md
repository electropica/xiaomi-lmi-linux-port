# Mobian M1 REPRO v4 hardware validation — 2026-09-04

**PAM/LOGIND/SEAT INTEGRATION VALIDATED ON HARDWARE**
**GNOME KEYRING RUNTIME FIX VALIDATED; RECIPE INTEGRATION REQUIRES REBUILD**

Target: POCO F2 Pro / Redmi K30 Pro (`lmi`) with the downstream D-v43 kernel.

## Tested artifact

- source commit: `d1469e8 Integrate validated Phosh logind seat setup`
- Android sparse userdata:
  `Mobian-M1-REPRO-v4-userdata-phosh-4G.android-sparse.img`
- SHA-256: `84361c4d7a1bced22046e8359d17865a55983ab730a15bd0489ed98d40fa8c92`

## Automatic graphical session

The image booted through clear-KMS, seatd and Phoc/Pixman into Phosh. Colored
clear-KMS rectangles remained visible for about two seconds. The lock screen,
touch, swipe-up, passcode unlock and desktop worked.

The integrated `PAMName=login` and `Environment=XDG_SEAT=seat0` produced active
logind session 2 with `Service=login`, `Desktop=phosh`, `Type=wayland`,
`Class=user`, `Seat=seat0`, `VTNr=0`, no TTY and `session-2.scope`. Graphical
`seat0` reported session 2 active with `CanTTY=no`. Phoc led that session while
continuing to use seatd. Phosh remained under the persistent user manager's
audit session, but its Polkit agent registered for `unix-session:2`; the old
`No session for pid` failure did not recur.

## NetworkManager SecretAgent diagnosis

NetworkManager 1.52.1 registered the Phosh NetworkAgent at system-bus owner
`:1.22`. Monitoring the correct fixed object path,
`/org/freedesktop/NetworkManager/SecretAgent`, observed NetworkManager send
`SaveSecrets` and then `GetSecrets` for the selected WPA network. This proves
that the agent was registered, eligible and called. NetworkManager's session
monitor only prefers agents whose UID has an active session; it did not reject
Phosh based on its PID's audit session.

Phosh replied to `GetSecrets` with:

```text
org.freedesktop.NetworkManager.SecretAgent.Failed
Internal error while retrieving secrets from the keyring
(The name org.freedesktop.secrets was not provided by any .service files)
```

The image contained `libsecret-1-0 0.21.7-1` and `libsecret-common 0.21.7-1`
but not `gnome-keyring`, its Secret Service activation file, or a keyring
daemon service.

## Runtime validation of the dependency

Installing Debian `gnome-keyring 48.0-1` with `--no-install-recommends`
provided `/usr/share/dbus-1/services/org.freedesktop.secrets.service` plus the
normal user service and socket. The Secret Service became D-Bus activatable.
Neither a reboot nor a manual start of `gnome-keyring-daemon` was performed.
A subsequent SSID selection in GNOME Settings worked normally, confirming the
missing Secret Service as the cause of the Wi-Fi GUI secret prompt failure.

No tested connection profile, PSK or other Wi-Fi secret is recorded here or
included in the repository. No permissive Polkit rule was used as the fix.
Administrative `org.freedesktop.NetworkManager.settings.modify.system`
challenges remain expected and distinct.

The tracked recipe now pins `gnome-keyring 48.0-1` and verifies its D-Bus
activation and user-unit files without force-starting the daemon. The next
user-built image must validate automatic boot, the graphical session,
Secret Service activation, first-time WPA secret prompting, association,
DHCP/DNS/Internet, and preservation of `usb0` SSH.

M1 REPRO v5 subsequently validated the integrated Secret Service and exposed
a duplicate legacy-autostart timeout plus an independent UPower user-namespace
failure. Their separate runtime corrections are documented in
`notes/mobian-m1-repro-v5-hardware-validation-2026-09-05.md`.
