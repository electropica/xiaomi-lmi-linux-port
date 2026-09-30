# time-seed profile hook

The executable initializer is mandatory for this profile. The builder rejects
preflight/build unless `--enable-hooks` is supplied explicitly. It receives
`DERIVED_BUILD_EPOCH` from the UTC clock of the build host and creates the
initial root-only seed; it does not use the target chroot's clock, RTC, NTP or
network. Review the hook before authorizing it.
