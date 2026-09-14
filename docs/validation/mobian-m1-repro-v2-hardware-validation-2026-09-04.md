# Mobian M1 REPRO v2 hardware validation — 2026-09-04

Image tested:

```text
Mobian-M1-REPRO-v2-userdata-phosh-4G.android-sparse.img
sha256: c2495b55daf77fdefff213cc64d37eab2101b52fea7d0ca0b96c43310b9af23a
```

## Display and Phosh

Linux and USB SSH started, and `/dev/dri/card0` plus DSI-1 existed, but the
screen remained black. The source tree used for the image still contained an
older `lmi-splash-release.service` with `Requires=` and `After=` dependencies
on `dev-dri-card0.device`. The real character device existed and udev knew it,
while the synthesized systemd device unit remained inactive and timed out.
This blocked splash release, seatd, and Phosh.

Starting the splash unit once with dependencies ignored succeeded, followed by
successful starts of seatd and Phosh. DSI-1 activated; the French Phosh lock
screen, touch, swipe-up, passcode unlock, and desktop all worked. This proves
the image's display/Phosh payload works, but automatic graphical startup in
this image is defective. The next recipe explicitly installs the already
corrected M0 splash unit and retains only the bounded character-device wait.

Phoc intentionally turned DSI-1 off after idle without crashing. Calling
`org.gnome.ScreenSaver.SetActive false` on the real mobian user D-Bus woke the
panel. Libinput also reported touch event-processing delays of approximately
29--72 ms; occasional slow swipe and passcode input remain a performance issue
to investigate.

## Wi-Fi and time

All tracked low-level WLAN units passed automatically through WLAN interface
creation. The tested image lacked `wpasupplicant`, causing NetworkManager's
supplicant D-Bus activation to fail. Runtime installation of
`wpasupplicant 2:2.10-24` and its Debian dependencies enabled scans, WPA2
association, DHCP (`192.168.4.121/24`), gateway and DNS (`192.168.4.1`), and
successful access to the configured Debian, security, and Mobian repositories.
USB SSH remained available.

The image had no NTP client and an incorrect RTC. Runtime installation of
`systemd-timesyncd 257.13-1~deb13u1`, followed by enabling NTP, synchronized
successfully with the Debian pool. This does not correct the underlying RTC.

## Deliberately unresolved

- A broad temporary Polkit rule allowed user `mobian` to control all
  NetworkManager actions and proved CLI radio off/on, but it did not repair the
  Phosh Wi-Fi button. It is not part of the recipe. The system-launched Phosh
  process is not associated with a conventional active logind session.
- UPower fails before starting `upowerd`: its unit requests
  `PrivateUsers=yes`, and D-v43 returns `EINVAL` while systemd creates the user
  namespace (`217/USER`). The kernel also logs an unsupported battery property.
  No UPower workaround is included without a separate runtime validation.
- Audio, GPU acceleration, and remaining quick-settings controls are not
  validated by this milestone.
