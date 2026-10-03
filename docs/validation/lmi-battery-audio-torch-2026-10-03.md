# lmi battery, speaker and torch validation — 2026-10-03

These are changes deployed to the running phone, not new golden userdata or
boot identities. The phone clock lagged the operator's date; durations and
sample counts are used below rather than treating phone wall time as exact.

## Battery service deployment

The full Debian 13 ARM64 packages `upower`, `libupower-glib3` and
`gir1.2-upowerglib-1.0`, version `1.90.9-1+lmi1`, were built from Debian's
`1.90.9-1` source with the canonical opt-in patch. Polkit, libimobiledevice,
introspection and Debian hardening remain enabled. Seven selected integration
tests passed in the ARM64 build environment under umockdev with proc mounted:
negative-current opt-in, charge, AC, capacity/charge, overfull, state guessing
and online-AC properties. Debian disables automatic tests in its package
rules; this was a separate explicit test run.

A private full-package hardware check preceded installation. The original
three Debian packages were retained privately for rollback. The installed
service then used the documented battery/SMB5-scoped udev rule and explicit
marker; USB supply scope was not changed. A real unplug/replug collection
recorded 90 observations: 65 Discharging/State=2/OnBattery=true,
24 Charging/State=1/OnBattery=false, and one transient
Not charging/State=5/OnBattery=false. The current-sign workaround therefore
works in the installed service, not merely in a private test binary.

This fixes state interpretation. It does not establish capacity accuracy,
recognize the missing fuel-gauge profile, or prove acceptable autonomy.
Battery inactivity suspend is locally enabled after 900 seconds; AC stays
awake. Notification screen-wakeup triggers were locally disabled for the
long test. Suspend counters grew by 104 successes without new failures;
frequent resume IRQ 438 (`msoc-delta`) remains under investigation. USB-attached
suspend had failed twice, while an unplugged timed deep-suspend test worked.

## Speaker through the user audio service

The temporary reset-GPIO diagnostic boot remains required, with SHA-256
`43132d1ad4a73728e3e4408ff3570d7693d43bc45bbc9ab9945880e1d1ae2638`.
The proprietary TFA container stays external; no calibration suitability is
claimed. Direct ALSA playback using a signed 32-bit frontend and S24_LE
backend produced recognizable, clear music, confirmed by the operator.

The opt-in user PCM in `userspace/audio/files/lmi-speaker.asoundrc` converts
to S32_LE at 48 kHz stereo. ALSA control hooks temporarily select S24_LE
on the backend and enable the MultiMedia1 route, preserving/restoring both
controls on close. The matching PipeWire drop-in exposes `Haut-parleur lmi`.
It was installed in the active user's configuration on PipeWire 1.4.2.

An initial raw-file PipeWire test produced no sound and terminated too soon;
it is not a successful validation. The same signed-32 signal wrapped in a
standard WAV then streamed for ten seconds through PipeWire and the operator
confirmed it worked. The lower-speaker sink was the default. After idle,
backend format returned to S16_LE and route to off/off, with no active streams.
No UCM2 profile, microphone, headset or durable diagnostic boot installation
is validated. The source-level Q-format explanation remains a hypothesis
supported by these format-dependent results, not a complete acoustic study.

The private music excerpt and full logs are not published. The reference
10-second signed-32 raw payload is 3,840,000 bytes with SHA-256
`cdfcd974ac1b0d0259c6f86cb25f563f38b1abc8f5fa27868231eac9a7e03fa3`.
An earlier malformed sign-extension test is excluded from conclusions.

## Graphical torch

`userspace/apps/files/lmi-flashlight.py` uses the active user's logind session
`SetBrightness` interface for the `flashlight` LED. Value 20 selects 20 mA
per torch channel in the downstream driver; zero switches both off.
A supervised 15-second test was visibly confirmed. The installed graphical
application's Allumer and Éteindre buttons were both confirmed functional.
Both switch brightness values were subsequently checked at zero.

The application switches off on normal close and after 180 seconds while
its process runs. There is no independent crash watchdog; unexpected process
termination is not claimed to guarantee automatic extinction. No global
sysfs permission change or passwordless sudo rule is required.

## Camera boundary

Megapixels is installed, but a usable capture pipeline is not established.
The downstream request-manager/sync video nodes are not a standard image
capture device. The existing camera-blocker record still applies; installing
another frontend alone is not demonstrated to solve it.
