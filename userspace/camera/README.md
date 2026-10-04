# Camera userspace status

Megapixels is installed in the validated userspace, but its required
`qcom,kona-mtp.ini` configuration is absent and the downstream camera media
pipeline was not demonstrated. Sensor identities remain suggestions rather
than confirmed node-to-device mappings. No speculative Megapixels
configuration is included. See the
[`camera blocker validation`](../../docs/validation/archi-validation-02-camera-blocker-2026-09-27.md).

## Current functional recheck — 2026-10-04

A bounded launch still exits immediately with status 1 and the missing
`qcom,kona-mtp.ini` message. The existing source's request-manager private
ioctl and sensor core-only operation tables support the previously recorded
downstream-interface mismatch. No speculative INI, replacement application,
capture attempt or kernel build was added. The functional blocker remains
open; see the [current checklist](../../docs/validation/lmi-app-checklist-2026-10-03.md#functional-priority-and-camera-recheck--2026-10-04).
