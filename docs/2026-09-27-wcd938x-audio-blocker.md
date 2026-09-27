# WCD938x SoundWire audio blocker — 2026-09-27

## Observed result

On Xiaomi `lmi`, AVC video playback was functional and the MP4 contained an
AAC audio track, but no audio output was heard. This separates working video
playback from the still-unproven AAC decode path and the downstream audio
output path.

PipeWire and WirePlumber were active, but the only exposed sink was `Dummy
Output`. ALSA exposed no sound card or PCM device; `/dev/snd` contained only
`timer`. Thus userspace had no hardware-backed ALSA endpoint to route to.

At the kernel/DSP layer, ADSP and Q6 were active and the TFA9874 amplifier was
detected. The WCD938x SoundWire RX slave was identified at
`0xd01170224`, but it did not reach `ATTACHED`. The observed
`swrm_get_logical_dev_num` path retained `-EINVAL`; WCD938x probe/bind failed
and the ASoC card remained in deferred probe. This is the first demonstrated
blocker before ALSA card registration, and explains why PipeWire had no real
sink to expose.

## Interpretation and limits

The SoundWire `clsh` state is a strong indication of an incomplete link or
attachment sequence, but it is not itself a demonstrated direct cause of the
`-EINVAL`. The exact condition that leaves the slave unattached is not yet
established.

An absent or unsuitable UCM2 profile would matter later, after a sound card
and PCM endpoints exist, for selecting a usable codec route. It does not
explain the current absence of an ALSA card, so adding UCM2 is not the next
diagnostic step.

The test boot was the D-repro D-v43 image with recorded SHA-256
`0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad`.
However, the exact kernel source commit, build configuration and DTB
provenance corresponding to the running binary have not been demonstrated.
Local candidate DTS material is not sufficient proof of binary/source
identity. No kernel patch is proposed or included; a speculative DT or driver
change would not be justified by the present evidence.

## Next discriminating experiment

Before changing the kernel or device tree, instrument the exact source/build
that can be proven to correspond to the running boot. Capture the SoundWire
slave state transitions, the readiness check and inputs to
`swrm_get_logical_dev_num`, its exact return path, and the WCD938x probe result.
Correlate that trace with the live RX-slave node and its supplier, reset,
clock, regulator and pinctrl readiness. This should establish why the slave
does not become `ATTACHED`; only then should a minimal correction be selected.

## Evidence provenance

The local private diagnostic directory was
`/home/linuxagent/dv43-openrc-reconstruction/audio-diagnostic/lmi-audio-kernel-investigation-20260927/`,
whose sanitized evidence manifest had SHA-256
`24cbb2127e2dbfb9665d7a395008fc1a32d3c9f6703138c9ce0fed9575d6c308`.
This path is provenance for the original workstation only; the evidence
directory is not part of this repository and need not exist after cloning.
This repository stores only this summary, not the full logs, DTB, full DTS,
binary dumps, identifiers or secrets.
