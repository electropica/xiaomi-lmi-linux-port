# Paired master-stat availability — October 23, 2026

The operator booted LineageOS and then returned to Mobian on the same lmi.
Both snapshots were connected and awake. The same shell-reader SHA256,
`b5e0afd0df759a0fd4b7bb6a350a72d602268c8c49ba82d2ce16cfb6a4589ba8`,
read `/sys/power/rpmh_stats/master_stats`, the sysfs path created by the
retained exact `rpmh_master_stat.c` driver. Earlier candidate debugfs paths
were not the correct interface and their missing output was not a firmware
availability result.

| Observed interface | Mobian a5b3099017ae | LineageOS 71b13e62f057 |
| --- | --- | --- |
| Reported master names | APSS, ADSP | APSS, ADSP, CDSP, SLPI, SLPI_ISLAND |
| SSR CDSP and SLPI labels | OFFLINING | ONLINE |
| SSR NPU label | OFFLINING | ONLINE |
| NPU power attribute | off | off |

The additional Android records are available on this hardware. This supersedes
the stronger statement that firmware inherently provides only two records on
the phone. The driver omits a record when its SMEM lookup returns NULL or an
error; the output alone does not identify the underlying reason. Differences
in subsystem initialization and firmware operation remain a hypothesis to
review against the precise drivers and Android startup path.

ONLINE does not mean continuously drawing active power: the NPU power attribute
is off despite its Android SSR label. The retained Android CDSP and SLPI
last-entered timestamps also exceed their last-exited timestamps, a condition
the driver treats as an ongoing sleep when printing accumulated duration.
Those cumulative counters do not provide a paired interval residency or an
electrical current. Mobian's missing records do not prove either power-off
or an excessive load. No firmware was started or stopped for this comparison.

Android did not list debugfs among its registered filesystems and had no
`/sys/kernel/debug` mount point. A temporary read-only mount attempt failed
before changing mounts; no mount was left behind. Therefore its modem GPIO
values are unavailable and must not be compared as low/zero. The Mobian
handshake levels remain an awake-only observation.

No unplug, forced suspend, new measurement window, build, flash or power-policy
change occurred. Android debugging was elevated using its already-authorized
ADB root facility. Raw outputs and script/output hashes remain private.
The pending independent review is scoped to CDSP/SLPI initialization, with no
device access, and must distinguish a reporting difference from a causal load.
