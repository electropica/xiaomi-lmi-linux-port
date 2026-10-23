# Guarded esr-delta quiet-resume candidate

Status: source patch and host policy fixture checked; package/device validation
pending. No claim of lower physical standby current. MiniMax found no blocker;
its restart/artifact-check suggestions were independently reviewed and addressed.

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

On a rerun, an already-patched source is first reversed to the pinned baseline
in temporary staging, checked, then patched forward again. Source/changelog
states must match. Rollback versions/architectures are checked. New packages
must have unchanged file/type/link lists and correct version/architecture.
The two policy binaries must differ from their rollback binaries and contain
the exact new ESR reason; both executable hashes are included in the receipt.
This is an artifact guard, not a substitute for package and device tests.

The fifteen-second grace is defined in plugins/power/gsd-power-constants.h,
now separately pinned. The900second timeout is a runtime setting, not changed
by this patch. Hash coverage remains limited to the two policy files,13home8
files and that constants header; unrelated source-tree drift is not exhaustively
audited. Installation must still use the four named deliverable packages only.

If preparation is interrupted with only one source changed, the bounded staging
check deliberately stops rather than guessing a rollback. Inspect source and
changelog hashes before retrying; do not remove guards or rerun old home recipes.
Source hashes in the final manifest still require review: the manifest is a
guard against accidental drift, not independent authentication of its author.

After any future installation, confirm normal UI/manual wake and then observe
a natural exactESRwake, preserving unknown/combined/critical wake behavior.
If that wake does not occur in a bounded observation, the test is incomplete.
Never inject an IRQ or change calibration to manufacture acceptance.

## Additional qualification-helper check

The native host test test-resume-guards-host.py extracts the actual old/new
reason and qualification helpers. Across403200input combinations it checks
that patched445has the existing441semantics and every other reason retains
its old result. It covers the opt-in/locked/clock, GSD peer/blank/activity/sleep
flags, duration boundaries, USB, capacity/status and read-failure fixtures.
Both components pass. This is a differential pure-helper check, not event-loop,
D-Bus timing, package or handset validation. It makes no power-saving claim.
