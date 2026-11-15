# Drawer layout with application previews

The `drawer-layout-20261115.patch` candidate adjusts the application deck's
height when previews are present. It also adds debug-level launch attribution
for investigating unexpected application launches. It builds on the previously
deployed `+previewdouble1` Phosh source; it is not a standalone patch for stock
Debian Phosh.

On 15 November 2026, the three `phosh`, `phosh-common` and `libphosh-0.45-0`
packages with suffix `+drawerlayout1` were installed on the handset. The user
confirmed that the drawer opens completely with a preview, that the spacing is
correct, and that an icon selected after scrolling opens the intended app.
The launch sometimes reported on the home screen when the sleep notification
appears remains a separate, unconfirmed issue; this patch adds diagnostics but
does not establish its cause.

The three matching `+previewdouble1` packages form the rollback set. Automatic
rollback was armed before installation and disabled after the shell passed a
stability check. Build outputs and user data are not part of the repository.
