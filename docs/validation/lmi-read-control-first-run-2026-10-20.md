# First read-control run and stable-unplug qualification — 20 October 2026

## Result: no usable read-control samples

The observer was fetched after explicit operator reconnection. Source hashes
matched, boot identity was unchanged, the service was inactive with success,
the RTC alarm remained empty, the normal battery timeout was 900 seconds and
charging had resumed. Raw evidence and its SHA-256 were preserved privately.

The trace has only four events: armed, unplugged, replugged, finished. The
observed USB0 window lasted about five seconds, with zero resume attempts.
Consequently no treatment/control comparison or battery saving can be inferred.
The service's success means an orderly stop, not a successful measurement.

The kernel journal around this window confirms Type-C disconnect, a configured
USB reconnect several seconds later, and another disconnect afterwards. The
observer stopped during that brief reconnect, before the operator confirmation
of the intended unplug. This is more evidence than a lone power_supply flag,
but it does not independently identify cable movement or a connector defect.
No claim about the entire operator absence follows from this five-second log.

## Candidate correction, not a live rerun

While waiting to start, the observer now requires USB0 observations separated
by at least 20 seconds without an intervening observed USB1. A short initial
cycle is recorded and returns to waiting, with no gauge reads. The next USB0
sequence starts its own full confirmation interval. Existing awake-only polls
are reused; no timer that wakes suspended hardware or sleep inhibitor is added.
Unobserved transitions between polls remain possible. Confirmation can be
noticed only at a later awake poll if the phone suspends first.

Once observation has started, an observed reconnect still stops immediately;
no charge-contaminated current samples are accepted. Three-hour initial wait,
18-hour total bound, eight-callback cap and all read/error guards remain.
The revised runtime has 19 fake-backend tests, including replay of the five-
second initial cycle and immediate stop after a confirmed start. Together with
13 offline analyzer tests, all 32 pass on the native host. No handset install,
arming, build, charger setting or calibration change was made for this revision.

The first run remains archived; a future revision uses a distinct log/unit and
requires a fresh connected preflight. Do not rerun an old armer into old paths.
