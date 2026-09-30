# daily-base-audio-fw-test hooks

Hooks execute as root inside the copied target rootfs with networking disabled.
This experimental profile requires the explicit `--enable-hooks` opt-in. Hooks
`10` and `20` reproduce the validated `daily-base` time-seed and Chatty
autostart behavior. Hook `30` consumes a separately exported, private host
input (default `inputs/vendor-firmware/tfa98xx.cnt`, override
`ARCHI_TFA_FIRMWARE_INPUT`; 510 bytes, SHA-256
`07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9`). The
input directory must be mode `0700`. The builder verifies it, stages it
temporarily in the copied rootfs, and removes that staging path after the
hook; the hook never reads `/vendor`. It installs
only `/lib/firmware/postmarketos/tfa98xx.cnt` as `root:root`, mode `0644`. No
package or downloaded binary is added. The firmware input stays outside Git.
Review all hooks before building.
