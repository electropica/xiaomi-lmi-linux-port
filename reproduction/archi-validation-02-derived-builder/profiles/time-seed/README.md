# `time-seed` profile

This profile is a distinct, package-neutral derivative of the locked golden
userspace. It does not modify `baseline-nochange`, the kernel, `/boot`, GPU72,
Phoc configuration, identities or package versions.

The opt-in `10-initialize-lmi-time-seed.sh` hook creates
`/var/lib/lmi-time-seed/last-good-utc` as root:root mode `0600`, in a root:root
mode `0700` directory. Its epoch comes from the UTC build host at hook time,
passed as `DERIVED_BUILD_EPOCH`; no date constant is versioned. Use
`--enable-hooks` explicitly for both `--check-only` and the later build.

At boot, `lmi-time-seed.service` is pulled in by `basic.target`, after local
filesystems are mounted and before later logind/timesyncd jobs when they are
queued in the same transaction. It advances the system clock
only if the validated seed is later. It never sets the clock backward. An
already-running/enabled `systemd-timesyncd` can then discipline time when a
trusted NTP source becomes available. A timer saves the maximum observed epoch
two minutes after boot and every five minutes; `ExecStop` saves at shutdown.
Each seed update uses a same-directory temporary file, restrictive umask,
strict epoch/file metadata checks and atomic rename. No RTC write, package,
network request or password/PIN handling is involved.

This is a fallback time floor, not authenticated time. If the seed is missing
or malformed, the unit logs an error and does not guess or rewrite it; normal
boot continues and NTP may still recover the clock.

## Hardware check

The files were installed without packages and enabled on the Poco lmi on
2026-09-27. After one normal reboot, SSH returned, system UTC remained at or
above the root-only seed, both units were active/enabled, and the boot journal
contained no new PAM “password changed in future” warning for `mobian`.
`systemd-timesyncd` remained active but unsynchronized, so this check did not
depend on receiving NTP packets. The reboot began with system time already at
the seed; the older-than-seed clock-setting branch was not forced by moving a
live device clock backward.
