# Incremental gauge-read control — October 20, 2026

## Result

All eight natural-resume probes completed without read or timing errors:
four counter-read bursts and four direct-current control bursts, in the
predefined T/C/C/T/T/C/C/T order. Every recorded wake reason was `msoc-delta`.
For each probe, both `current_avg` and `current_now` were numerically identical
before and after its middle read sequence: all eight within-probe deltas were
zero for each channel.

| Middle read sequence | Valid probes | Filtered-current delta, each probe | Direct-current delta, each probe |
|---|---:|---:|---:|
| Software/shadow/raw counters | 4 | 0 uA | 0 uA |
| Three direct-current reads | 4 | 0 uA | 0 uA |

Filtered pre/post spans were 1.21–2.99 ms. Direct-current spans were
2.12–11.16 ms. The result supplies no evidence of an immediate numerical
change caused by the extra counter reads at these sampling times. It does
not rule out delayed effects, effects common to both arms, or gauge update
latency exceeding the probe duration. Both arms already read SRAM through
their common filtered-current getter; this is not a no-SRAM comparison.

Filtered samples decreased from 59.320 to 49.849 mA across the observation;
direct samples ranged from 47.851 to 51.269 mA. The first higher filtered
sample and subsequent drift must not be attributed to treatment order. SOC,
temperature and capacity scales were not recorded by this candidate, so this
is not a context-matched integrated current or battery-life comparison.

## Observation and cleanup

The observer detected stable USB-off over approximately 25 seconds and
retained the normal 900-second inactivity policy. Its stable-unplug-to-finish
window was 4,775.628 seconds, approximately 79 minutes 36 seconds. It stopped
at its eight-callback cap, before the later operator-confirmed reconnect;
therefore it does not identify the physical reconnect time or observe the
entire interval until that reconnect. No RTC wake was scheduled.

After explicit reconnect, the log was fetched once and its SHA-256 checked:
`21958321701ffabe9b72f635cbef1ae0e50c4386f5091c8c7f8c6432ac345f86`.
The same boot was retained. The observer was inactive with Result=success,
the phone was charging, timeout was 900 seconds, Wi-Fi remained enabled,
RTC wakealarm was empty and no NPU recovery state remained. The JSONL stream
was structurally complete, with no parse error or truncation indicator.

## Battery-authentication follow-up

A separate source audit found bounded startup/retry workers and a conditional
activity path outside them. With the inspected configuration, BMS change
uevents can enumerate authentication-related properties. ROM-ID, chip-status
and status getters can then perform actual one-wire transactions; reading
the authentication-result property itself returns cached state. This does
not establish a periodic transaction source while unplugged.

After reconnection, a bounded query inspected 2,695 retained kernel journal
rows spanning arm through the observer's finish. It found none of the selected
ROM transaction/getter, chip getter, status collector, verification or reset
failure message patterns. Only counts/timestamps were retained; no device
identifier, page payload or authentication material was published. Absence
of these messages does not establish absence of all calls or physical load:
some source messages use debug logging, build correspondence is bounded and
unlogged paths remain possible. No authentication getter was called for this
check and no policy was changed.

## Decision

The narrow immediate read-perturbation hypothesis has no supporting change
in this run. Repeating the identical probe overnight is not justified without
a different predicted effect or evidence gap. No residual-drain fix follows
from this result; distinguish it from calibrated physical current and from
the [grouped software-isolation observation](lmi-minimal-scope-result-2026-10-20.md).

See the [getter review](lmi-read-control-getter-review-2026-10-20.md) for the
source-level limits of the treatment/control contrast.
