# Guarded msoc-high resume candidate

Source-only incremental patches for qualified Phosh v2 and GSD2. No ARM build,
phone installation or target qualification has yet occurred. No measured saving.

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
