# lmi battery viewer

Small GTK4/libadwaita application for the Mobian lmi handset. It displays
readable power-supply attributes, stores user-started sessions, plots sampled
battery percentages and exports CSV files. The French launcher is **Batterie
lmi**. GTK4, libadwaita, Python GI and an SVG GdkPixbuf loader are required;
the application does not download packages.

## Recording behavior

Recording is stopped after initial installation and is not enabled at login or boot.
The optional automatic-start switch enables the user unit at the next desktop
session; it does not start a recording immediately. Disable that switch to
prevent future automatic starts. Use Stop to end an already running session.
The Start button starts the user service; Stop terminates it. Closing the
viewer leaves an explicitly started recording running. The viewer reads live
attributes only while its window is active. The recorder samples once per
awake minute and observes login1 sleep and screensaver signals. It uses no
wake alarm, power inhibitor, forced suspension, governor changes or media
capture. Its ordinary GLib timer waits while the system is suspended.

Private JSONL sessions and recorder status are stored under
`$XDG_STATE_HOME/lmi-battery` (normally `~/.local/state/lmi-battery`). CSV
exports go to `~/Documents/Batterie-lmi`. Sessions include times, boot identity,
kernel identity and wake reasons; keep these private unless reviewed. Session
files use a restrictive umask. No session data belongs in the public repository.

## Interpretation

The instantaneous current is shown with the driver's sign, in mA. Voltage is
in volts and temperature in degrees Celsius. A negative charging current is
expected with the current lmi driver; this is not a battery-health verdict.

The three displayed averages derive separately from `charge_counter`,
`charge_counter_shadow` and `charge_now_raw`. They are different gauge models,
not three calibrated ammeters. Each reports its own valid coverage. Charging
endpoints, missing values, changed boot IDs, increasing counters and changed
capacity scales are excluded. A reset inside a sampled interval can still be
undetectable. No per-application or per-service electrical attribution is made.

Sleep duration uses paired login1 signals and the BOOTTIME-minus-MONOTONIC
clock difference. Missing or invalid pairs are not presented as valid sleep.
The percentage chart shows sampled points, avoiding interpolation across long
unsampled intervals. This application supports investigation; it does not by
itself fix standby consumption or validate the cell's physical condition.

The foreground view loads at most 5,000 records from the last 8 MiB of a session,
so its history memory does not grow without limit. Average estimates and sleep
totals refer to this visible window. Full-session CSV export streams records
instead of loading the whole session into memory. Private JSONL files remain
complete on disk; disk use still grows over time and requires normal management.

## Installation

Run `install.py USERNAME` as root on the handset, from this source directory.
The installer writes the application, desktop entry and optional user service;
it reloads that user's units without enabling or starting recording. An owned
manifest permits later updates only if installed files still match it.

Add `--automatic` to explicitly enable and start background recording. Its
user unit then starts with the desktop session. The automatic-start switch
controls future session starts; the Start/Stop buttons control the current run.
The recorder adds awake CPU, sysfs-read and disk-write work. The foreground
viewer also uses graphics resources. Neither cost is assumed to be zero;
standby qualification should keep the viewer closed and document whether the
recorder was active. Compare observer-on/off measurements before assigning a
quantitative overhead. GLib sampling timers do not wake deep suspend.

Run `install.py USERNAME --remove` to remove unchanged owned installed files.
Private sessions and CSV exports are preserved.

## Validation

`python3 test_model.py` covers valid discharge, charging exclusion, scale drift,
missing-counter coverage, reboot, increasing counters and sleep-clock validity.
On 12 October 2026, the handset check confirmed GTK4/libadwaita/SVG availability
and window startup. A bounded plugged-in recorder test produced start, periodic
sample, screen-signal and stop records, then exported a nonempty CSV. The user
confirmed that the real session and its chart were visible after correcting
the viewer's session-directory lookup. Recording was left stopped.
Long-term observer overhead and unplugged sleep callbacks remain separate
hardware qualifications; the viewer is not enabled automatically.

After that prototype check, optional automatic-start controls and bounded
history loading were added with source-level validation. Those additions have
not been qualified on the handset. The project handset application is being
removed at the user's request because its global readings duplicate the
existing focused diagnostic collector. These sources remain available as a
standalone utility; they do not require the coordinator's private scripts.
