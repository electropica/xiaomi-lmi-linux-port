# Audio userspace status

The preserved host-only kernel recipes and patch provenance are documented in
[audio kernel diagnostics](../../kernel/diagnostics/audio/README.md); the
later reset-GPIO, ALSA-card, and weak-output results are summarized in the
[dated kernel diagnostic record](../../docs/validation/archi-validation-02-audio-kernel-diagnostics-2026-09-30.md).

The experimental `daily-base-audio-fw-test` userdata profile supplies an
external, SHA-locked TFA9874 firmware container to the active firmware lookup
directory. The proprietary container is not stored in this repository.

On the reset-GPIO diagnostic boot, WCD938x RX/TX and TFA9874 bound, the ALSA
card registered, and direct ALSA PCM playback completed. The sound was
audible from the lower speaker grille but extremely quiet. PipeWire routing
and UCM2 remain unfinished; the current audio path is only partially
functional. See
[`audio progress validation`](../../docs/validation/archi-validation-02-audio-progress-2026-09-29.md)
and the
[`initial WCD938x blocker`](../../docs/validation/archi-validation-02-audio-initial-blocker-2026-09-27.md).

## Speaker route validated — 2026-10-03

Clear music is now operator-confirmed through direct signed-32 ALSA and the
normal PipeWire service. This supersedes the weak-output result above for
the tested route only. See the
[deployment record](../../docs/validation/lmi-battery-audio-torch-2026-10-03.md).

The optional files under `files/` are local configuration for the validated
experimental profile and temporary GPIO diagnostic boot. Install
`lmi-speaker.asoundrc` as the active user's `.asoundrc` only after reviewing
any existing configuration; install `90-lmi-speaker.conf` in that user's
`.config/pipewire/pipewire.conf.d/`, then restart their audio services.
The PCM uses card 0/device 0 and exact downstream mixer names. Do not deploy
it to another kernel/device or overwrite unrelated ALSA configuration.
ALSA hooks preserve the original controls and restore them on PCM close.
The frontend converts to S32_LE/Q31; the backend remains S24_LE. Idle
suspension closes the path after five seconds. A standard 32-bit WAV worked;
the first raw-file PipeWire attempt did not and is not counted as validation.

This is not a full UCM2 profile. Microphone/headset, volume range, and durable
kernel installation still need validation. To roll back this opt-in, remove
only these two added user files and restart the user's audio services.

## Missing-card startup handling — 2026-10-04

The speaker adapter uses `flags = [ nofail ]`: an absent ALSA card must not
prevent the entire PipeWire server from starting. Tested on the phone with
no ALSA card: PipeWire, its PulseAudio service and WirePlumber remain active,
but only Dummy Output exists and no microphone source is exposed. This is
startup recovery, not speaker/microphone validation. Re-test physical playback
on the known diagnostic boot before claiming it for this revised configuration.
See the [application checklist](../../docs/validation/lmi-app-checklist-2026-10-03.md).

## Diagnostic-boot speaker retest — 2026-10-04

After a temporary Fastboot load of the preserved diagnostic boot, the ALSA
card returned and the revised nonfatal speaker adapter loaded. The operator
confirmed ten seconds of clear music without distortion. Standard ALSA
capture produced eight seconds of data with all tested controls restored;
recognizable microphone sound and application integration remain unvalidated.
No kernel was installed durably and no microphone source was installed.
See the [application checklist](../../docs/validation/lmi-app-checklist-2026-10-03.md).

## Microphone and Recorder capture — 2026-10-04

On the same temporary reset-GPIO diagnostic boot, standard ALSA recording
captured 384,000 mono S16_LE frames at 48 kHz (eight seconds). The operator
recognized the recorded video sound during playback of an amplified preview
(gain eight, without clipping). This validates microphone capture, not the
earpiece or headset. Unamplified capture remains quiet.

The opt-in `lmi-microphone.asoundrc` fragment retains/restores eight mixer
controls and selects the OEM static `speaker-mic` route (ADC4/INP5).
Merge the fragment with the active user's existing ALSA configuration;
do not replace the speaker fragment or unrelated configuration. Install
`91-lmi-microphone.conf` alongside the speaker adapter in the user's
`pipewire.conf.d` directory. It uses mono S16_LE, 48 kHz, 1024-frame periods,
four periods, disabled mmap and a suggested `node.latency = 1024/48000`.
The latency setting is essential for the tested Qt/PulseAudio recording
path: without it, a saved test contained only 4096 frames (0.085 seconds)
despite eight seconds of UI recording. Direct `pw-record` had succeeded.
This is a tested workaround; the exact downstream scheduling defect has
not been established. No global quantum override is installed.

KRecorder 25.04.0-2 with Qt 6.8.2 needs numeric settings for this tested
WAV/PCM combination: `containerFormat=12`, `audioCodec=8`. The optional
`lmi-krecorder.conf` contains those two settings only. Merge them into the
active user's `kde.org/krecorder.conf` while KRecorder is closed; retain
other settings. Selecting the displayed `Wave File` description had instead
persisted an incompatible string and produced WMV. Other formats are not
validated. These values are version-specific; review before upgrading.

With both changes, two KRecorder trials produced 430,080 mono S16_LE frames
at 48 kHz: 8.96 seconds each. After saving and closing normally, the final
trial persisted and displayed `0:08` on relaunch. Old failed trials still
display `0:00`; the fix cannot recover their missing audio. The final trial
had peak 1463 and RMS 90.16. The initial listening reply was too weak/no
sound, but after replaying the recording the operator confirmed it was good.
An additional source-gain experiment was discarded and source volume restored
to 1.00; speaker volume remains 0.70. Earlier recognition concerned an
amplified native ALSA capture; this later confirmation concerns KRecorder. Playback and capture PCMs were both closed at idle.

The source is nonfatal when its adapter cannot open; idle suspension remains
five seconds. This is not a complete UCM2 profile and does not establish
headset, earpiece, simultaneous playback/capture, durable boot deployment,
or a rebuilt image. Remove only the microphone fragment, adapter and the
two added recorder preferences to roll back; restart user audio services.
Private recordings, screenshots, firmware and generated images stay out of
Git. The files are opt-in, not automatically added to the image builder.


## Recorder controls and normal launcher — 2026-10-04

The functional recording reported as quiet was confirmed good after replay;
the operator clarified that playback volume, not microphone gain, was too
low and set the output to 1.00. Microphone gain remains 1.00.

The default Qt theme left Recorder's Play/Pause, Stop and action buttons
without visible icons. Selecting `XDG_CURRENT_DESKTOP=KDE` only in Recorder's
process resolves the already installed Breeze icons and exposes a window
Close button. The `lmi-recorder` wrapper also retains the tested mobile and
compose input settings. Phosh and other apps retain their session environment.
The normal desktop entry keeps upstream translations and invokes the wrapper;
the app installer stages this wrapper for the next image. Audio configuration
and version-specific recorder preferences remain a separate opt-in.

On-phone checks: launch from the Phosh icon, record, usable Save/Discard
dialog with visible icons, save a WAV, and close using the visible window
button. Playback reached the fixture's eight-second duration; Back returned
to the list. Other codecs, export destinations and every edit operation
remain unvalidated. No new image was built and no session-wide theme changed.
