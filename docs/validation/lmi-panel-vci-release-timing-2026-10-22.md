# Display panel VCI release timing — LineageOS reference vs Mobian, 2026-10-22

Scope: a **timing** difference in the display power path, derived entirely from
the retained raw traces. No device contact, no new test.

Evidence class: **T** (retained suspend-transition evidence). A regulator
transition is a software request. Nothing here is a calibrated electrical
measurement.

## 1. Observation

`display_panel_vci` and `pm8150_l14` are released at a different moment on the
two platforms.

**LineageOS reference**, kernel `4.19.325-cip131-st15-perf-g71b13e62f057`,
retained trace `work/lineage-power-trace-20261022-private/trace.txt`, four
complete `machine_suspend` windows, timestamps relative to the suspend entry:

| window | `display_panel_vci` enable | `display_panel_vci` disable | suspend entry | idle gap after the release |
|---|---|---|---|---|
| 0 | −260.690 s | −255.081 s | 0.000 s | 255.08 s |
| 1 | −601.682 s | −596.073 s | 0.000 s | 596.07 s |
| 2 | −1201.672 s | −1196.063 s | 0.000 s | 1196.06 s |
| 3 | −1801.683 s | −1796.073 s | 0.000 s | 1796.07 s |

`pm8150_l14` follows the same instants (disable at the same timestamp as
`display_panel_vci`, to the microsecond). The panel is enabled, released
5.61 s later, and the suspend follows 255 s to 1796 s after that release.

**Mobian**, 2026-10-12 wide observer trace
(`work/wide-regulator-observer-20261012-private/trace.txt`, the only Mobian
trial with a complete trace: `complete_trace_possible: true`, no overrun, no
unmatched call, 190.634 s of userspace-qualified sleep), timestamps relative
to the suspend entry at 208655.511691:

```
   -0.301 s  regulator_disable_complete: name=display_panel_vci
   -0.301 s  regulator_disable_complete: name=pm8150_l14
    0.000 s  suspend_resume: machine_suspend[3] begin
```

There is **no** `display_panel_vci` enable event in the 110.6 s of trace
coverage before the entry, and the disable lands 0.301 s before the suspend
entry — i.e. inside the suspend path. The rail was therefore held enabled
from before the trace window right up to the suspend.

The forced observer trial of the same day shows no `display_panel_vci` event
within an hour of its entry, but that trace lost cpu3 events (overrun 7307)
and captured only 66 regulator events, so its silence is not evidence of
absence.

## 2. Reading

* On the LineageOS reference the regulator framework is asked to release
  `display_panel_vci` and `pm8150_l14` at screen-off, 255 s to 1796 s before
  the machine suspend.
* On Mobian the same release is requested **inside the suspend path**, 0.301 s
  before the machine suspend, and no re-enable appears in the observed
  post-resume window (the LineageOS reference re-enables both 43 s to 1584 s
  after the resume).

**A regulator disable event is a software request by the regulator core.** It
does not prove that the rail was electrically cut, that the consumer released
it, or that the rail was powered before the request. What is established here
is *when the framework was asked to release the rail*, not the electrical state
of the panel during the sleep.

During the powered-down interval both rails are released on both platforms, so
this is **not** a difference in the deep-suspend state. It is a difference in
the **screen-off to suspend idle gap**: on Mobian the panel rails stay
*requested by the regulator framework* for the whole idle gap, on LineageOS
they do not.

That gap is governed by the inactivity delay. The shipped Mobian profile sets
`sleep-inactive-battery-timeout=900`
(`build/profiles/lmi-current/94_lmi-current-power.gschema.override`), so the
exposure per screen-off can be up to the order of 900 s of a requested display
panel rail instead of a few seconds. The LineageOS idle gaps observed above
(255 s to 1796 s) show the same structure on the reference side.

This is the kind of difference that a **deep-suspend current measurement cannot
see**, because the rail is released before the processor goes down on both
platforms. It would appear in daily consumption, not in a suspend-window
current figure.

## 3. Limits

* A regulator enable/disable is a request. **The current drawn by an enabled
  `display_panel_vci` is not measured anywhere** in the retained evidence.
* The Mobian observations come from the 2026-10-12 observer build, which does
  not record a kernel release string and is therefore **not certified** to be
  the current build. The 190.634 s Mobian window is plugged-context and awake
  at the boundaries.
* The **length** of the Mobian screen-off to suspend gap is **not measured**;
  the retained trace only shows that the rail was still requested 0.301 s
  before the suspend.
* The trace carries no display-driver tracepoints, so the display stack's own
  power-down sequence is not observed; only the regulator requests are.
* The mechanism (who keeps the rail requested on Mobian: the panel driver not
  releasing at blank, or another consumer) is **not established**.
* An awake read of the rail state would settle **one** precise question:
  whether the regulator framework still holds the rail during the idle gap. It
  would not measure the current, would not identify the consumer that holds
  it, and would not establish the electrical state during the sleep.

## 6. Cheapest discriminator

One **awake, read-only** observation, no policy change and no suspend:

1. On Mobian, with the screen off and the system still awake (before the
   inactivity delay expires), read the state of `display_panel_vci` and
   `pm8150_l14` — through the regulator framework's own interface, not by
   writing anything — and record the elapsed time between screen-off and the
   suspend that follows.
2. Repeat the same read on the LineageOS reference at the same point in its
   idle gap.

**Discriminating outcomes.**
* Mobian reads *enabled* during the idle gap while LineageOS reads *disabled*
  → the difference is confirmed, its duration is quantified, and the display
  panel power path becomes the top-ranked client path.
* Mobian reads *disabled* during the idle gap → the difference was an
  artefact of the 2026-10-12 build or of the observer's capture, and the
  display path is closed.

If the state cannot be read without privilege on the LineageOS side, the same
privileged read-only snapshot already required for the UFS policy covers it:
both readings come from one capture set.

## 7. Relation to the existing checklist

`docs/validation/lmi-standby-peripheral-checklist-2026-10-20.md` lists the
display row as **Open** with the gap *"Panel-specific sequence and rail
requests during a qualified sleep interval; software screen-off alone
insufficient"*. The retained transition evidence above narrows that gap to the
**idle gap before the suspend**, and adds the observation that the release
happens at a different instant on the two platforms. It does not close the row:
the current is still unmeasured and the Mobian build is unconfirmed.


## 5. Current-build reading, 2026-10-22: R1 is refuted

Two point-in-time regulator summary reads on the **current** Mobian kernel
(`4.19.325-cip128-st12-perf-ga5b3099017ae-dirty`, root over the existing SSH
route, USB connected, the device untouched in between):

| moment | `display_panel_vci` | `pm8150_l14` | `gpu_cx_gdsc` | `vdd_boost_vreg` |
|---|---|---|---|---|
| 16:53, about 110 s after boot | **use=1**, open=2 | **use=1**, open=2 | use=0, open=4 | use=1, open=1 |
| 17:00, about 536 s after boot, untouched | **use=0**, open=2 | **use=0**, open=2 | not sampled | use=1, open=1 |

In both readings the consumer of the two panel rails is
`soc:qcom,dsi-display-primary`, and it holds them *open* the whole time
(`open=2`); the *enable* (`use`) is what changes. The rails went from enabled
to disabled while the system stayed awake and was not touched, which is the
signature of the display stack releasing them when the panel blanks.

**The 2026-10-12 observation does not reproduce on the current build.** The
retained 2026-10-12 regulator summary shows the same consumer and the same
`open=2` throughout, with `use` toggling 0 -> 1 -> 0 across the session, so
the release-at-blank path exists there as well. The reading of "the rails are
released 0.301 s before the suspend" on that trial is therefore better
explained by the panel still being lit until the suspend path of that
particular run than by a missing release-at-blank behaviour.

**Consequence.** R1 is **refuted as a standby difference**: on the current
Mobian build the panel rails are not held enabled through the screen-off to
suspend idle gap. The earlier statement in this note that Mobian "keeps the
panel rails requested for the whole idle gap" does not hold and is withdrawn.

**Limits that remain.** The absolute screen state is not directly readable on
this platform: the DRM connector reports `connected` whether or not the panel
is lit, and there is no backlight on this OLED panel. The conclusion therefore
rests on the **differential** observation (use 1 -> use 0 while the system
stayed awake and untouched), not on a directly observed blank event. A
regulator `use` count is still a framework state, not an electrical
measurement.
