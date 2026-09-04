# Mobian M1 REPRO v6 hardware validation — 2026-09-05

**PERSISTENT KEYRING AND UPOWER STARTUP FIXES VALIDATED ON HARDWARE**

Target: POCO F2 Pro / Redmi K30 Pro (`lmi`) with the downstream D-v43 kernel.

## Tested artifact

- source commit: `d054ba8 Integrate validated M1 startup fixes`
- Android sparse userdata:
  `Mobian-M1-REPRO-v6-userdata-phosh-4G.android-sparse.img`
- size: 1,881,808,716 bytes
- SHA-256: `b6e7c3bbb57e4edd1f17c829ded37b7c8ce94b883329d34d983cb05f44a30a00`
- build filesystem check: PASS
- Windows transfer SHA-256: identical
- sparse userdata flash: all three segments PASS, 47.451 seconds total
- boot image: `D-repro-01-boot.img`

No generated image is stored in Git.

## Persistent GNOME Keyring correction

The three recipe-transformed legacy autostarts contained
`X-GNOME-HiddenUnderSystemd=true`. The fresh boot produced no
`failed to register before timeout` message. The systemd user keyring service
remained functional, and `org.freedesktop.secrets` had a real owner with UID
1000 without any manual daemon start.

GNOME Settings displayed the Wi-Fi password prompt on this freshly flashed
image. User entry of the secret and connection both succeeded, without an
`nmcli` workaround. This validates the persistent Secret Service path. No
SSID, PSK or connection profile is recorded here or in the repository.

## Persistent UPower correction

The installed device-specific drop-in reported `PrivateUsers=no`.
`upower.service` became active and running with a nonzero main PID and owned
`org.freedesktop.UPower`. The boot contained neither `Failed to connect to
upowerd` nor `Failed to set up user namespacing`; the former `217/USER` failure
did not recur.

UPower still warned that it did not recognize several downstream
power-supply types, including Wireless, Main, BMS and Nothing attached, and
that a USB power supply lacked an `usb_type` property. Phosh displayed 100%,
which proves that a value reached the UI but not that the gauge follows
discharge. Dynamic battery reporting remains unvalidated.

## Session and timing

The significant journal events were:

- 40.987 s: listening on `gnome-keyring-daemon.socket`;
- 41.027 s: `phosh-m0.service` started;
- 41.768 s: `gnome-keyring-daemon.service` started;
- 41.839 s: GNOME Session manager starting;
- 41.957 s: GNOME Session manager started;
- 42.398 s: UPower starting;
- 43.154 s: UPower D-Bus activation completed;
- 43.659 s: Phosh ready after 1.60 seconds;
- 43.870 s: NetworkManager registered the Phosh NetworkAgent.

Logind retained the expected active Wayland user session on graphical `seat0`;
`seat0` had `ActiveSession=2` and `CanGraphical=yes`. The lock screen, touch and
passcode unlock passed.

The operator observed clear-KMS rectangles around 25 seconds, the loading logo
around 45 seconds and the lock screen around 50 seconds. The difference from
the corrected v5 runtime boot occurred before `phosh-m0.service`, so it is not
attributed to the Keyring or UPower changes without further evidence.

After GUI Wi-Fi connection, automatic network time synchronization passed.
A short Power-button press waking the locked display was observed again.

## Scope and open work

The only failed system unit observed was `getty@tty1.service`; it is outside
this milestone because D-v43 has no VT. Also open are French OSK layout,
dynamic battery tracking and detailed power-supply recognition, colored
clear-KMS rectangles, GPU acceleration, modem/SIM, locked-screen power-off and
optimization of the time before `phosh-m0.service`.
