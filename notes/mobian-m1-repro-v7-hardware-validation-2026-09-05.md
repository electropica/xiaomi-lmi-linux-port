# Mobian M1 REPRO v7 hardware validation — 2026-09-05

**HARDWARE VALIDATION PASSED; FRENCH INPUT DEFAULT NOW IN RECIPE AND AWAITS REBUILD**

Target: POCO F2 Pro / Redmi K30 Pro (`lmi`) with downstream D-v43.

## Tested artifact

- source commit: `d054ba8 Integrate validated M1 startup fixes`
- Android sparse userdata:
  `Mobian-M1-REPRO-v7-userdata-phosh-4G.android-sparse.img`
- SHA-256: `3b514d386b486137d8c730a0c6f1e970f1aa10116720669f9b66d920902d1015`
- userdata flash: PASS
- D-v43 boot: PASS

No generated image is stored in Git.

## Preserved M1 functions

The lock screen, touch, passcode unlock, USB SSH, GUI Wi-Fi, GNOME Keyring
Secret Service, UPower with `PrivateUsers=no`, active Wayland logind session on
graphical `seat0`, and NTP synchronization after network availability passed.
The former Keyring registration timeout, UPower D-Bus timeout and systemd user
namespace failure were absent. `getty@tty1.service` remained the only known
failed unit and is non-blocking on this `CONFIG_VT=n` kernel.

Approximate visual timing was clear-KMS near 20 seconds, loading logo near 40
seconds, and lock screen near 50 seconds.

## Measured critical path

`systemd-analyze critical-chain` reported:

```text
phosh-m0.service @23.830s
└─user@1000.service @22.991s +836ms
  └─systemd-user-sessions.service @22.968s +16ms
    └─network.target @22.963s
      └─NetworkManager.service @22.578s +383ms
        └─lmi-wlan-on.service @10.802s +11.773s
          └─lmi-cnss-fs-ready.service @2.737s +8.061s
```

Thus WLAN initialization was on the real path to Phosh on this boot via
NetworkManager, `network.target`, `systemd-user-sessions`, and `user@1000`.
This corrects the earlier analytical assumption that Wi-Fi was merely
parallel. The display branch completed separately:
`lmi-splash-release.service` started at 2.140 seconds, ran for 3.260 seconds,
and released `seatd.service` at 5.404 seconds. Clear-KMS was a visual marker,
not the critical branch. `user-runtime-dir@1000.service` took 64 ms.

No ordering or timeout was changed as part of recording this evidence.

## Dynamic battery evidence

Initially, battery and BMS sysfs capacity were 100%, while UPower reported
100% and fully charged. After about 39 minutes physically unplugged, both
sysfs capacities were 95% and `current_now` was `-449706`. UPower reported
95%, discharging, `on-battery=yes`, about 2.03 W energy rate and approximately
six hours to empty.

This validates changing capacity, discharge reporting, battery/BMS data and
their UPower/D-Bus exposure to Phosh. It does not resolve two downstream
inconsistencies: battery sysfs still reported `status=Charging`, and USB sysfs
reported `present=1` and `online=1` while physically unplugged. Reconnection,
the charging transition, return from 95% to 100%, and low-battery behavior are
not tested.

## French input-source experiment

The existing `fr_FR.UTF-8` locale still yielded:

```text
org.gnome.desktop.input-sources sources = [('xkb', 'us')]
```

and Squeekboard was QWERTY. Setting that key for `mobian` to
`[('xkb', 'fr')]` changed Squeekboard immediately to AZERTY. After a complete
reboot and a new `fastboot boot` of D-v43, without reflashing userdata, the
AZERTY setting persisted.

This proves the setting causally and on hardware. The tracked recipe now uses
a textual GSettings schema override and compiles the schema during image
construction. It deliberately does not import the experimental user's dconf
database. A fresh image must still validate that the default is delivered to
a newly created `mobian` profile.
