# Quiet-gauge grace v4 source candidate — October 20, 2026

Status: reviewed source candidate, not an ARM package or deployed policy.

## Concrete target

The latest completed observation contains seven closed natural gauge-resume
gaps of 15.226–15.387 seconds, totaling 107.515 seconds before the next sleep
preparation. The candidate optionally shortens the existing temporary-idle
restoration timer; it does not add a second forced-suspend timer or disable
gauge interrupts. The default and ordinary visible wake/AC paths retain their
15-second duration. Strict decimal opt-in values from 2 through 15 seconds
are accepted through `LMI_GSD_QUIET_GAUGE_GRACE_SECONDS`.

The existing paired quiet-resume opt-ins and qualification gates remain:
locked/blank state, actual prior sleep, no real activity, disconnected USB,
and the existing qualified gauge reasons. The IRQ 441 discharge/capacity
guard and USB-cycle correction are preserved. A requested two-second GLib
seconds timer is not a target timing guarantee.

## Asynchronous correctness prerequisite

The exact v3 source still had an unguarded asynchronous logind inhibitor reply.
A private D-Bus fixture reproduced an obsolete FD being installed when its
reply was deliberately delivered after release. This forced ordering is not
evidence that it occurred on the handset.

Shortened-grace operation therefore uses generation-tagged inhibitor requests
and a manager reference through completion. Release invalidates pending
generations, obsolete replies close their FD, and failure clears only the
current pending request. Independent review found an additional shutdown
case; shutdown now invalidates pending guarded requests before closing an
arrived FD and clearing the proxy. A dedicated real-FD test covers late reply
delivery after this shutdown helper.

## Source and validation

- Exact v3 source SHA-256:
  `3a776734c398cd88f64ef62116c5b6e1f1ada5165abd6f20b2fd8507e0f31fe2`.
- Candidate source SHA-256:
  `d762d7a696864ec6e355f788e9ec2793d4c3dfbec7c8677194660bdb1bd4317e`.
- Incremental patch SHA-256:
  `14ffad57f193bf76e47e4ed47c2d8ed26989405cf115bbeee79eb58d2e9322f9`.
- Exact-base patch application reproduces the candidate source.
- Actual-function policy fixtures pass: default/2/15 parsing, input, USB,
  state restoration and IRQ 441 conditions.
- Private-GTestDBus tests pass six FD ordering/lifetime/shutdown scenarios.
- Independent source review resolved the shutdown finding; no remaining
  actionable blocker was found in the reviewed scope.

These native checks do not replace a complete ARM package build, actual
logind/session scheduling, on-device interaction tests or energy measurement.
The proposed package version is `48.1-1+lmiquietgauge4`. Existing v3 rollback
packages were verified present. The incremental user-run build script has
source/version/architecture guards, shared build locks, no APT/network setup,
a private proc/devpts mount namespace and two compilation jobs. No kernel or
full image build is needed. No package was built or installed autonomously.

## Interpretation and next gate

This targets avoidable awake time after natural gauge resumes. It does not
explain or establish a reduction of current during actual deep sleep. Before
an overnight trial: build the ARM package, stage verified v3 rollback, verify
the unchanged default, then qualify the opt-in shortened path and normal
input/USB/power-button behavior. Do not silently enable an unqualified
candidate immediately before an unattended night.

Parallel source audits of retained kernel differences, configuration,
Android initialization, firmware, debug/secure peripherals and fingerprint
control found no additional demonstrated residual-drain fix. In particular,
the Goodix driver does not normalize inherited GPIO state at probe, but the
available pin/ownership snapshots do not demonstrate that it consumes the
residual current. No blind GPIO or secure-subsystem shutdown is justified.

See the [completed read-control result](lmi-read-control-result-2026-10-20.md)
and the [grouped isolation result](lmi-minimal-scope-result-2026-10-20.md).

[Reviewed incremental source patch](../../kernel/diagnostics/power/userspace/gsd-quiet-gauge-grace-v3-draft.patch).
