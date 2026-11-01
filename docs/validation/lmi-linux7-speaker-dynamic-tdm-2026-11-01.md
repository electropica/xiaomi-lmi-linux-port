# Linux 7 LMI speaker playback with dynamic TDM

On 1 November 2026 the user confirmed audible speaker playback after booting
kernel `87b9b647919418e0951cf3345cff60f0cb5dfcdd2f30e009547db7abc760bef8`
with `tfa98xx.pcm_sample_format=3` added to the Linux 7 command line. The
previous boot with the same kernel and static mode 0 produced no audible sound.
The Android boot image prefix read back as SHA-256
`cb6aeee9727dc39226c4be8ed9e77ec343c7adcc7d7ad1e7ab6e5fc996b59216`.

Before the change, PipeWire's sink monitor carried nonzero audio and ALSA
reported 48 kHz, stereo S16_LE. The TFA9874 configuration read 0x20=0x2890,
0x21=0xc1f1 and 0x22=0x043c. After mode 3, the module parameter read back 3
and the same configuration registers read 0x0890, 0xc0f1 and 0x043c.
These correspond to the driver's dynamic 16-bit TDM framing; the codec
profile and the kernel Image were unchanged. This is an observed improvement,
not a measurement of physical I2S signals.

The phone retains the existing permanent menu and rescue entries. Do not assume
all audio features, capture, headset, suspend/resume or charging are validated
by this speaker playback test. Future Linux 7 menu bundles must retain the
argument in `kernel/experimental/linux7/configs/lmi-audio-bootargs.txt`.
The repository bundle builder adds it automatically and rejects conflicts;
other menu builders must preserve it explicitly. The
community driver warns that container TDM settings may override dynamic mode,
so changes to the installed TFA container require revalidation.
