# Drawer touch alignment

This patch builds on the project's customized Phosh 0.46 drawer. It disables the vertical deck gesture over the application list and provides a back button, so scrolling the list and tapping its icons do not compete with that gesture. It also reserves space for running-application previews.

The `+drawertouchfix1` package containing this patch was installed on the lmi handset; the operator confirmed that tapping icons after scrolling opened the intended applications. Further coverage with different window counts is still needed.

Known limitations: the downward gesture to close the drawer is replaced by the back button, the previews are reported as too small, and the reserved preview height may remain after the last window closes. These are follow-up work. This patch depends on the earlier custom drawer series and is not a standalone patch for stock Phosh.

Phosh is session-managed on the device and its unit refuses manual restart. Installation and rollback need a device-specific procedure that restores all three matching packages (`phosh`, `phosh-common`, and `libphosh-0.45-0`) and verifies the running executable.
