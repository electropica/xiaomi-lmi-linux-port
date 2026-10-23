# Battery evidence review — October 23, 2026

This review supersedes stronger exclusions in the preceding MiniMax notes.
The dualboot menu is now installed and read-back verified; its independent
status is recorded in docs/status/MOBIAN-STATUS.md. No battery-policy change
or new battery experiment was made for this review.

## What was independently checked

A separate parser re-read the original retained Android trace and the
embedded Mobian trial36 trace. Four complete Android machine_suspend windows
inside the retained common-CPU suffix were compared with one complete Mobian
window. All twelve apps_rsc SLEEP commands matched in value, order and
multiplicity in every pair. The differences at 0x50000, 0x50004 and 0x50014
are in the WAKE group, not the SLEEP group. Android 0x50000 alternates between
0x60124a6f and 0x6024ca6f; the compared Mobian WAKE value is 0x60003f55.
The earlier prose misattributed one of these values to Android.

The slot classification is derived from the retained exact rpmh-rsc.c
allocation loop and kona.dtsi: apps_rsc ACTIVE slots0-1, SLEEP2-4, WAKE5-7;
CONTROL allocates no slot. The replay script accepts local capture paths and
does not contact the phone. Its sanitized results are kept beside this note.

This result concerns the observed apps_rsc programming in those windows.
It does not prove the trigger, hardware state, absence of retained demand,
current electrical load, or equivalence of every current-build path. A WAKE
value difference is not evidence of a SLEEP bandwidth vote difference.

## Conclusions that remain open

* The firmware output exposes APSS and ADSP in the retained Mobian snapshots.
  Other masters are unreported. Their absence is not proof of physical
  shutdown, and it does not by itself establish why a SMEM lookup is absent
  or fails. Driver-supported record names do not prove record availability.
* High sleep residency constrains the recorded master's residency. It does
  not establish zero subsystem consumption or rail voltage.
* A common gauge driver, battery and arithmetic capacity ratio do not prove
  equal gauge configuration, learned state, operating-point behavior or a
  calibrated counter scale. A simple constant arithmetic normalization may
  cancel under equal assumptions; that does not exclude all gauge effects.
* Matching observed rail requests and SLEEP programming does not exclude all
  kernel policy, peripheral demand or unobserved masters. The conclusion
  that only firmware or an external measuring instrument remains is too
  strong for the available coverage.
* The prior audit already distinguishes BCM commit/valid and x/y fields.
  Resolving the resource name for an absolute address is a separate task;
  absence of a complete address map must not erase an existing field or
  bank decoding. No new address-to-device attribution is asserted here.

The overnight result independently checked earlier is approximately46.96mA
in gauge-counter-equivalent units over its qualified endpoint interval, with
approximately95.10% recorded suspension. Those units are not a calibrated
physical current. The slope changes with the retained observation interval.

## Next useful work

No repeated master_stats unplug experiment is justified merely to rediscover
missing records. A one-shot read during a future already-planned Android boot
could establish record availability there. Before a new energy experiment,
use the same endpoint qualification and distinguish sleep, wake and charging
transitions. Preserve all unresolved gauge and peripheral branches until a
specific discriminating observation is available.

## Provenance and limits

Private captures remain outside Git. Source SHA256 values in the sanitized
replay identify the exact retained inputs without publishing their contents.
Historical full traces are referenced through their hashes, not uploaded.
No handset contact, build, API request or hardware measurement was performed
for this review. The reviewed MiniMax work is retained with the corrections
above; it is not represented as an independently proven physical diagnosis.
