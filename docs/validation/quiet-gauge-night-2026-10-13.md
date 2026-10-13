# Quiet-gauge overnight observation, 12–13 October 2026

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

## Narrow source candidate, not installed

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

Full ARM package compilation, installation and target qualification have NOT
been performed. This candidate has no measured battery saving yet. Its intended
effect is to avoid the identified screen relight and twenty-minute awake episode.
