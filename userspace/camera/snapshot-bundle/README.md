# Snapshot rear-camera image bundle

See [the complete image recipe](../../../build/profiles/lmi-current/COMPLETE-BUILD.md).
This directory contains source only. `build-bundle.py` is operator-run and uses
external NDK/ARM build roots and the matching external Android C++ library.
`--prepare-only` applies the canonical timing, fixed-FPS and NEON patches to
a fresh output tree without compilation or camera access. `check-bundle.py`
validates the fixed external bundle before any image staging.

`lmi-snapshot` owns the child producer, fixed Wayland focus monitor and Snapshot.
It refreshes the existing root backend's foreground lease only while Snapshot
is active and the session is unlocked. Lock/background/exit stops sensor acquisition and polling; children
receive a death signal if the launcher is killed. No service is enabled at
boot and no microphone or video recording is requested by this launcher.
Snapshot itself can request recording through its own UI.

The ordinary launcher uses scoped Cairo/GDK and Snapshot tuning settings.
The retained runtime remains rear-only and experimental. The new lifecycle
has source/host checks, not handset qualification; actual preview/recording
requires fresh operator readiness. Do not install old resource-only home UI
on top of the paired native Phosh candidate.
