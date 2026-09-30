# `daily-base-audio-fw-test` experimental profile

This experimental profile is a copy of the validated `daily-base` behavior,
plus one firmware-path preparation for the TFA9874. It does not modify
`baseline-nochange`, `time-seed`, or `daily-base`.

Hooks `10` and `20` reproduce `daily-base`: initialize the root-only UTC
time-seed from the build host; disable only Chatty daemon autostart through
the user XDG `Hidden=true` override. Chatty remains installed and manually
launchable. The package install/remove lists and time-seed overlay are copied
unchanged from `daily-base`; the verifier checks this equivalence.

Hook `30-install-lmi-tfa-firmware.sh` requires the separately exported host
input `inputs/vendor-firmware/tfa98xx.cnt` (510 bytes) with SHA-256
`07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9`. The
builder temporarily stages that verified input inside the copied rootfs; the
hook never reads `/vendor`. It places the file at
`/lib/firmware/postmarketos/tfa98xx.cnt`,
`root:root`, mode `0644`, and verifies the destination hash. There is no
download or versioned firmware binary. The input is private, excluded from Git,
and must be exported once from the read-only Android vendor mount before this
profile can pass preflight. An existing destination with different content or
a symlink is rejected; an already-identical regular file is accepted.

The source defaults to the ignored local path
`inputs/vendor-firmware/tfa98xx.cnt`; an external path can be supplied through
`ARCHI_TFA_FIRMWARE_INPUT`. The input file's parent directory must be mode
`0700`. No firmware bytes are versioned.

All hooks require explicit `--enable-hooks`; there are no package changes or
other declared functional differences from `daily-base`. Hardware testing
confirmed firmware loading, TFA9874 probe, ALSA card registration and a direct
speaker route. Music was audible at the lower grille but remained extremely
quiet. The profile therefore remains experimental: usable audio gain and a
finished PipeWire/UCM2 route are unresolved. This is not a claim that audio is
fully fixed.
