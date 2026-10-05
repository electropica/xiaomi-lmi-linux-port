# Lomiri Camera installation test — 2026-10-05

## Result

Debian ARM64 `lomiri-camera-app 4.0.8+dfsg-5` was installed on the lmi
Mobian/Phosh phone. Its interface starts under Wayland/OpenGL, but the operator
reported a black viewfinder; a compositor screenshot independently confirmed it.
No photograph or video was validated. Installation is not camera compatibility.
The existing rear HAL3 diagnostic remains the only validated preview path.

## Installation and launch findings

The phone could not resolve the Debian mirror. Official Debian packages were
obtained on the host using the phone's APT URI plan, checked against that plan,
and transferred over SSH. No Wi-Fi setting was changed for this trial.

Besides `qtwayland5`, launching required `qml-module-qt-labs-settings` and
`libqt5multimedia5-plugins` (with their dependencies). Missing Qt settings
initially prevented QML loading. A software Qt Quick launch subsequently
crashed: a bounded GDB trace located the fault in `QOpenGLContext::functions()`
called by Lomiri Toolkit `UCLomiriShape::updatePaintNode`. Removing the software
backend override and using OpenGL allowed the interface to remain running.

The upstream desktop entry is restricted to Lomiri. A per-user test launcher
removes that restriction and explicitly selects Wayland. It is an experimental
installed-phone launcher, not enabled in the canonical image recipe.

## Backend limitation and next investigation

The installed Debian Qt multimedia plugins provide the standard GStreamer
backend. `gst-inspect-1.0 droidcamsrc` reports no such element. This trial did
not install or validate the Android camera bridge used by Ubuntu Touch/Sailfish.
An application shell with a black viewfinder does not establish sensor failure,
HAL compatibility, or the feasibility of adapting those bridges to this HAL3.

Before implementing a complete custom camera UI, investigate a reusable Android
camera bridge or exposing the validated stream to a standard Linux frontend.
Flash, zoom, front popup camera and video remain unvalidated here. No motor,
kernel, boot, partition or OEM calibration changes were made during this trial.

## References

- [Ubuntu Touch camera application](https://gitlab.com/ubports/development/apps/lomiri-camera-app)
- [Sailfish multimedia architecture](https://docs.sailfishos.org/Reference/Core_Areas_and_APIs/Multimedia/)
- [Debian package](https://packages.debian.org/trixie/lomiri-camera-app)
