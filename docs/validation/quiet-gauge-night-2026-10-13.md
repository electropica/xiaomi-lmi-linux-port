# Quiet-gauge validation, 12–13 October 2026

## Installed baseline and result

The persistent RPMh diagnostic kernel, suspend-only NPU hook, Phosh
`0.46.0-3+deb13u1+lmigaugewake2` and GSD `48.1-1+lmiquietgauge2` were unchanged.
Both quiet-resume opt-ins were active, debug logging was off, Wi-Fi remained
enabled and the normal automatic-suspend timeout was 900 seconds. The optional
battery viewer had been removed. A passive observer used sleep/screen callbacks
and an awake USB poll, without a wake alarm or forced suspension.

Observed unplugged duration was 31,041.226 seconds (8 h 37 min 21 s). Battery
capacity read 100% at departure and 77% at cable return; the return endpoint was
already charging and is not a pristine discharge endpoint. The boot did not
change. Clock-accounted suspension totaled 28,281.213 seconds across 42 paired
windows: 91.11% of the unplugged interval. The first automatic suspension began
915.163 seconds after observed unplug.

All 40 `438 msoc-delta` resumes started with the screen blank, kept it blank and
were followed by suspension after 15.204–15.565 seconds. This qualifies the
installed delta filter over the night; it does not establish low standby power.

One other unplugged resume reported `441 msoc-high`. A WakeUpScreen signal and
unblank followed it; blanking returned about 300 seconds later and suspension
resumed 1,200.216 seconds after that wake. Existing filters deliberately match
only `438 msoc-delta`, so this is an unhandled event rather than a failure of the
qualified delta path. It accounts for a twenty-minute awake episode, not the
entire residual drain.

Scale-stable, battery-only counter intervals covered 30,711.140 seconds.
Software/shadow/raw estimates were respectively 69.27 / 69.30 / 92.06 mA. These
include awake intervals and are differently scaled gauge estimates, not three
independent ammeters or a pure deep-suspend current measurement. Do not infer a
causal regression from a prior shorter, approximately 50 mA sleeping observation.
The observer finished successfully; RTC state was clear, the NPU restoration
state was absent and normal charging/input settings were verified after return.

## Guarded msoc-high candidate

The preserved `qpnp-fg-gen4.c` registers `msoc-high` as wakeable and directs it
to `fg_soc_irq_handler`, which logs the IRQ and returns handled. `msoc-empty`
uses a separate handler. This does not justify suppressing all fuel-gauge events
or changing thresholds/calibration.

The [candidate patches](../../userspace/power/msoc-high-resume/README.md) extend
both existing userspace guards to the exact single reason `441 msoc-high`, only
with a fresh Discharging status and a valid 30–100% capacity reading. The existing
USB, actual-sleep, lock/blank, peer opt-in and activity checks remain in place.
Low/empty, combined IRQs, unknown reasons, missing/malformed data and ordinary
user/USB/alarm wake paths fail open. Notifications and battery-protection handling
are unchanged. Neither the kernel nor its IRQ wake policy is modified.

Native tests compiled the actual candidate matchers: 20 reason/data cases through
both guards plus eight surrounding resume boundaries passed. Both normalized
patches applied to the recorded baselines and yielded the expected candidates.
Phosh's original CRLF bytes and LF-normalized identity are recorded separately;
the guarded build copies the pinned LF candidate only after validating the actual
compiled baseline bytes. GSD baseline bytes already use LF.

At the initial source publication, ARM compilation, installation and target
qualification had not been performed. The subsequent update below records the
completed build/install and normal-path smoke test. The exact msoc-high resume
remains unqualified; no saving is established yet. The intended effect is to
avoid the identified screen relight and twenty-minute awake episode.

## Build, installation and normal-path smoke update

The user completed the incremental ARM build. Source identities match the pinned
candidates; package names, versions and architectures were checked for Phosh/
common `0.46.0-3+deb13u1+lmigaugewake3` and GSD/common `48.1-1+lmiquietgauge3`.
Four qualified v2 rollback packages were verified and staged before installation.
The package simulation upgraded only these four packages and removed none.
A bounded rollback was armed before installation; existing opt-ins, the kernel
and the NPU policy remained unchanged. Both services started without restart
loops, and the user confirmed normal touch, application scrolling and power-key
behavior. The session can read the new capacity/status guard inputs.

One accepted three-minute unplugged smoke observation temporarily reduced the
automatic-suspend delay from 900 to 60 seconds, with independent restoration.
There was no forced suspension or wake alarm. Clock accounting measured
154.149 seconds of actual sleep, followed by the expected USB interrupt. The
screen was blank before suspension, all four v3 versions remained installed on
the same boot, and no pending RTC/NPU restoration or observer remained.

The normal 900-second delay was restored. Owned restart overrides and both trial
fallback timers were removed/stopped after verification; the qualified v2
rollback remains available. Charging/input settings and unchanged service PIDs
were verified. V3 is retained as a candidate for a longer natural discharge.
No msoc-high interrupt occurred during this smoke test: it does not qualify the
new high branch, prove a battery saving or solve the residual sleep drain.

## Daytime v3 qualification: 13 October

The normal-timeout passive observation ran on the same persistent kernel and
Phosh/GSD v3, with both opt-ins, debug off and Wi-Fi left enabled. No wake alarm,
forced suspension, capture or new power-policy change was introduced. The
observer was armed before departure and no phone contact occurred between the
confirmed unplug and return. Its one-hour unplug-wait limit accommodated the
planned departure; the measurement begins at observed USB loss, not arming.

The unplugged interval was 37,754.451 seconds (10 h 29 min 14 s). Reported capacity
was 100% at departure and 75% at USB return; the latter is a charging-contaminated
endpoint. Actual suspension totaled 36,089.465 seconds across 48 paired windows,
95.59% of the interval. Initial automatic sleep occurred after 911.133 seconds.

All 46 observed msoc-delta wakes stayed blank and resuspended. Crucially, one
exact `441 msoc-high` wake occurred at 80% with Discharging and USB absent. The
screen was blank before and at resume, no unblank was observed in its awake
gap, and the next suspension began 15.366929 seconds later. The prior v2 night
had the same reason at 80% followed by screen relight and 1,200.216 seconds
awake. This qualifies the guarded v3 behavior for this real noncritical case;
it does not qualify every battery level or establish a calibrated total saving.

Valid battery-only counter coverage was 37,461.874 seconds; software/shadow/raw
estimates were 59.43 / 59.42 / 88.29 mA. They include awake intervals and remain
differently scaled gauge estimates. The day and previous night are not a
controlled identical-duration electrical A/B, so do not claim their rate
difference as the isolated power saving of this filter. Residual drain is
still present despite successful suspension and the fixed screen episode.

The boot and four v3 versions were unchanged, services were active with no
restart, and analysis found no unmatched sleep window or clock warning. The
observer finished successfully; RTC state was clear and NPU restoration was
complete. Normal charging and input_suspend=0 were checked after return.
The qualified v2 rollback remains available. No new short repeat is required
merely to reproduce this already observed high-wake result.
