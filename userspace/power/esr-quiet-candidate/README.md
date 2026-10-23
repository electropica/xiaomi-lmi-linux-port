# Guarded esr-delta quiet-resume candidate

Status: source patch and host policy fixture checked; package/device validation
pending. No claim of lower physical standby current. MiniMax review is pending.

The October23 temporary-kernel test recovered the expected FG profile but an
esr-delta wake took the ordinary screen-on path. This candidate extends the
existing guarded msoc-high reason gate to exact445esr-delta in BOTH Phosh and
GSD. It retains fresh noncritical Discharging checks, USB/user/unknown-event
guards and existing fifteen-second grace. It changes no kernel IRQ, ESR
calibration, battery protection, capacity or boot menu. Kernel work retains
its own wake controls. No direct hardware writes are performed by the recipe.

Files: esr-delta-accept.patch; identity.json with both source identities and
13preserved home8 files; build-packages.py. The current source/changelog versions
and old rollback package presence are checked. The build uses the retained
arm64 chroot and private proc/devpts/shm mounts, reuses existing object trees,
removes only the two known debhelper build stamps and runs package tests.

Preflight only:

```sh
python3 /home/linuxagent/xiaomi-lmi-linux-port/userspace/power/esr-quiet-candidate/build-packages.py
```

After review, the OPERATOR may launch the potentially long package build:

```sh
sudo python3 /home/linuxagent/xiaomi-lmi-linux-port/userspace/power/esr-quiet-candidate/build-packages.py --execute
```

No package build, phone installation or full image/kernel build occurs in
default mode. Final marker is ESR_QUIET_PACKAGES_BUILT; four package hashes and
a receipt are written under the retained chroot build directory. Old packages
are not removed. Package versions add +esrquiet1 to qualified home8/quiet3.

If preparation is interrupted with only one source changed, the bounded staging
check deliberately stops rather than guessing a rollback. Inspect source and
changelog hashes before retrying; do not remove guards or rerun old home recipes.
Source hashes in the final manifest still require review: the manifest is a
guard against accidental drift, not independent authentication of its author.

After any future installation, confirm normal UI/manual wake and then observe
a natural exactESRwake, preserving unknown/combined/critical wake behavior.
If that wake does not occur in a bounded observation, the test is incomplete.
Never inject an IRQ or change calibration to manufacture acceptance.
