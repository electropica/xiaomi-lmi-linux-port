# Guarded msoc-high resume candidate

Incremental patches based on qualified Phosh v2 and GSD2. The four v3 runtime
packages have now been ARM-built and installed. User interface checks and one
normal sleep/USB-return smoke test passed. The subsequent daytime observation
qualified one real msoc-high wake at 80% while discharging: the screen stayed
blank and suspension resumed after 15.367 seconds. Residual standby drain
remains unresolved; a calibrated total saving has not been established.

See the [overnight evidence and boundaries](../../../docs/validation/quiet-gauge-night-2026-10-13.md).
`identity.json` pins actual before bytes, LF-normalized before bytes and LF
candidate bytes. Patches describe the semantic change against normalized source;
Phosh originally used CRLF. Do not apply against an arbitrary release or discard
the already qualified delay-inhibitor and USB-cycle changes.

Only exact single `441 msoc-high` with fresh Discharging and valid capacity
30–100% is added to the existing delta rule. Missing/low/empty/combined/unknown
events fail open. Existing actual-sleep, USB, lock/blank, activity and opt-in
guards remain. This is a userspace screen/idle fix, not a gauge recalibration,
kernel change or solution to all remaining deep-suspend drain.

For rebuilding from the pinned unmodified Debian sources, use the
[cumulative v3 patches and source verifier](../quiet-gauge-v3/README.md).
The patches in this directory remain historical v2-to-v3 increments.
