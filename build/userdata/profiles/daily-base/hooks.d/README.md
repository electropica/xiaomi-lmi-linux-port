# daily-base hooks

Hooks execute as root inside the copied target rootfs with networking disabled.
This profile requires the explicit `--enable-hooks` opt-in. Hook `10` creates
the host-UTC time seed and enables its units; hook `20` creates a user XDG
autostart mask for only the Chatty daemon. Review both before building.
