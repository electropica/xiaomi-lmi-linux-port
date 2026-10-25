# Offline gauge recheck — 25 October 2026

No handset contact, kernel/package build, installation or power-policy change.
The current passive night remains undisturbed; preserve its capture first
after the operator explicitly confirms reconnection.

## Known retry defect, not a new battery cause

The ADC shadow-read retry boundary error was already reproduced and documented
on 7 October. The separate candidate remains
kernel/patches/diagnostics/lmi-fg-shadow-retry-unvalidated.patch; do not create a
second equivalent patch or add it to tonight's kernel.

A fresh check of the exact Mobian a5b3099017ae581aae8bf597b2f9c8c765026af1
and Android 71b13e62f057a649b77fe4062feb73ee72ad609c public fg-util.c files
finds them byte-identical (SHA256
c969590d0f30c2746a725497969eb49cad9a951e2426b1753b670c2bf7f94837).
Thus the defect is shared, not a demonstrated source-level asymmetry.

The existing native actual-function test now injects I/O errors at all ten
possible read positions instead of four boundary positions: 32 cases per
implementation, original defect reproduced and candidate checks pass.
The original erroneously accepts five mismatching pairs and rejects a match
on attempt five. The candidate rejects exhaustion and accepts the fifth match.
No retained handset evidence demonstrates this exceptional path occurred.
Existing measured endpoints are not all invalidated and no battery drain
improvement follows from this source test.

## Narrowing the displayed-percentage hypothesis

Saved Mobian and Android FG DT nodes both lack hold-soc-while-full,
linearize-soc, fg-increase-100soc-time and fg-increase-100soc-time-2.
Ordinary batt_soc tracking remains; SOC hi-res is enabled.
The high-voltage captured interval reports scale_mode_en=0. A DT capability
such as rapid-soc-dec-en does not establish its low-voltage runtime activation.

An unchanged-body native replay of fg_get_msoc with fixed register reads and
smooth_batt_flag=false shows that toggling report_full at fixed raw MSOC
changes the returned high-range percentage by at most two points.
The report_full latch alone cannot explain the complete 100-to-95
REAL_CAPACITY progression at a fixed raw value. The normal outer smoothing can
still delay CAPACITY relative to REAL_CAPACITY. This is source-level narrowing,
not a reconstruction of the actual internal register history or an electrical
measurement.

## Prioritization from the already preserved afternoon window

Between its observed unplugged marker and last USB-absent sample, the raw
reported counter falls 128382 units: 44043 during the initial ordinary
15-minute awake wait, 79719 across five natural sleep callback brackets and
4620 during postwake awake gaps. The last category is 3.60%; software and
shadow equivalents are 3.33% and 3.42%. These are reported-channel arithmetic,
not an energy budget; sleep brackets include short awake callback margins.

With natural returns now around 15 seconds at the D-Bus callback layer,
further blind shortening of those wakes is not the priority indicated by this
window. The initial wait share must not be projected to a full night.
No remaining consuming chip or calibrated current is established.

## Deferred work

Analyze only the preserved night data after return: compare sleep accounting
and early/late reported gauge progression. Do not require flat counters for
'stabilization' under event-selected SOC sampling, and do not treat filtered
endpoint current as an integral over sleep. The host analyzer checks USB,
clock, profile, closure and hash boundaries; no new experiment is triggered.
