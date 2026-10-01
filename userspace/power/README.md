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

## Package build: prepared, not yet executed or installed

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

## Installation and rollback procedure: pending package validation

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
check `Full` when reached. This persistent rule and the full package have
not yet been validated on hardware; the completed test used a private
udev database and private D-Bus, leaving the installed service unchanged.

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
