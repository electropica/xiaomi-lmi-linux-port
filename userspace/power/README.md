# UPower battery status opt-in for the validated lmi kernel

UPower 1.90.9 overrides a battery's reported state with `Discharging` when
`current_now` is negative, except for `Full`. The observed downstream lmi
kernel uses negative current while charging and positive current while
discharging, with correct `status` transitions. This produces a false
discharge indication and `OnBattery=true` while plugged in.

The patch adds `UPOWER_TRUST_BATTERY_STATUS=1` as an explicit udev opt-in.
It preserves the reported state without changing current values. When the
property is absent or zero, upstream behavior is unchanged. No activation
rule is installed by the package recipe.

See the [hardware and simulation validation](../../docs/validation/lmi-upower-battery-status-2026-10-01.md).
The patch is based on [UPower v1.90.9](https://gitlab.freedesktop.org/upower/upower/-/tree/v1.90.9)
and is GPL-2.0-or-later. Original documentation and helper scripts follow the
repository license.

## Package build: built and deployed on the validated phone

Use an expendable Debian 13 ARM64 build environment, separate from the
phone and the locked image builders. Enable the corresponding Debian source
repositories. Acquire the exact source package `upower=1.90.9-1`, install its
build dependencies and `devscripts`, then run the recipe below. A different
base version requires a new review rather than bypassing the identity check.

The recipe retains Debian's packaging, Polkit, libimobiledevice,
introspection and hardening. It creates version `1.90.9-1+lmi1`, which must
be installed with the matching runtime library and introspection package.
Debian's rules disable automatic test execution; the simulated tests must
also be run explicitly. A successful package build is not, on its own,
equivalent to the recorded seven-test validation.

🐧 WSL / Linux — disposable Debian 13 ARM64 builder — 🏗️ Build — preparation model: GPT-6 Luna high

```sh
apt-get source upower=1.90.9-1
/path/to/xiaomi-lmi-linux-port/userspace/power/scripts/build-upower-package.sh --check ./upower-1.90.9
/path/to/xiaomi-lmi-linux-port/userspace/power/scripts/build-upower-package.sh ./upower-1.90.9
```

`--check` is read-only and starts no build. Build mode modifies the supplied
source tree. Generated `.deb` packages and build trees stay outside Git.
The temporary validation binary disabled Polkit and libimobiledevice: it
must not replace the installed Debian service permanently.

## Installation and rollback procedure

Before installation, verify the package architecture, version, dependencies
and enabled features. Preserve/download the currently installed versions of
`upower`, `libupower-glib3` and `gir1.2-upowerglib-1.0` for local rollback;
do not rely on their continued availability from the mirror. Keep the SSH
session and USB connection during installation. No kernel/boot rebuild or
flash is required for this userspace change.

Install those three matching local packages with APT so dependency checks
remain active. Deploy an activation rule only on the individually validated
phone, after reviewing its kernel and battery driver. The following rule is
a local opt-in template, not a rule to distribute or enable on other phones.
It requires an explicit marker at `/etc/upower/lmi-trust-battery-status` and
matches only the battery supply below the downstream SMB5 device. The marker
must not be added to a generic image.

📱 SSH — validated Xiaomi lmi only — 🛠️ Local udev rule content — preparation model: GPT-6 Luna high

```udev
SUBSYSTEM=="power_supply", KERNEL=="battery", KERNELS=="*qpnp-smb5", TEST=="/etc/upower/lmi-trust-battery-status", ENV{UPOWER_TRUST_BATTERY_STATUS}="1"
```

Store the reviewed rule as `/etc/udev/rules.d/99-lmi-upower-status.rules`.
Create the empty marker only when deliberately enabling this validated
quirk, reload the rules, trigger only the battery supply and restart UPower.
Before and after restart, compare kernel `status`, `current_now`, USB
`online` and UPower `State`/`OnBattery`. Repeat the unplug/replug cycle and
check `Full` when reached. The full package and this persistent rule were
installed and validated
with a physical cycle on 2026-10-03. See the
[deployment record](../../docs/validation/lmi-battery-audio-torch-2026-10-03.md).
Full/low-battery behavior and a rollback execution remain untested.

For rollback, remove only the added rule and marker, reload rules, trigger
the battery supply, reinstall the preserved original versions of all three
packages together using APT's explicit downgrade support, and restart
UPower. Confirm that no opt-in property remains in the battery's udev
database. If it remains, remove the previously applied property through a
temporary, battery-scoped removal rule and trigger it before deleting that
temporary rule. Do not overwrite other UPower configuration or service
drop-ins. Confirm the original service is active and its package versions
match the preserved baseline.

This correction does not load the missing FG battery profile, calibrate
capacity, enable suspend or change charger parameters. With the opt-in,
`OnBattery=false` was obtained while charging even though the USB supply
remained unexported. A separate USB scope correction is still needed for
explicit representation of that supply; it was not applied here.

## CPU idle opt-in — 2026-10-03

The running diagnostic boot passes `lpm_levels.sleep_disabled=1`; the live
parameter is `Y`, blocking non-default cpuidle selection. A controlled unplugged
comparison reported 208.4 mA awake idle with zero C1 entries, then 100.8 mA
with 831 C1 entries after setting it to `N`. Deep suspend succeeded and still
reported 97.2 mA. This is evidence of an awake-idle improvement, not a complete
fix for deep-suspend consumption or fuel-gauge accuracy.

The opt-in helper and service are limited to the exact tested kernel release.
They retain the previous runtime setting and restore it on service stop.
Installation does not alter boot cmdline, kernel or battery charge parameters.
The service requires `/etc/lmi/cpu-idle-opt-in`; the marker is local and must
not be included in generic images before wider validation. No automatic
integration into the next image builder is made by this patch. Runtime USB remained functional and the operator confirmed touch, music and
volume controls. The phone-local service is installed, enabled and active;
its stop/start rollback was tested. Long-run and reboot validation remain
pending. Install the helper as `/usr/local/sbin/lmi-cpu-idle` and the unit
as `/etc/systemd/system/lmi-cpu-idle.service`, with the explicit local marker.
Disable/stop the service to restore the saved parameter. No charge current,
capacity-learning data or thermal protections are modified.

A subsequent private tracefs collection recorded 121.761 seconds of deep
suspend without new failures, with APSS/ADSP asleep almost throughout
and approximately 96.2 mA reported consumption. Static DDR counters
do not identify a memory-power fault; the residual consumer remains
unresolved. The trace instance was removed after reconnect. A subsequent
unplugged inspection confirmed USB runtime suspend and its power domains
disabled; an always-on boost/shared GPIO is a review lead, not a proven cause.


## Finite runtime observation

`scripts/watch-battery-runtime.py` logs selected battery/USB sysfs properties,
suspend counters, boottime/monotonic timestamps and the CPU-idle parameter to
a new private JSONL file. It refuses an existing output and bounds duration
and sampling interval. No wake alarm is created; the sleep pauses during
system suspend, so samples can be delayed until a normal resume. It does not
change charge, display, suspend or regulator policies. Keep logs outside Git.

A six-hour, ten-minute-interval observation was started on the tested phone
after the peripheral-idle test. Its first sample showed Charging, USB online,
95% capacity and `sleep_disabled=N`. This is an active observation, not a
completed long-run validation. Samples spanning charging and unplugged use
must be separated; coarse polling cannot locate every transition exactly.


## Latest long unplugged observation - 2026-10-06

The daytime charge-history interval fell from 97% to 55% in 10.97 hours,
about 3.83 percentage points/hour, with approximately 95.9% deep-suspend
occupancy and no reboot. Conditions were not a controlled Wi-Fi experiment.
Autonomy is not fixed; the bounded gauge re-suspend trial is not permanently
installed. See the [existing observation record](../../docs/validation/lmi-battery-overnight-2026-10-06.md)
for sample boundaries, charge-at-inspection and remaining uncertainties.


Read-only follow-up found the same always-on GPIO-5 boost declaration in all
12 on-phone OEM-style DTBO entries, with that GPIO also assigned to the haptic
supply. PCIe L1/L1SS enable bits are set; no simple disabled-ASPM configuration
was found. These facts do not identify the residual current consumer or validate
a hardware change. See the [existing boost candidate record](../../docs/validation/lmi-boost-diagnostic-candidate-2026-10-06.md).


### Battery diagnostic follow-up - 2026-10-06

The active 416-byte J11 battery-profile payload matches OEM-style DTBO entry 7
exactly. This does not independently validate battery health or gauge calibration.
A separate [power debugfs candidate](../../kernel/diagnostics/power/README.md) is prepared for inspecting
clock/regulator summaries, retaining the reset-GPIO audio correction. It is not
Kconfig-validated, built or booted; no hardware policy or durable boot was changed.
Residual deep-suspend consumption remains unresolved.
