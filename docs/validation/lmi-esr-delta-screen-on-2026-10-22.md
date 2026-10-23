# The esr-delta wake and the screen that came on: what the evidence supports

## The question

The second resume of the 15:21-15:47 UTC window was caused by IRQ 445
`esr-delta`, and the display was programmed 0.16 s later. The quiet-gauge
policy installed on the phone recognises "438 msoc-delta" and, with
guards, "441 msoc-high", but not "445 esr-delta". This note records what
was verified on the device, what the source says, what the kept evidence
shows, and what a limited change would and would not do.

It does not propose suppressing an interrupt, and it does not attribute
the standby difference to this single wake.

## What is actually installed and enabled

Read on the device, not inferred:

* `phosh` `0.46.0-3+deb13u1+lmigaugewake3+homedrag7`, that is the v3
  quiet-gauge build. The v4 candidate of 2026-10-20
  (`48.1-1+lmiquietgauge4`) was never built and never installed.
* `/usr/libexec/gsd-power` (package `gnome-settings-daemon`), sha256
  `244e30992ee87fc4eeb7269514ca015596e07848f9c5b138c54db913c5b87161`.
  Its strings contain `438 msoc-delta`, `441 msoc-high`,
  `LMI_GSD_QUIET_GAUGE_RESUME` and `quiet gauge resume`. They do **not**
  contain `445 esr-delta`.
* `/usr/libexec/phosh`, sha256
  `52412006a0d7d39bba244ac9c6e40ad5d89fbd72ffa237b5b41e4632c8338190`.
  Its strings contain `438 msoc-delta` and `441 msoc-high`. They do
  **not** contain `445 esr-delta`.
* `/usr/bin/phosh-session` contains neither.
* Both opt-ins are live in the running processes: `phosh` (pid 3418) has
  `LMI_PHOSH_GAUGE_WAKE_FILTER=1`, `gsd-power` (pid 3496) has
  `LMI_GSD_QUIET_GAUGE_RESUME=1`.
* `/sys/kernel/wakeup_reasons/last_resume_reason` on the device reads
  `445 esr-delta` at the time of this check.

So the gate is active, the reason it rejects is the one the device
produces, and neither installed binary knows that reason.

## What the source says

The installed code comes from the v3 sources kept in the private area,
`msoc-high-candidate/gsd.c` (sha256 `3a776734…`, the exact base of the
2026-10-20 candidate review) and `msoc-high-candidate/phosh.c`. Both
carry the same gate.

The Phosh side, in `on_logind_prepare_for_sleep`:

```c
-    phosh_screen_saver_manager_wakeup_screen (self);
+    if (!lmi_is_gauge_resume (self))
+      phosh_screen_saver_manager_wakeup_screen (self);
+    else
+      g_debug ("lmi: keep screen blank after gauge-only resume");
```

The GSD side, in `handle_resume_actions`: when the resume is not
qualified as a gauge resume, the last branch calls
`backlight_enable(manager)`.

The gate itself, identical in both trees:

```c
static gboolean
lmi_quiet_reason_allowed (const char *reason)
{
  ...
  if (g_strcmp0 (reason, "438 msoc-delta") == 0)
    return TRUE;
  if (g_strcmp0 (reason, "441 msoc-high") != 0)
    return FALSE;
  ...  /* fresh, noncritical, discharging reading */
}
```

The other conditions are the same on both sides: the screen was blank and
locked, no user activity was seen, the idle mode was sleep, the suspended
interval was longer than 50000 microseconds, that is 50 ms and not 50 s,
and USB was disconnected. The reason list is the only condition that
differs between "438 msoc-delta" and "445 esr-delta".

## The differential inside the window

From the preserved kernel analysis of 2026-10-22
(`mobian-window-analysis-20261022T162957.json`, private):

| moment | event |
|---|---|
| t=1818.956 | display blanked, `DC off` |
| t=2719.630 | resume caused by IRQ 438 `msoc-delta` (15:43:24 UTC) |
| t=2735.432 | resume caused by IRQ 445 `esr-delta` (15:44:37 UTC) |
| t=2735.595 | `dsi_display_set_mode`, panel ESD interrupt re-enabled |
| t=3035.589 | display blanked again, at the reconnection |

The screen was blank across both resumes, USB was disconnected across both,
and the operator's own account is that the phone woke by itself with no
operator action. The first resume produced no display programming at all.
The second one produced a full mode set 0.163 s later. The only
difference between the two events is the wake reason, and that is exactly
the condition the installed gate does not recognise.

What the wake cost in that window: from 15:44:37 to the reconnection at
15:47:43, that is 186 s with the screen lit. The window's awake time was
1117 s in total, of which about 915 s is the idle delay that follows the
screen blank, and 16 s is the 15 s grace timer after the recognised
`msoc-delta` resume. The esr-delta wake therefore accounts for 186 s of
the 1117 s awake, about 17 %. It does not account for the rest, and the
standby difference must not be attributed to it.

## What the interrupt is

In `drivers/power/supply/qcom/qpnp-fg-gen4.c`, sha256
`0f5676829cb2a40daa191a456998c700d744afe8346e07dd3c7af2a7e8685957`,
identical between the Mobian and the Android revision:

```c
[ESR_DELTA_IRQ] = {
    .name       = "esr-delta",
    .handler    = fg_delta_esr_irq_handler,
    .wakeable   = true,
},
```

The handler reads the battery resistance, and the ESR delta interrupt is
armed with `enable_irq_wake`, so it can wake the system from suspend. It
is a fuel-gauge interrupt of the same family as `msoc-delta` and
`msoc-high`, and the review's caution applies unchanged: the handler may
vote awake and schedule calibration work, so **no interrupt is disabled
and no gauge processing is suppressed**. Keeping the screen off is a
userspace policy decision, and a different thing from the hardware
processing.

## How often it happens

A census of every kept quiet night and quiet day capture, 15 of them,
from 2026-10-11 to 2026-10-21
(`wake-reason-census-20261022.json`, private):

| wake reason | occurrences |
|---|---|
| `438 msoc-delta` | 995 |
| `502 typec-cc-state-change` | 115 |
| `441 msoc-high` | 23 |
| `-1 misconfigured IRQ 374 qcom,qmp-aop` | 10 |
| `323 pm8xxx_rtc_alarm` | 5 |
| `445 esr-delta` | **0** |

For the recognised reasons the quiet path worked every time: after a
`438 msoc-delta` resume the device went back to sleep after 15.16 s to
15.58 s (median 15.38 s, 495 observed cycles), and after a `441
msoc-high` resume after 15.33 s to 15.40 s (9 cycles). That is the grace
timer doing its job.

`445 esr-delta` never appears in those captures. The occurrence in the
2026-10-22 window is the first one in the kept evidence, and that window
is the first one where the phone spent a long time unplugged. Its
frequency on this device is therefore unknown, and its energy cost is
not measured.

## The candidate change

A limited diff is prepared, outside the repository, in
`quiet-grace-v3-review-20261020/esr-delta-accept-20261022.patch`, sha256
`6838a975f1ee6e46154fdd07530e1347046b2869d1042ffbba3bdcbc35ace1e0`. It
touches the gate in both trees and nothing else: "445 esr-delta" joins
"441 msoc-high" and is accepted only with a fresh, noncritical,
discharging reading. The comment above the function is updated with it.

The patch does not disable an interrupt, does not touch the gauge
drivers, does not touch the charge protections, does not touch the sleep
delay and does not touch the Phosh or GSD thresholds.

## The off-phone test

`check-esr-delta-policy-20261022.py` compiles the **actual**
`lmi_quiet_reason_allowed` function taken from both the GSD and the Phosh
source, patched and unpatched, with isolated dependency fixtures, and
runs it.

* against the unpatched v3 sources: **fails** on `allow("445
  esr-delta")`, in both trees, with the assertion message naming the
  defect;
* against the patched sources: **passes** every assertion, in both
  trees.

The assertions cover the new reason with every guard (rejected below
30 %, while charging, when the reading cannot be read, when the capacity
is not a number), the unchanged behaviour of "438 msoc-delta" and "441
msoc-high", and the safety direction: unknown reasons ("323
pm8xxx_rtc_alarm", "502 typec-cc-state-change", "-1 misconfigured IRQ
374 qcom,qmp-aop", the empty string, NULL) and combined reasons
("438 msoc-delta\n502 typec", "445 esr-delta+438 msoc-delta", "445
esr-delta 438 msoc-delta") keep failing open, that is they still turn the
screen on. An unrecognised wake is never silenced.

The report is `esr-delta-policy-check.json`, sha256
`f7c64c5bb9548aa81d5eaeee807d1d23824226f8e3e759361cbd87c8d455d2ba`. The
check uses host GLib and stubs only: no ARM build, no installation, no
phone deployment, no device UX validation.

## What is still missing

* **A build and a deployment.** Nothing was built, installed or pushed.
  That needs the operator's authorisation, and the patch is not ready for
  an unattended night: the screen behaviour with a real esr-delta wake has
  to be observed first.
* **A frequency measurement.** One occurrence in the kept evidence is not
  a rate. The wake is rare on this device as far as the captures show,
  which bounds the expected effect of the change.
* **A touch cannot be excluded from the preserved evidence.** The raw
  kernel log of the first window has rotated out of the ring buffer, so
  the preserved analysis carries the display and suspend markers but no
  input events. The grounds for the conclusion are the differential
  inside the window and the source path, not the absence of a recorded
  touch. A touch within the same 0.163 s would also have turned the
  screen on.
* **The two userspace gates are not isolated.** The log shows a full mode
  set, which both `phosh_screen_saver_manager_wakeup_screen()` and
  `backlight_enable()` can lead to. The patch changes both gates, so the
  distinction does not change the fix.
* **A policy risk, stated plainly.** Accepting `445 esr-delta` means an
  esr-delta wake keeps the screen blank. The ESR delta interrupt is a
  gauge interrupt, but it is also sensitive to a load change, so in
  principle real activity could accompany it. The GSD side keeps its
  activity flag and the Phosh side its locked state, and the guards
  narrow it further, but the behaviour with a real user action has to be
  validated on the device.

## Next decision

Two independent tracks, both waiting on the operator:

1. The second standby window with the corrected collector, which is still
   the measurement that produces a Mobian window figure.
2. The esr-delta acceptance, which needs a build, an installation and a
   device observation of the screen behaviour, none of which is done here.

The patch is not to be deployed before the second window, because the
second window measures the standby behaviour of the system as it is now.
