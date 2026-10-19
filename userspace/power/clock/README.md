# Offline wall-clock restoration without PMIC writes

On the observed lmi, the hardware RTC exposes a counter with an Android-era
offset. Linux wall time should not be copied into that PMIC counter merely to
repair the Mobian clock. NTP remains enabled, but an offline USB-only boot cannot
assume a successful network synchronization.

The helper records a **trusted** pair of UTC system time and RTC counter. At
boot, the oneshot computes trusted UTC plus the RTC elapsed seconds. It advances
a stale system clock only, never moves it backwards, and never writes the RTC.
There is no periodic process, wake alarm, network access or suspend hook.
An RTC reset, a large epoch discontinuity, invalid schema or reference older
than366days is rejected; ordinary network synchronization remains the fallback.

## Trust and per-device state

First establish correct UTC from a trusted host or synchronized NTP. Only then
run `lmi-rtc-time-anchor capture --trusted-current-time`. The flag is an explicit
operator assertion of time trust, not a verification supplied by the program.
`check` is read-only; `restore` is the boot-service action. The root-owned0600
state is `/var/lib/lmi-time/rtc-anchor.json`; do not distribute it with a generic
image or reuse it for another handset. The RTC name is not a unique device ID.

The current phone was synchronized against the host, its reference captured,
the systemd unit verified, enabled and executed successfully with no clock step
needed. The live reference check differed by less than a second. A fresh boot
through this service has **not yet been physically validated**.

## Build integration

The image recipe installs/enables the conditional service. A fresh generic
image has no trusted anchor and skips it until calibrated. For rebuilding this
same handset only, `M1_RTC_TIME_ANCHOR_FILE` can supply its private reference;
the builder validates the schema and copies it with0600 permissions. An image
without this input still includes normal NTP, but does not invent a UTC anchor.

## Validation

Run `python3 -m unittest discover -s . -p 'test_*.py'` in this folder. These pure
tests never read device nodes or set any clock. Runtime `systemd-analyze verify`
and successful oneshot execution are distinct from a future boot test. Manual
wall-clock correction happened after the recovery measurement ended; measured
suspend durations use uptime/BOOTTIME and are unaffected by that later change.

To disable this optional restoration, disable `lmi-rtc-time-restore.service`.
Neither disabling it nor removing its private anchor changes PMIC hardware time.
