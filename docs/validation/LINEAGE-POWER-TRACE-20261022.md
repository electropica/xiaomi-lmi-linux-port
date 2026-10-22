# Lineage power trace and unplug-counter discontinuity, 2026-10-22

## What was observed

After explicit operator unplug/replug, a dedicated Android trace instance recorded
46 available power events: device PM callbacks, regulator transitions, clocks,
CPU/cluster idle, PM QoS, wake sources, Wi-Fi PM and RPMh commands. No energy
policy was changed and no periodic userspace reader ran while unplugged. The
32-MiB rolling RAM buffer used the boot clock. Snapshot trigger was unsupported.
The instance was stopped, saved privately and removed before any boot operation.

The interval is 30m44.775s on battery with 20.348s battery uptime (~98.9% asleep).
Regulator and callback events are present. CPU0/1/2 overwrote 151119 early events;
commit-overrun/dropped-event counts are zero. The maximum per-CPU oldest timestamp
defines a common retained suffix. All four retained machine_suspend windows are
inside that suffix; their emitted sleep-bank commands are complete for this
comparison. This does not recover every earlier device preparation event.

Each of the four windows contains the same twelve sleep-bank RPMh address/value
pairs as retained Mobian trial36. Active/wake requests are not asserted identical.
This narrows the search for a difference in APSS sleep requests; it does not
exclude every regulator, remote-master vote, peripheral state or physical loss.

machine_suspend begin/end have equal trace timestamps: the clock advances only
during syscore_resume. Treating those endpoints as zero physical sleep would be
wrong. Hardware sleep counters and BatteryStats independently show long sleep.
The entry-to-restored-clock intervals include resume overhead, not pure residency.

## Correction to the initial 26-mA overnight statement

The first live return read was already charging (96%). History preserves 95%
before charging. During the night, the counter changes from 2676 to 2590 mAh at
the exact same unplug timestamp: an 86-mAh logical discontinuity. Later precharge
history reaches 2472 mAh over 30685.759 s. After excluding that discontinuity,
the net quotient is 118 mAh / 8.524 h = 13.84 mA; summed downward changes are
134 mAh / 8.524 h = 15.72 mA, with 16 mAh upward corrections. The previously
quoted 223-mAh aggregate includes the unplug discontinuity and return-boundary
effects. It must not be presented as 26 mA of calibrated physical standby draw.

The traced short trial repeats this pattern more strongly: 2676 to 2498 mAh at
the same unplug timestamp (178 mAh), then 2498 to 2491 mAh over 1801.492 s
(13.99 mA net), still displaying 100%. Its raw 186-mAh discharge total is dominated
by the immediate counter jump. The agreement of later quotients is useful but
they remain one gauge's rounded software history, not an independent sensor.

No claim is made that the entire Mobian residual is a gauge artifact. A matched
Mobian comparison must exclude equivalent discontinuities and use the same
post-unplug counter path before attributing the difference to hardware policy.
Raw histories, trace data and identifiers remain private. Android clock was
corrected before this short trial; the old overnight calendar date was wrong,
but its internally consistent elapsed interval is preserved.
