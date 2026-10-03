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
