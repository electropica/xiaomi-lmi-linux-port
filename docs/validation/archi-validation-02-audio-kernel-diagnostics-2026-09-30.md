# archi-validation-02 audio/kernel diagnostic progress — 2026-09-30

This record summarizes later evidence and supersedes the earlier
no-ALSA-card snapshot only for the later reset-GPIO and audio-firmware test
boots. The earlier observations remain valid for their original boot state.
The original D-repro boot remains distinct from all temporary diagnostic
boots.

## Established kernel and codec progression

The verified WCD938x reset pinctrl states used func2, although the Kona
pinctrl driver registered gpio and no func2 function. Changing only those
two DTS mux selections from func2 to gpio removed the observed invalid
pinctrl-function message. On the temporary diagnostic boot containing the
rebuilt DTB, the earlier SoundWire RX/TX clashes were absent and both WCD938x
RX and TX slaves bound.

The first reset-GPIO boot still could not register the ASoC card because
tfa98xx.cnt was not found through the active firmware lookup path. A
separate experimental userdata then made the existing TFA container
available at that path. The TFA9874 probe completed and
kona-mtp-snd-card registered, exposing ALSA PCM devices and /dev/snd.
The private container remains outside Git; its identity is recorded only by
SHA-256 07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9.

Direct PCM playback on the hardware endpoint completed technically in both
S16_LE and S24_LE at 48 kHz stereo. A longer music excerpt was physically
audible at the lower speaker grille, but extremely quiet. This validates a
working kernel-to-amplifier playback path, not acceptable acoustic gain or a
finished desktop audio route.

## Current limits

The active generic TFA container matches the TFA9874 device entry and the
speaker profile starts. The inspected container provides no vstep table, and
the driver consequently exposes no TFA playback-volume/vstep control.
Speaker-ID based AAC/GOER selection was not available in the tested device
tree/driver path, and no authenticated alternate lmi container was obtained.
These facts make speaker-specific tuning a plausible explanation for the low
output, not a demonstrated cause. Device calibration values and container
payload bytes are intentionally omitted.

PipeWire/UCM2 routing remains unfinished. PipeWire has not been shown to
provide a usable final user-facing hardware route; direct ALSA playback is
the demonstrated path. Audio is partially functional and the low acoustic
level remains unresolved.

The original boot, diagnostic boots, and userdata variants are external
unversioned artifacts. The source archive, locked config and patch hashes
used by the diagnostic recipes are documented in
[the audio-kernel recipe](../../kernel/diagnostics/audio/README.md).
Neither the diagnostic kernel nor derived userdata is claimed to reproduce
the historical boot bit-for-bit. The proprietary TFA container must never be
added to Git.

The earlier
[2026-09-27 initial blocker](archi-validation-02-audio-initial-blocker-2026-09-27.md)
remains a historically accurate record of the unattached-slave/no-card stage;
it is not the current audio status.
