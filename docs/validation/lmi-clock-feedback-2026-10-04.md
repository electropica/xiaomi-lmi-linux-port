# Clock, timer feedback and Recorder editing — 2026-10-04

## Recorder editing

Using the installed app-only launcher and simulated touch, the temporary
four-second launcher recording was renamed through Modify, with the old
filesystem path absent and the new WAV present. Its Delete confirmation
was readable and usable; confirming removed only that temporary recording.
The previously operator-confirmed eight-second recording remained present.
The visible window Close button exited the application. Cancel/Apply in
Rename remain English; translation is secondary to these functional checks.

## Silent timer: cause and correction

An actual five-second GNOME Clocks timer expired and displayed the French
notification, but the operator heard no sound. The journal identified the
missing `org.sigxcpu.Feedback` D-Bus service for `timeout-completed`.
`feedbackd` was absent; event sounds were enabled and the sound theme existed.
Only the ALSA libcanberra backend was installed, while the validated speaker
route belongs to PipeWire/PulseAudio.

Installed from the phone's Debian trixie package metadata, transferred through
the host without enabling phone Internet:

| Package | Version | SHA-256 |
|---|---|---|
| feedbackd-common (all) | 0.8.2-1 | `5a9ca68ef25d2d7b024fec5c503f0c8d17911f08f2a99fcd02f92c899084f8ae` |
| feedbackd (arm64) | 0.8.2-1 | `f9534b42e760fb0208969280e225d70bcb340144d5bb78d8c48d53f93f7491d6` |
| libcanberra-pulse (arm64) | 0.30-18 | `552ea19cfffa8d5e85fd7447e6629daefd5289df60b5d777022a523eb9c1b326` |

Downloaded package hashes matched the phone's APT metadata; `dpkg --audit`
was empty after installation. No packages were upgraded or removed.
The feedback profile remained `full`. A second actual five-second timer
activated feedbackd, and the operator confirmed an audible alert. The only
test timer was removed: the timers setting returned to its original empty
list. The speaker PCM was closed at idle afterward.

The application installer now explicitly includes `feedbackd` and
`libcanberra-pulse` even with `--no-install-recommends`; `feedbackd-common`
is its package dependency. This prepares the next image recipe, not a new
built/booted image. Haptic feedback, alarm wakeup from suspend and alarm
delivery with the app closed are not established by this timer test.

## Clock offset without Internet

The operator reported approximately two minutes of delay. A paired host/phone
reading found approximately 85 seconds of delay, including sampling latency.
The phone used `Europe/Paris` correctly, but reported synchronization false;
timesyncd was active with packet count zero and no selected server address.
The only route was the connected USB subnet, with no Internet default route.
This explains the absence of NTP correction, not the original offset or an
RTC drift rate. The RTC reported a 1975 date; it was not changed.

The phone's system clock was aligned from the operator's Windows clock, then
saved by the existing `lmi-time-seed-save.service`. The immediate comparison
was within one second. The existing save timer remained active. This is a
host-assisted clock correction, not NTP synchronization. No Wi-Fi connection,
Internet route, RTC write, battery profile or timesyncd policy was changed.
Offline time retention and synchronization once Internet is available still
require separate validation.
