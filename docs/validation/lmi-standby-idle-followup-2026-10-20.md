# Standby peripheral follow-up — October 20, 2026

These checks qualify remaining hypotheses after the grouped one-hour trial.
They establish software paths and requested states, not calibrated rail current.
No additional hardware control, build or unplugged phone access was performed.

## Touchscreen and display during the completed hour

The retained kernel journal for the actual trial contains the FocalTech
POWER DOWN notification, IRQ disable and a gesture-disabled suspend path.
No touchscreen resume appears between that transition and USB reconnection;
no reported failure of the ordinary sleep-command write appears in the window.
The applicable driver is `focaltech_touch_mi`, not another FocalTech variant.
This supports operation of the existing notifier correction during this trial;
it does not measure sensor current or establish every GPIO/rail state.

Display ESD IRQ disable precedes the touch suspend. The next retained display
modeset/ESD enable occurs at USB return. Missing intermediate messages do not
establish electrical shutdown of every panel rail. An older trace also contains
a `display_panel_vci` disable request before machine suspend; its ftrace clock
must not be used to derive actual suspension duration from identical timestamps.

## Auxiliary ownership and sensor interface

A bounded, connected observation after restoration found the AKM-associated
`pm8150a_l8` request disabled with zero users, and no direct file-descriptor
holder of `/dev/akm09970` or `/dev/sensors` among 523 inspected processes.
The RPMh regulator enabled getter returns cached request state. These are
software observations after wake, not physical sleep-current exclusion.

The inspected `drivers/sensors/sensors_ssc.c` character interface has no-op
open/release methods and a timer-reading ioctl. File-descriptor ownership of
this particular interface therefore does not establish a SLPI power request.
Separate write-only boot/SSR controls are not status interfaces and were not
used. Firmware/kernel clients remain outside the descriptor observation.

## Codec reset and low-power requests

In `techpack/audio/asoc/codecs/wcd938x/wcd938x.c`, reset sequencing belongs
to probe and subsystem-restart paths. Ordinary component suspend sets a bias
flag; platform late suspend conditionally requests buck disable and supply
low-power mode. Neither ordinary callback selects the reset pinctrl state.
`msm-cdc-pinctrl.c` caches the requested state, which is not pad-voltage proof.

The previously identified reset mux difference therefore does not, by itself,
demonstrate an erroneous reset transition during ordinary suspend. Electrical
equivalence of the two mux configurations is also not established. Asserting
reset merely because playback is silent is not justified: retained MBHC and
SoundWire functionality has separate sequencing requirements.

The helper dependency omitted from the initial bounded source snapshot was
subsequently checked: `msm-cdc-supply.c:334–372` calls `regulator_set_load`
only for supplies whose `lpm_supported` flag is set. This requests zero load
in LPM and the configured optimum load on return; it is neither a physical
current measurement nor an unconditional regulator disable. Earlier retained
DT comparisons found no corresponding LPM-support properties in either the
Mobian codec node or the Lineage package overlay. Adding those properties
without validating shared-regulator capability is not an established fix.

## Consequence

No residual-drain cause or new kernel patch is established by these checks.
They narrow unsupported interpretations: descriptor absence is not firmware
shutdown, reset mux difference is not an observed suspend reset, and cached
rail state is not electrical calibration. The distinct incremental gauge-read
control is being observed separately and must not be presented as a power fix.

Private provenance: `touch-window-private.json`,
`aux-idle-after-return-private.json`, retained driver copies, and the bounded
codec call-graph review. See the [grouped result](lmi-minimal-scope-result-2026-10-20.md)
and [peripheral checklist](lmi-standby-peripheral-checklist-2026-10-20.md).
