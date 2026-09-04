# Mobian M1 REPRO v5 hardware validation — 2026-09-05

**GNOME KEYRING AND UPOWER RUNTIME CORRECTIONS VALIDATED**
**PERSISTENT RECIPE REQUIRES REBUILD AND HARDWARE REVALIDATION**

Target: POCO F2 Pro / Redmi K30 Pro (`lmi`) with the downstream D-v43 kernel.

## Tested artifact

- source commit: `593676f Integrate validated Phosh Wi-Fi secret service`
- Android sparse userdata:
  `Mobian-M1-REPRO-v5-userdata-phosh-4G.android-sparse.img`
- SHA-256: `b4adb244c686dcbbc1c10cce9087c792f69b8410080995893336ddd1f6a3f142`

## GNOME Keyring startup timeout

The package's systemd user service successfully started
`gnome-keyring-daemon` before GNOME Session. Its three legacy XDG autostarts
for `secrets`, `pkcs11`, and `ssh` then ran in the `PreDisplayServer` phase with
`X-GNOME-Autostart-Notify=true`. Each `--start` process discovered the existing
daemon but did not register as the client awaited by GNOME Session. Session
startup therefore paused for about 90 seconds and reported that all three
applications had failed to register before timeout.

Complete per-user overrides adding only
`X-GNOME-HiddenUnderSystemd=true` were tested on a clean boot. GNOME Session
then started in about 120 ms with no keyring registration timeout. The keyring
daemon service and socket remained active, `org.freedesktop.secrets` had a real
D-Bus owner, and the previously validated GUI Wi-Fi PSK path remained
available. The recipe implements the same semantics deterministically in the
three installed global entries; it does not remove them or manually start the
daemon.

## UPower startup timeout

After removing the keyring delay, Phosh still waited twice for the 25-second
D-Bus activation timeout of UPower. The Debian `upower.service` explicitly has
`PrivateUsers=yes`. systemd 257.13 attempted
`setup_private_users(PRIVATE_USERS_SELF, ...)`; D-v43 returned `EINVAL`, so
systemd exited at step `USER` with status `217/USER` before executing
`/usr/libexec/upowerd`.

A device-specific runtime drop-in containing only:

```ini
[Service]
PrivateUsers=no
```

started UPower successfully. Its process remained active, owned
`org.freedesktop.UPower`, and exposed the expected D-Bus object. All other
Debian sandbox directives remained unchanged. This validates only the
userspace service startup; detailed battery recognition remains open because
UPower did not recognize several downstream power-supply types and the kernel
has separately reported an unsupported battery property.

## Combined clean boot

With both runtime corrections, `gnome-session-manager@phosh.service` started
at 30.839 seconds and completed at 30.961 seconds. UPower started at 31.356
seconds and acquired its D-Bus name at 32.132 seconds. Phosh reported ready in
1.65 seconds and its service completed startup at 32.727 seconds; the physical
lock screen appeared around 40 seconds.

The active graphical session remained a Wayland `Class=user` session on
`seat0`; touch and passcode unlock worked. A short Power-button press woke the
locked display. GUI Wi-Fi and PSK entry remained functional. The remaining
failed `getty@tty1.service` is outside this milestone because D-v43 has no VT.

Open work not addressed here includes French OSK layout, detailed battery
recognition, colored clear-KMS rectangles, GPU acceleration, modem/SIM and
locked-screen power-off behavior. No Wi-Fi profile or credential is recorded
in this note or the recipe.

## M1 REPRO v6 follow-up

The subsequent v6 image, freshly built from commit `d054ba8`, reproduced both
corrections from the tracked recipe. It removed both startup delays while
preserving UPower, the Secret Service and GUI Wi-Fi secret entry. See
`notes/mobian-m1-repro-v6-hardware-validation-2026-09-05.md`.
