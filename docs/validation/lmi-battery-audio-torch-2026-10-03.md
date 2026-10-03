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

## MP3, MP4, volume controls and Chinese filenames — 2026-10-03

The operator confirmed normal MP3 and MP4 playback and working hardware
volume buttons. These confirmations extend the previous PipeWire WAV test;
the private songs/videos and their personal titles are excluded from Git.

`fonts-noto-cjk` version `1:20240730+repack1-1` was installed on the phone.
Because phone DNS failed, the official Debian package was downloaded on the
host and checked against the phone's APT metadata before local installation.
The package SHA-256 is
`f5dc28a754e17327d99f0a612134d92c8dd6187314ae967cb77f25df60860139`.
Fontconfig selected CJK families; the active user's font cache was rebuilt.
A new GTK window displayed the exact Chinese filename characters with both
default and explicit Noto fonts. The existing Files process initially still
showed incorrect glyphs; after a normal quit/relaunch, the operator confirmed
correct Chinese names in Files. The optional-app installer now includes the
font package, without modifying the external golden image or its historical
lock. Existing applications may need relaunching to refresh their font maps.

## Controlled battery idle/deep comparison — 2026-10-03

A finite phone-local collector waited for USB unplug, sampled awake idle,
then requested a 120-second RTC-timed deep suspend. The successful suspend
counter increased from 106 to 107 with failures unchanged at 2; RTC IRQ 323
caused resume. Kernel suspend timing reported 121.224 seconds asleep.

Over the measured 30.077-second awake-idle interval, the reported charge
counter fell from 1,434,830 to 1,433,005 uAh: approximately 218.4 mA average.
Across the 121.423-second before/after-suspend interval it fell to 1,429,556
uAh: approximately 102.3 mA average. Capacity stayed at 53%. These averages
come from the downstream fuel gauge, not an external current meter. The
comparison includes transition overhead and does not establish long-term
runtime. The immediate post-unplug negative-current sample was transient;
the settled unplugged samples had positive current and Discharging status.

The live battery type now reads `j11sun_4700mah`, nominal capacity 4,700,000
uAh, learned full capacity 2,845,000 uAh, and resistance ID 99,900 ohms. The
boot log reports authentication retries; the exact driver includes fallback
profile selection, so this name alone is not proof of authenticated battery
identity or correct learned capacity. Earlier unknown-profile observations
must not be treated as the current live value. No charge parameters, fuel-
gauge learning data or battery IRQ wake controls were changed in this test.

Debugfs is disabled in this kernel. Readable RPMh master and DDR residency
statistics exist in sysfs; a before/after controlled comparison is still
needed before attributing the residual consumption to a hardware domain.
