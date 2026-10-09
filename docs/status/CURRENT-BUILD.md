# Current validated build and userspace state

This document distinguishes the validated Mobian userdata family from the
separate D-v43/OpenRC reconstruction and from temporary diagnostic boots.
Generated images are not stored in Git.

## Current hardware state

The `archi-validation-02` Debian 13/Mobian userdata was booted on Xiaomi
`lmi` with the D-repro D-v43 boot. Phosh was visible and usable; touch/unlock,
DSI-1, and GLES2 → Zink → Vulkan Turnip → KGSL → Adreno 650 were validated.
GNOME Console and Calculator were exercised. The original D-repro boot
(`D-repro-01-kernel-Dv43-qca6390-v2-complete-fcsource-boot.img`, SHA-256
`0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad`) is
the durable boot identity for the golden and `daily-base` validations. The
boot image embedded in userdata is a distinct artifact.

## Golden userdata: `archi-validation-02`

The external raw and Android-sparse images were verified as a matching pair:

| Form | Size | SHA-256 |
| --- | ---: | --- |
| Raw `archi-validation-02.img` | 4,551,868,416 bytes | `329e2124f97032a2f4b15167bbd9bbbd9395bb422f2794a2117ee610a2368f27` |
| Sparse `archi-validation-02.img.android-sparse.img` | 2,960,036,280 bytes | `84182b57edb7be8e49c29e0f0b472e9b6a54f7efa645ef99664dc0e004759f78` |

The sparse image was flashed as userdata and booted with the D-repro boot.
The text lock records its packages, persistent customizations, GPU72 runtime
and boot/userspace contract at
[`build/locks/userspace/`](../../build/locks/userspace/README.md).
The golden is not in Git. A bit-for-bit rebuild from all historical sources
is not demonstrated.

## Derived profile: `daily-base`

`daily-base` was derived from the golden userdata without rebuilding the
kernel. It adds the validated time-seed floor and a per-user XDG override
that disables only automatic Chatty-daemon startup; Chatty remains installed
and manually launchable.

| Form | Size | SHA-256 |
| --- | ---: | --- |
| Raw `archi-validation-02-derived-daily-base-20260927.img` | 4,551,868,416 bytes | `5cc226cd96c324b68d74e33eec461a091e7f5dd69b80e0529c2d0267cfa3cad5` |
| Sparse `archi-validation-02-derived-daily-base-20260927.img.android-sparse.img` | 2,960,466,444 bytes | `172a4f950252e810f408bf4d5caf5075c699020e6a2198999f7f0b30c7f19928` |

The raw/sparse round trip and hardware boot were validated. The images remain
external. See
[`daily-base` validation](../validation/archi-validation-02-daily-base-validation-2026-09-27.md).

## Experimental profile: `daily-base-audio-fw-test`

This separate experimental derivative adds the proprietary TFA9874 container
to the kernel's active firmware lookup path. It was tested with a distinct
reset-GPIO diagnostic boot loaded temporarily using `fastboot boot`; that
boot was not installed durably. The firmware binary, userdata and diagnostic
boot remain external and must never be added to Git.

The WCD938x/TFA9874 path now supports clear speaker music through direct
S32_LE ALSA and an installed opt-in PipeWire route (2026-10-03). A complete
UCM2 profile and headset/earpiece validation remain pending; microphone
capture and KRecorder saving were subsequently tested on 2026-10-04; see
[`archi-validation-02` audio progress](../validation/archi-validation-02-audio-progress-2026-09-29.md).

## Earlier build: `archi-validation-01` (superseded as current pointer)

The prior Android-sparse build remains a historical artifact identity, not
the current golden:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| Work ext4 | 4,294,967,296 bytes | `60de98660991379cb1d463ebadc7de43b73242d68f73502308e3891d2350844d` |
| Raw userdata | 4,551,868,416 bytes | `559d6c44f2aa2223f91fd8af1db7a838b8183d7a223ceb80f7bdd13a9b6e31e4` |
| Android sparse userdata | 2,834,813,356 bytes | `f61c19a09881c9a7ac165cc5e36ab08f146d65acddae2de18a6bb555c10663b3` |

Its two `e2fsck` validation passes completed cleanly. It is superseded as the
current userspace reference by `archi-validation-02` and its validated
`daily-base` derivative.

## Build entry points

Repository orchestrator:

    build/build-mobian-image.sh

Current Phosh/userspace builder:

    userspace/phosh/scripts/build-m1-phosh.sh

Optional application installer:

    userspace/apps/scripts/install.sh

The optional application layer is enabled with:

    INSTALL_OPTIONAL_APPS=1

## Current optional application set

The current selected optional application packages are:

- epiphany-browser
- gnome-console
- gnome-calculator
- gnome-text-editor
- papers
- showtime
- gnome-clocks
- gnome-weather
- gnome-contacts
- gnome-calls
- chatty
- gnome-calendar
- gnome-maps
- geary
- amberol
- krecorder
- koko

## GPU source state

The active GPU72 runtime is stored under:

    userspace/gpu/files/gpu72/

Its canonical source provenance is documented in:

    userspace/gpu/files/gpu72/SOURCE-PROVENANCE.md

The validated source reconstruction is upstream Mesa 25.0.7 plus the canonical
GPU72 patch.

## Important separation of concerns

The current M0/base-rootfs chain, current Phosh/userspace chain and kernel
build are separate.

The separate Mobian device workflow is not a replacement for the current
`userspace/phosh/scripts/build-m1-phosh.sh` image-production chain.

## Known deferred work

The following remain separate deferred items:

- full UCM2 routing, headset/earpiece and durable audio-boot deployment
- camera configuration and a usable downstream capture pipeline

The historical M0 Weston display validation and the later D-v43/OpenRC Weston
failures are different environments and must not be conflated.

## Battery, speaker and torch updates — 2026-10-03

The full Debian ARM64 UPower `1.90.9-1+lmi1` package and phone-local activation
are installed. Seven explicit ARM64 integration tests passed; the installed
service tracked a real unplug/replug cycle correctly over 90 observations.
Capacity accuracy and autonomy remain unresolved. Automatic battery suspend
is locally enabled; frequent msoc-delta wakes remain under investigation. A bounded follow-up
returned to deep suspend about six seconds after one gauge wake, but still
measured about 106 mA over a ten-minute interval with 98.8% suspend occupancy.
Autonomy remains unresolved; this diagnostic is not permanently enabled.
See the [guarded wake trial](../validation/lmi-gauge-resuspend-trial-2026-10-06.md).

A subsequent October 6 unplugged history interval lost 42 percentage points
(97% to 55%) in 10.97 hours, approximately 3.83 points/hour, despite about
95.9% deep-suspend occupancy. No reboot occurred; autonomy remains unresolved.
See the [October 6 observation](../validation/lmi-battery-overnight-2026-10-06.md).

The October 7 night on the temporary touch-notifier candidate again showed
substantial discharge: 99% to 66% over 8 h 51 min, approximately 3.73 points/hour,
with 96.74% suspend occupancy over the journal-covered interval. No reboot or
UPower restart occurred. A normal Wi-Fi shutdown check cleared the five
CNSS/PCIe power votes, but its suspend-current comparison was invalidated by
an early gauge wake. Autonomy remains unresolved; see the
[power diagnostic record](../../kernel/diagnostics/power/README.md#wi-fi-shutdown-isolation-and-october-7-overnight-observation).

A subsequent nearby three-minute comparison measured approximately 92.1 mA
with normal radio shutdown and 94.8 mA with Wi-Fi enabled, both above 99.6%
suspend occupancy. This single pair does not establish a stable Wi-Fi penalty;
stopping the radio did not remove the residual consumption. Both collectors
and alarms are cleaned up; the enabled-radio trace is complete.
A further three-minute trial exposed APSS/ADSP master sleep counters: they
report 99.65% and 99.95% asleep respectively while the gauge still measures
approximately 93.7 mA. This narrows the investigation but neither measures
all physical loads nor validates an autonomy fix; the complete result is in
the power diagnostic record.
A subsequent RPMh trace confirms final APSS sleep votes of zero for CX/MX/XO
and three inspected bus resources, while the gauge still reports about 94.9 mA.
These software requests do not establish all physical rail currents; the
residual discharge remains unresolved. The trial and alarm are cleaned up.






Clear speaker music was operator-confirmed through an installed PipeWire
route using the S32_LE frontend and S24_LE backend on the temporary GPIO
diagnostic boot. ALSA controls restore on close. The graphical torch app's
Allumer and Éteindre buttons were operator-confirmed. Camera capture was
blocked at this milestone; later rear-camera diagnostic progress is recorded
in the [camera record](../../userspace/camera/README.md). These are live-phone
customizations, not newly locked golden images.
See the [validation record](../validation/lmi-battery-audio-torch-2026-10-03.md).

## Next-build multilingual baseline — prepared 2026-10-03

The M1 recipe now includes core/CJK/emoji Noto fonts and all Debian locales
without requiring optional apps. Initial interface locale and XKB layout are
build parameters. Korean-interface/Turkish-document rendering is an intended
validation scenario, not yet an image/hardware result. No new image was built
and the battery-test phone was not changed. See the Phosh recipe README for
remaining input-method, runtime language selection and translation limits.

## CPU idle improvement — installed 2026-10-03

A legacy `lpm_levels.sleep_disabled=1` boot parameter blocks deeper CPU idle
between activities. A controlled test reported awake-idle current dropping
from 208.4 to 100.8 mA with 831 C1 entries after a runtime opt-in. Touch,
music, volume and USB remained functional. The phone-local opt-in service is
installed and enabled; stopping it restores the original parameter. Boot
images/cmdline and the historical golden are unchanged. Reboot and long-run
validation remain pending. Deep-suspend current still reports about 97 mA;
acceptable autonomy and fuel-gauge accuracy are not yet established. See
`userspace/power/README.md` and the 2026-10-03 validation record.

A subsequent private tracefs collection recorded 121.761 seconds of deep
suspend without new failures, with APSS/ADSP asleep almost throughout
and approximately 96.2 mA reported consumption. Static DDR counters
do not identify a memory-power fault; the residual consumer remains
unresolved. The trace instance was removed after reconnect. A subsequent
unplugged inspection confirmed USB runtime suspend and its power domains
disabled; an always-on boost/shared GPIO is a review lead, not a proven cause.


## Application checklist and Chatty incident — 2026-10-03

An inventory of 21 visible applications and one-at-a-time functional checks
is recorded in `docs/validation/lmi-app-checklist-2026-10-03.md`. Chatty
0.8.7-2 exhausted memory during camera enumeration through GStreamer and
libpurple. An isolated test excluding two video plugins stayed active at
approximately 108 MiB. The phone-local desktop/D-Bus helper was then installed
with an isolated registry and a requested 384 MiB systemd-user memory limit;
user memory delegation was checked after restart at 384 MiB and zero swap.
The operator subsequently confirmed normal opening, menu access and relaunch;
shortcut-window sizing remains defective. SMS/MMS remain unvalidated. SMS is not validated and no modem was detected. The new helper
is not automatically installed by the generic image recipe.

The restart interrupted the six-hour battery observer. CPU-idle and UPower
were active after restart, but no ALSA card was detected; previous music
confirmations apply to the temporary diagnostic boot, not this restart.


## Application follow-up — 2026-10-03

The operator's application and menu defects are preserved in the app checklist.
Koko's missing Qt/QML dependencies were installed on the test phone and made
explicit in the application recipe. Photos now has operator-confirmed image
opening, working Back navigation and no unsolicited keyboard. A bounded
standard-thumbnail-cache helper restores the gallery preview in a remote
screenshot; the lmi launcher uses the tested Zink runtime when available.
The bottom folder header, truncated labels and broader gallery functions remain
open. Helpers and dependencies are recorded in the recipe.
This is a live userspace repair, not a newly built or hardware-validated image.
No automatic rotation sensor or usable GPS was established in this follow-up.
See the [application checklist](../validation/lmi-app-checklist-2026-10-03.md).


The text editor's off-screen GTK Save dialog was reproduced. GNOME file-chooser
portal routing and a per-app launcher now give an accessible Save button.
Remote tests passed create/save, reopen, Save As, edit/save and normal close;
the operator also confirmed the Save As dialog usable by touch. Recipe and
builder staging include these userspace fixes; no new image was built.

## Runtime audio checkpoint — 2026-10-04

The inspected phone runtime exposed no ALSA card. The earlier speaker result
remains specific to the temporary diagnostic boot. Its installed opt-in
PipeWire adapter now tolerates a missing card, allowing the server to start;
Dummy Output is not physical audio. Diagnostic-boot speaker and microphone
retesting is pending. See the [application checklist](../validation/lmi-app-checklist-2026-10-03.md).

## Diagnostic-boot speaker retest — 2026-10-04

After a temporary Fastboot load of the preserved diagnostic boot, the ALSA
card returned and the revised nonfatal speaker adapter loaded. The operator
confirmed ten seconds of clear music without distortion. Standard ALSA
capture produced eight seconds of data with all tested controls restored;
recognizable microphone sound and application integration remain unvalidated.
No kernel was installed durably and no microphone source was installed.
See the [application checklist](../validation/lmi-app-checklist-2026-10-03.md).

## Microphone and Recorder result — 2026-10-04

Native eight-second capture was operator-recognized after amplified playback.
An opt-in PipeWire microphone source and numeric KRecorder WAV/PCM settings
then produced two complete 8.96-second recordings. The final saved trial
survived normal close/relaunch and displayed `0:08`. After replaying it,
the operator confirmed that the application-produced recording was good. Both hardware PCMs
closed at idle. This supersedes earlier no-source/microphone-unvalidated
observations on this diagnostic boot only. Full UCM2, headset/earpiece and
durable boot deployment remain pending. See the
[audio integration record](../../userspace/audio/README.md#microphone-and-recorder-capture--2026-10-04).

## Timer feedback and offline clock correction — 2026-10-04

A real five-second Clocks timer now gives an operator-confirmed audible alert
after adding Feedback and the PulseAudio backend to the app recipe and phone.
The timer test was removed; no rebuilt image is claimed. The phone clock was
aligned from Windows and saved using the existing seed service, because NTP
had no Internet route. Wi-Fi and battery settings were unchanged. See the
[validation and remaining limits](../validation/lmi-clock-feedback-2026-10-04.md).


Rear camera update (2026-10-05): the isolated PREVIEW backend now captures
1280 x 720 rear images with adaptive automatic exposure. The verified CVP/synx
interfaces and temporary host-visible OEM firmware segments resolve the prior
configuration failure; three fifteen-frame runs completed, including the final
consolidated sources. A privately inspected image shows the scene correctly.
The helper cleans up its links/runtime and is not installed persistently.
Live preview and Megapixels integration remain pending; video, focus quality and generic-image support are not validated.
See [automatic rear preview capture](../../userspace/camera/README.md#automatic-rear-preview-capture--2026-10-05).

An opt-in GTK rear snapshot app is now installed on this exact diagnostic boot.
Two automated end-to-end app runs saved user-owned 1280 x 720 PNGs in Images/
Camera. The app runs unprivileged; a fixed demand-started backend service has
bounded execution and a narrowly scoped local-user rule. No generic-image or
Megapixels support is claimed. Operator capture and upright portrait display
are confirmed; opening the saved photo in Photos remains pending. The HAL-based
rotation saves 720 x 1280 portrait pixels. Explicit private-manager shutdown
reduced one full UI trial from 14.610 to 10.048 seconds. Replacing fixed
startup/result pauses then yielded two successful trials at 8.625 and 8.623
seconds, including smoke-mode startup/exit delays. Per-shot initialization
and live preview remain unresolved. See [application and validation scope](../../userspace/camera/README.md#opt-in-rear-snapshot-application--2026-10-05).


A bounded rear live-preview prototype now displays successive rotated frames
without reopening the sensor. A 45-frame diagnostic returned eleven images
about 0.725 seconds apart after warmup; a separate 120-frame preview published
36 frames and stopped automatically. The normal photo button saves the displayed
frame directly; operator save-responsiveness confirmation remains pending.
The fixed early-stop action now leaves no runtime directory or CVP links.
The operator reports that preview is too slow for normal use; no PipeWire
video source is currently exposed for an alternative standard frontend. Preview is slow and limited to about 30 seconds per launch.
See [bounded rear live preview](../../userspace/camera/README.md#bounded-rear-live-preview--2026-10-05).


Preview follow-up (2026-10-05): automatic preview now works on fresh launch and
reactivation of an existing window after completion. Publishing every live
frame yielded 106 displayed frames with a mean 0.242-second interval, versus
about 0.725 seconds with every-third-frame sampling. Instrumentation measured
about 235–242 ms request/result wait and 14 ms conversion/write for published
frames. The client still submits requests serially; queued-buffer capture is
not yet validated. Operator confirmation of the visual improvement is pending.
See [cadence measurement](../../userspace/camera/README.md#preview-cadence-measurement-and-automatic-reactivation--2026-10-05).


Queued-preview follow-up (2026-10-05): automatic startup and noticeably smoother
preview are operator-confirmed. Three genuine buffers now keep requests in
flight instead of waiting serially. A rear diagnostic yielded 106 images at a
mean 0.0444-second interval; the final real-UI run displayed 423 images at a mean
0.0581-second interval (about 17 fps). Queueing stops after 25 seconds and drains
outstanding requests, under the existing outer timeout. Normal and early-stop
cleanup passed; the original snapshot path still succeeds. No kernel change.
Full-resolution stills, autofocus, video and standard-app integration remain
pending. See [queued rear preview](../../userspace/camera/README.md#queued-three-buffer-rear-preview--2026-10-05).


Foreground-preview follow-up (2026-10-05): the normal app no longer requires a
restart every 25 seconds. Preview runs while its GTK window is active, pauses
in the background and resumes automatically on return; the operator confirmed
the return path. A real session ran 137.8 seconds and published 3,034 images.
A fresh PID/start-time/UID-checked lease and watchdog replace the normal session
cap; the diagnostics retain their bounds. Background and GUI-exit cleanup tests
passed after extending the firmware wrapper teardown wait. No kernel change.
See [foreground continuous preview](../../userspace/camera/README.md#foreground-owned-continuous-preview--2026-10-05).


### Existing camera application trial — 2026-10-05

Debian Lomiri Camera 4.0.8+dfsg-5 was installed experimentally. Its Wayland/OpenGL
interface launches, but the operator and a screenshot confirmed a black
viewfinder. No photo/video was validated; the Android camera bridge is not
installed. This is not a replacement for the validated rear HAL3 preview and is
not added to the image recipe. See `docs/validation/lomiri-camera-app-installation-test-2026-10-05.md`
(repository-root-relative) for installation findings and limitations.


### Current camera status — 2026-10-06

Snapshot rear preview is experimental. The operator found the native PipeWire
preview fluid but mirrored and delayed; its measured publication rate was about
18.8 fps. The preview target is 25 real images/s. A rear-identity and fresh-file
polling correction is prepared and passes synthetic tests at about 25 fps;
rear orientation is now operator-confirmed, while visible preview delay is now confirmed. A one-minute follow-up measured
16.68 fps upstream and 16.90 fps at the native producer; sensor profiling found 60 ms exposure with a 12–30 fps range. The supported
fixed-30 fps trial reduced sensor-to-RGB age to 86.5 ms; the operator confirmed
reduced delay and adequate brightness. Preview publication reached only 19.34 fps
and production integration remains pending. Real recording has
unresolved preservation and quality defects. Megapixels was removed and the
lmi-camera prototype remains provisional. A private NEON trial reduced conversion
to 9.3 ms, but delivered only 18.81 fps. The operator estimates remaining visible
delay at 0.2-0.5 seconds; a preview queue experiment has no demonstrated gain.
A later two-buffer/10 ms polling trial reached 21.62 fps but was reported
saccadic by the operator; it remains rejected for production integration.
No camera test or recording is active.
See the [camera implementation status](../../userspace/camera/README.md) and
[complete validation record](../validation/snapshot-pipewire-rear-preview-2026-10-05.md)
for distinct operator, hardware and synthetic results.


### Battery diagnostic follow-up - 2026-10-06

The active 416-byte J11 battery-profile payload matches OEM-style DTBO entry 7
exactly. This does not independently validate battery health or gauge calibration.
A separate [power debugfs candidate](../../kernel/diagnostics/power/README.md) is prepared for inspecting
clock/regulator summaries, retaining the reset-GPIO audio correction. External-input preflight and native Kconfig checks pass. It includes the
Qualcomm idle statistics required by this source when debugfs is enabled, with
optional Bluetooth/block debug interfaces disabled. The operator subsequently built the separate diagnostic boot successfully
(54,652,928 bytes; identity in the linked record). Temporary hardware startup is confirmed by the matching live IKCONFIG hash
and readable clock/regulator debugfs interfaces. USB SSH and existing CPU-idle
service work. Short suspend/current results are documented below; no hardware
power policy or durable boot was changed.
Residual deep-suspend consumption remains unresolved.


The first debugfs-boot trial confirms approximately 181 seconds in deep suspend
through both clock accounting and Qualcomm suspend statistics. Gauge-derived
consumption remains approximately 96.4 mA; there is no demonstrated autonomy
improvement. USB power votes drop after unplugging, while PCIe/shared rails
require interpretation rather than forced shutdown. The transient trial ended,
its RTC alarm was cleared, and charging resumed after reconnection.


The revised trace trial confirms 181.26 seconds of sleep with a complete,
loss-free trace and approximately 95.63 mA gauge-derived consumption. Display,
UFS and PCIe clock-disable transitions precede machine suspend, with no nonzero
device-PM callback result. This narrows the diagnosis but provides no autonomy
fix. The transient collector and RTC alarm are cleaned up; see the linked power
diagnostic record for measurement limits and the invalidated earlier trial.


A separate touch shutdown-notification candidate has now been manually built
and temporarily started. Its live build banner and IKCONFIG match the verified
candidate; USB SSH and charging work. The first unplugged trial now shows
the expected touch suspend/resume path and 181 seconds of deep sleep. The operator
confirmed normal touch response after wake; an autonomy improvement is not
established. This covers one suspend/resume cycle only. The power diagnostic record gives its exact
identity and experimental scope; this is not a production boot update.


### RPMh observer diagnostic follow-up ? 2026-10-07

The operator manually built and temporarily booted the read-only RPMh observer
variant (54,652,928 bytes; SHA-256
`a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50`).
All 47 provider attributes, USB SSH and charging were checked. The inner builder
completed successfully despite the outer wrapper's inability to read its
root-owned status directory. A roughly 10 h 20 min uncontrolled unplugged period
still lost 37 capacity points. Kernel logs show approximately 96.54% deep sleep
between the first recorded suspension and reconnection, predominantly interrupted
by battery-gauge interrupts. There is no demonstrated autonomy improvement and
no production boot replacement. The bounded observer/trace comparisons subsequently completed, as recorded
below. See the
[power diagnostic record](../../kernel/diagnostics/power/README.md) for identity,
measurement boundaries and wrapper reporting details.


The first bounded aggregate-observer trial completed with all 47 snapshots
readable and a loss-free trace. It measured approximately 94.787 mA by the gauge
with 99.617% suspend occupancy; no autonomy improvement is established.
Pre-suspend supply requests must be reconciled with late suspend transitions:
L17 is explicitly disabled and L12 receives a zero sleep-enable request.
The collector, trace instance and RTC alarm are cleaned up; Wi-Fi is enabled
and charging resumed. The power diagnostic record contains the consumer mapping
and remaining limitations. The instrumented radio-off comparison subsequently completed: four Wi-Fi VRM
sleep-enable requests are zero, yet the gauge still reports approximately
93.135 mA with 99.612% suspend occupancy. L5/L6 receive low-power-mode commands;
L17 is disabled before machine suspend. Wi-Fi was restored and the collector,
trace and alarm cleaned up. No autonomy fix is demonstrated. Reported 2,822 mAh
full capacity and cycle count one are gauge state, not verified physical health;
the operator confirmed the original battery. See the diagnostic record for the
charge-counter scaling and measurement limits.

The constructor's private-status reporting issue has a host-validated fix:
16 metadata cases and a newly prepared observer preflight passed without a
kernel build. Existing diagnostic images and historical prepared recipes were
not modified; interactive sudo and a full manual build remain to be retested.
The subsequent approximate powered-off comparison returned at the same 88%
reported charge. Charging and boot/Fastboot intervals were not quantified, so
this does not establish zero off-state drain or physical battery health. No
autonomy fix is established.
See the power diagnostic record for return-measurement and kernel-identity limits.

The next-build optional application recipe no longer installs the abandoned
Megapixels package. Snapshot is still a separately tested diagnostic application,
not a production camera replacement in this recipe. No image was rebuilt and
no live-phone package was changed by this recipe correction.

M1 now stages the Recorder launch wrapper required by the optional-app installer.
A host-only dependency-closure check first reproduced the missing-file failure,
then passed all seven staged app inputs after the correction. No image or live
phone was changed. The checker is under `userspace/apps/scripts/`.


### Persistent diagnostic baseline installed — 2026-10-07

The operator selected the existing reviewed RPMh observer image for persistent
boot installation, avoiding another build/version. Its 54,652,928-byte artifact
hash is `a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50`.
The operator flashed only `boot` and rebooted successfully. Post-reboot
verification confirms that its image-size prefix matches the selected RPMh
image, the running banner is dated 2026-10-07 05:27:54 UTC, and IKCONFIG SHA-256
is `c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`.
All 47 RPMh observer attributes are present; USB charging and CPU idle work.
The gauge recognizes `j11sun_4700mah`, with design 4,700 mAh and learned full
2,822 mAh. This is not a new autonomy validation. Display/touch confirmation
remains an operator check. The original D-repro remains the rollback image. The newly prepared guarded FG observer and lookup/retry fixes are
excluded from this chosen image and must not be reported as active. See the
[power protocol](../../kernel/diagnostics/power/README.md#reuse-of-the-existing-reviewed-kernel--2026-10-07).


### Persistent-kernel overnight result — 2026-10-08

The first return after the night reported 69% versus the previous plugged-in
100% baseline. Running and installed RPMh kernel identity remained confirmed,
with no intervening restart supported by boot-time progression. The journal
records 96.808% deep suspend between the first and last overnight suspend
markers, with 61 `msoc-delta` and one `msoc-high` wake reports. Approximate
counter-derived consumption is 94.089 mA over 8.666782 hours between readings;
charging at both ends and the unknown exact unplug time prevent treating this
as a controlled current measurement. No autonomy fix is established. See the
[power record](../../kernel/diagnostics/power/README.md#overnight-return-on-the-persistent-rpmh-baseline--2026-10-08).


### Test handset temporarily switched to LineageOS — 2026-10-08

The operator installed official LineageOS 23.2-20261007-NIGHTLY-lmi, Android 16,
for an idle-drain comparison. The ZIP SHA-256 is
`c182c6f8ed1ccb1821be38e764e189f3d58f65dd9bea8aa21f1381c791395a29`;
the matching recovery SHA-256 is
`211cdc50ae40a9ecbcc35fa91ee81a54fcb02af7b49b77e8623a357f9984f7b3`.
Both downloaded files were verified. The operator explicitly chose installation
without a snapshot of the current Mobian runtime. The installer replaces boot,
Android dynamic partitions, dtbo and vbmeta images; the earlier permanently
installed RPMh image is no longer the running test-handset kernel. Existing
Mobian artifacts and Git history remain available, but exact runtime restoration
has not been established. No new Mobian image was built.

The first short Android idle comparison suggests lower drain but is preliminary.
See the [single power decision summary](../../kernel/diagnostics/power/README.md#current-decision-summary--2026-10-09)
for grouped results and the distinction between charging return samples and
pre-charge battery-history events. The longer Android interval is complete: 29 min 41 s on battery, displayed
83% unchanged before charge, about 98.5% system suspend and 5.35 mAh summed
gauge decreases reported by Android. An upward gauge correction prevents a
reliable net endpoint-current estimate. This supports lower apparent Android
idle drain, not a physical battery-health verdict. Radios are restored and the
one-shot reminder is paused. Detailed logs remain private.


### LineageOS overnight comparison completed — 2026-10-09

The same-boot, radios-off overnight interval lasted 8 h 37 min, with displayed
charge falling from 100% to 91% before reconnect. Pre-charge history gives
283 mAh net loss (about 32.8 mA); Android's sum-of-decreases statistic gives
289 mAh (about 33.5 mA). Upward gauge corrections, cooling and baseline timing
limits remain explicit in the [single power decision record](../../kernel/diagnostics/power/README.md#completed-android-overnight-result--2026-10-09).
About 99.54% system-suspend occupancy and lower apparent drain than historical
Mobian trials are supported, without a physical battery-health verdict or an
identified autonomy fix. The finite collector completed, its private data was
retrieved, and original radios were restored. The handset remains on LineageOS;
no Mobian build, restoration or new kernel was performed.

The hourly review refines this overnight result: approximately 71% of net
counter loss occurs in the first two hours, with about 12.4 mA net gauge
accounting over the remaining 6 h 37 min. This is not uniform physical idle
current. See the [counter interpretation and limits](../../kernel/diagnostics/power/README.md#overnight-discharge-is-not-uniform).
The subsequent operator-requested comparison completed after 13 h 29 min.
No periodic diagnostic logger was used.

### LineageOS daytime comparison completed — 2026-10-09

The same-boot, radios-off interval lasted 13 h 29 min, with displayed level
100% to 94% before charging. Net rounded gauge loss is 150 mAh (~11.1 mA);
Android counts 188 mAh decreases (~13.9 mA), with positive corrections retained.
System-suspend accounting is about 99.62%. Original radio settings were
restored and verified. This reinforces lower apparent Android idle drain,
without a physical cell-health verdict or a demonstrated Mobian fix. See the
[single power decision record](../../kernel/diagnostics/power/README.md#completed-android-daytime-result--2026-10-09).
The handset remains on LineageOS; no Mobian restoration or new build occurred.
