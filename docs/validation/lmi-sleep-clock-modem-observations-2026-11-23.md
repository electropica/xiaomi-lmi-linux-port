# Suspend, clocks and modem observations — 22–23 November 2026

## Scope and build state

The operator temporarily booted a Linux 7.2.12 diagnostic menu with
`clk_ignore_unused` removed from the command line. It was loaded into RAM,
not flashed. The kernel and initramfs were preserved, and the user confirmed
the Mobian desktop and audible music. The modified boot image is not promoted
as the permanent build. Its SHA-256 was
`0b7075d1ea9b9878c7c971ebc74e59304e2a516a2f537fcdaeb33226d5c3ff89`.

## Battery comparisons

Two physically unplugged Mobian sleep observations on 22 November lasted
approximately 70 minutes each and lost 12 raw MSOC ticks each. The first
post-sleep capture already reported `Charging`; the second reported
`Discharging`. The 23 November diagnostic sleep lasted approximately
83 minutes and lost 14 ticks, with its post-sleep capture already reporting
`Charging`. Dividing by 255 ticks and assuming a 2,617 mAh capacity gives
rough estimates around 105–106 mA for the first two observations and 104 mA
for the diagnostic. These are not direct current measurements: the endpoints,
radio state, gauge scaling and effective capacity limit the comparison. No
energy-saving effect has been demonstrated.

A saved LineageOS `dumpsys battery` report of 12 November lists maximum
capacity 2,617,000 and design capacity 4,700,000. It supports the provenance
of the assumed capacity; it does not calibrate Mobian MSOC or prove that
capacity remains constant across state of charge and temperature. The Android
overnight displayed percentage comparison is not an exact mA measurement.

## Trace observations

The active kernel exposes `CONFIG_FTRACE=y`, suspend callbacks, clock and RPMh
events, `pm_genpd_summary`, and `suspend_stats`. An older archived config is
not evidence of the active configuration.

A private trace captured the suspend and resume callbacks of platform
`1c10000.pcie`, root port `0002:00:00.0` and modem `0002:01:00.0`; recorded
callback results were zero. All 70 trace events were retained, with no
reported buffer loss. A separate private trace of PCIe-named clock
enable/disable/prepare/unprepare events recorded no matching clock events
around the subsequent suspend; 30 suspend events were retained without loss.
The trace clock was monotonic and does not measure elapsed sleep time.

These observations establish software callbacks and the absence of matching
events in the selected trace, not the modem's electrical state during sleep,
its current, or the absence of autonomous hardware transitions. Both traces
and their temporary hooks were stopped and removed after collection.

## Interpretation and next action

An older RPMh trace contained sleep programming but lost 15,840 events on one
CPU. An address-to-client mapping is needed before a new filtered RPMh trace
can attribute requests to the modem. A missing modem firmware message and a
historical D3cold error do not prove the modem's present sleep power state.
Avoid interpreting shared device-tree supplies as proof of a shared physical
cutoff, or a successful PM callback as proof that a rail was disabled.

An additional offline review maps the archived command-db resource `ldoa5`
to base address `0x41900`. In the older capture two active-set commands to
`0x41904` have data values 0 and 1; the trace uses a per-CPU local clock and
has substantial loss, so their cross-CPU order and completeness are not
established. The archived device tree associates the corresponding regulator
with both modem PCIe and UFS PHYs. The commands do not identify which client
released the regulator, prove its physical voltage, or establish the topology
of the currently booted DTB. Driver and active-DTB comparison is needed before
another targeted experiment can attribute a cause.
