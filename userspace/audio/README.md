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
