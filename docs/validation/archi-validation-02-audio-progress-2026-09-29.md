# `archi-validation-02` audio progress — 2026-09-29

## Established progress

The reset GPIO description for WCD938x was corrected from `func2` to `gpio`.
With the corresponding diagnostic DTB, the prior SoundWire RX/TX clash
messages disappeared and both WCD938x SoundWire slaves bound successfully.
The diagnostic boot was used temporarily with `fastboot boot`; it did not
replace the durable D-repro boot.

The experimental `daily-base-audio-fw-test` userdata makes the proprietary
TFA9874 container available at the kernel's active firmware lookup path. The
container remains private and outside Git; its identity is recorded only as
SHA-256 `07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9`.
The kernel loaded it and the TFA9874 probe completed successfully.

The `kona-mtp-snd-card` ASoC card registered with ALSA PCM endpoints, and
`/dev/snd` appeared. Direct playback through the hardware PCM was technically
successful in both S16_LE and S24_LE. The validated route is:

```text
MultiMedia1 → PRI_MI2S_RX → TFA9874 → speaker
```

Music was physically audible from the lower speaker grille, but at an
extremely low level. This establishes that the kernel-to-amplifier path can
produce output; it does not establish a suitable everyday gain or a finished
desktop audio route.

## Current boundary

Audio is **partially functional; the low output level remains unresolved**.
PipeWire does not yet expose a finalized user-facing hardware route, and a
device-appropriate UCM2 profile remains to be built. The result should not be
described as fully resolved audio.

The D-repro original boot remains the durable boot identity. The reset-GPIO
diagnostic boot, `D-repro-01-audio-swr-reset-gpio-diagnostic-boot.img`
(SHA-256 `43132d1ad4a73728e3e4408ff3570d7693d43bc45bbc9ab9945880e1d1ae2638`),
and all userdata variants are external, unversioned artifacts. This
diagnostic boot is distinct from the original boot and was only launched
temporarily with `fastboot boot`. Neither boot nor userdata is reconstructed
bit-for-bit from all source inputs by this milestone. The proprietary TFA
container must never be added to Git.

The earlier 2026-09-27 audio blocker note is retained as a historical snapshot
and is explicitly superseded for current status. No complete logs, firmware
binary, image, or private device data are included here.
