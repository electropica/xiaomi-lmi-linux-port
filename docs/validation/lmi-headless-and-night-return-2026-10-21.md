# Graphical-session comparison and retained night logs — October 21, 2026

The October 20 comparison did not complete both planned five-minute phases.
It must not be reported as an energy-saving result or a peripheral exclusion.

The graphical phase completed 301.899 seconds, with 294.117 seconds actually
suspended (97.42%). Its software-counter quotient was 75.63 mA; the shadow
and raw-scale quotients were 78.98 and 97.36 mA. These are related gauge
estimates over a short post-charge interval, not calibrated electrical current.

Phosh and Phoc were absent in the following headless phase. It achieved
245.227 seconds suspended, but USB reconnection ended the phase before the
planned endpoint. Its return sample already reports USB online. That sample
is not accepted as a clean unplugged battery endpoint, and no graphical versus
headless consumption ratio is inferred. The interface was restored, the RTC
alarm cleared and the NPU recovery state absent at return.

An initial connected stop/start qualification had also exposed a session-exit
race: seeing the new processes once did not prove that the launcher would
remain active. A subsequent start was stable across four three-second samples.
The observer's restoration was updated to check continued service activity and
retry once. The restored graphical launcher remained active at the October 21
return, on the same boot. This is a protocol qualification issue, not a battery
fix or a demonstrated cause of standby drain.

## Night observation boundary

The dedicated October 20 night observer was not armed. Neither its source nor
its output log was present on the phone at the October 21 return. Therefore
there is no dedicated departure battery snapshot for that night, and no exact
overnight current, percentage loss or battery-life improvement is claimed.
The first connected return snapshot showed 84% and charging; that is not an
unplugged endpoint.

Retained kernel logs since October 20 at 20:00 UTC still provide useful wake
evidence. The bounded query returned 15,055 records, below its 20,000-record
cap. The selected transitions contain 29 gauge wakes (IRQ 438, msoc-delta)
and two USB-C-state wakes (IRQ 502). All 29 gauge wake exits have a following
deep-suspend entry. Their exit-to-next-entry monotonic gaps range from
15.628 to 15.874 seconds, with median 15.829 seconds.

These gaps establish continued return-to-suspend behavior in the retained log,
not rail power-off or electrical current. Console buffering and journald wall
timestamp reconstruction around suspension prevent treating entry/exit wall
timestamp differences as exact sleep durations. The query's first cycle can
also begin before the chosen time bound.

No new observer, alarm, power setting, build or flash was started during this
return. Private evidence is retained locally in headless-comparison-20261020
and return-20261021-private, including the incomplete raw log and its SHA-256.
