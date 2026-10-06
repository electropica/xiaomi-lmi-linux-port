# Gauge-wake resuspend trial - 2026-10-06

The operator explicitly approved a bounded unplugged test. The temporary
root service waited for unplug, armed a 720-second RTC end alarm and observed
resume causes. It would request suspend only for the exact inspected
438 msoc-delta wake, USB offline, capacity at least 20%, six seconds without
touch/button events, and no blocking sleep inhibitor. Input values were
discarded and never logged. No persistent settings or Wi-Fi state changed.

## Completed trial: the policy was not exercised

The test ran 720.075 seconds; CLOCK_MONOTONIC also advanced 720.075 seconds.
No suspend/resume event occurred. There were zero resuspend requests and no
call errors. Counter loss was 20,911 uAh (104.544 mA derived mean), which
describes awake idle here and must not be compared as a deep-suspend result.
The service completed with Result=success and ExecMainStatus=0; its RTC
alarm was empty afterward. Charging resumed, with capacity at 80%.

Postflight found sleep-inactive-battery-timeout=900 seconds (15 minutes),
longer than the 12-minute trial. The protocol incorrectly relied on automatic
initial suspend and did not test its intended condition. No battery fix or
wake-policy validation is established by this run.

Executed preparation source SHA-256:
830a58f115d0875a8850bb30f49691acaa286127c8032574d4b7349cc7b037b4.
Raw numeric logs remain private.

## Corrected diagnostic source prepared before the follow-up

The [reusable diagnostic](../../userspace/power/diagnostics/gauge-resuspend-trial.py)
now explicitly requests initial suspend after USB-off, input-quiescence,
capacity and inhibitor checks, rather than changing the permanent idle timeout.
It uses a ten-minute RTC cap, rejects stale wake state, repeats activity/cable
checks immediately before a gauge resuspend, and handles interruption cleanup.
Its seven policy guard cases pass and Python compilation passes. These
additional protections and initial-suspend path were not present in the
completed trial; hardware validation was pending at preparation time. The diagnostic
is not enabled or included in the production installation.

## Corrected hardware trial completed

After renewed readiness and unplug confirmation, the corrected trial ran
601.378 seconds. CLOCK_MONOTONIC advanced 7.088 seconds, leaving approximately
594.290 seconds of system-suspend time. Counter loss was 17,643 uAh, giving
a fuel-gauge-derived mean of 105.615 mA. Kernel logs confirm deep entry at
05:54:51 CEST, gauge wake at 06:04:15, deep re-entry at 06:04:22 and final
RTC wake at 06:04:52. One resuspend request followed the observed gauge wake
after 6.037 seconds; there were no call errors.

The transient service finished successfully with exit status 0 and was
inactive afterward. Its RTC alarm was empty; charging resumed at 82%, with
battery temperature 24.0 C. No permanent idle, Wi-Fi, charge, gauge or thermal
setting changed. The diagnostic monitor reads independent input queues without
grab and discards all input values; none are stored or published.

This validates one guarded gauge-wake return to deep suspend. It does not
establish that every possible wake is handled correctly or validate permanent
deployment. Remaining consumption is still high despite roughly 98.8%
suspend occupancy. This result is not a controlled paired comparison with
the earlier approximately 94 mA measurement; no current-saving claim follows
from comparing them. Reducing the awake wake interval has not resolved the
residual deep-suspend draw. The diagnostic remains outside production startup.
