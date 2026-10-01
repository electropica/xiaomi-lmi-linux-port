# lmi UPower battery status validation — 2026-10-01

## Result and scope

A targeted UPower 1.90.9 opt-in corrects the false discharge state on the
observed downstream Xiaomi lmi kernel. The candidate compiled, passed seven
selected test functions and followed a real unplug/replug cycle on the
phone. The installed system service was not replaced or modified.

Implementation and package/rollback procedure:
[`userspace/power`](../../userspace/power/README.md).

## Problem observed

The kernel reports `Charging` with negative `current_now`, and `Discharging`
with positive current on the recorded cycles. UPower's negative-current
heuristic changes `Charging` to `Discharging`; this also produces a false
`OnBattery=true`. The patch introduces
`UPOWER_TRUST_BATTERY_STATUS=1`, preserving the reported status only when
explicitly enabled. It neither inverts current nor changes charger controls.
The absent/zero property retains existing behavior.

Primary code: [UPower v1.90.9 battery backend](https://gitlab.freedesktop.org/upower/upower/-/blob/v1.90.9/src/linux/up-device-supply-battery.c).

## Host build and simulated tests

The patch applied to the v1.90.9 source archive with zero fuzz. Sources were
extracted on a Linux filesystem to retain both `UPower.xml` and
`upower.xml`; their names collide on a case-insensitive Windows filesystem.
Meson/Ninja compilation succeeded on Ubuntu WSL x86_64 with GCC 15.2,
GLib 2.88 and GUdev 238. Polkit and libimobiledevice were disabled for this
validation build, not for the proposed Debian package recipe.

Seven selected functions passed, with no failures:

- `self-test`;
- `Tests.test_battery_negative_current_status_opt_in` (seven property/state/current combinations);
- `Tests.test_battery_charge`;
- `Tests.test_battery_ac`;
- `Tests.test_battery_capacity_and_charge`;
- `Tests.test_battery_overfull`;
- `Tests.test_battery_state_guessing`.

The opt-in test includes property absent/zero/one, Charging, Discharging,
Full and both current signs. This was not an execution of the entire UPower
suite. The helper package recipe has only static/preflight validation;
its native Debian package build and tests remain pending.

## ARM64 build and private hardware test

An ARM64 candidate was cross-built with GCC 15.2 against Debian 13 runtime
libraries from the preserved package cache, including GLib 2.84.4 and
GUdev 238. Development packages came from Debian's trixie index and were
checked against its package sums. The binary requires at most GLIBC_2.34;
the phone has libc 2.41. All dynamic dependencies resolved on the phone.
This build also disabled Polkit and libimobiledevice and is not a complete
replacement Debian package.

The candidate read real hardware on a private D-Bus and private mount
namespace. A private udev database added the opt-in only for the battery.
The sysfs view was read-only. No global rule, installed service or package
was changed.

| Private configuration while charging | Battery state | OnBattery | USB supply exported |
|---|---|---|---|
| Default candidate behavior | Discharging | true | no |
| Battery status opt-in only | Charging | false | no |
| Opt-in plus virtual USB scope System | Charging | false | yes |

The third test changed USB scope only inside the candidate's namespace.
The real kernel's scope remained Device. This distinguishes explicit USB
export from OnBattery inference: the status opt-in alone corrected
OnBattery in this observed charging state.

## Physical cycle, without virtual USB scope

The autonomous collector recorded 80 samples at two-second intervals:

| Phase | Samples | First-to-last sample duration | Kernel status | Candidate state | OnBattery |
|---|---:|---:|---|---|---|
| Plugged in | 10 | 18 s | Charging | Charging | false |
| Unplugged | 44 | 86 s | Discharging | Discharging | true |
| Plugged in again | 26 | 50 s | Charging | Charging | false |

All sampled candidate states matched the kernel status. No latency below
two seconds is claimed. The battery was around 90 percent. Full state was
tested in simulation, not reached in this physical cycle. Collection used
monotonic time because the phone's civil clock was incorrect.

The collector ended normally. Private processes, bus, mounts, candidate
binary and helper scripts were removed. The original UPower service remained
active, with its original behavior. Raw logs remain private and are not
published.

## Remaining limits

- Build, validate and deploy the full Debian ARM64 package while preserving
  Debian's Polkit, libimobiledevice and existing service configuration.
- Validate an explicit, phone-local activation rule and package rollback.
- Recheck the physical cycle after persistent activation, then Full.
- Correct explicit USB scope representation separately if required.
- Investigate FG profile failure: the observed boot still falls back to OTP
  after errors -6/-61, reports Unknown Battery and zero design capacity.
  The learned full-charge figure is not evidence of physical battery wear.
- Validate suspend/resume before enabling autosuspend. Recorded discharge
  with autosuspend disabled is not a deep-standby autonomy measurement.

The current golden and derived-image identities remain unchanged. No
kernel build, firmware change, charging-parameter write or persistent
installation is claimed by this validation.
