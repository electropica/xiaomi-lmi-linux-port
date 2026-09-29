# D-v43 display milestone — 2026-09-26

## Validated direct KMS path

The guarded legacy `modetest` procedure produced several colored rectangles
on the physical Xiaomi lmi panel. It requested connector 29 (`DSI-1`) on CRTC
129 with mode `1080x2400x60x184345cmd`. This validates the downstream CRTC,
scanout, DSI link, panel, and backlight path. It does not validate GPU/EGL,
Weston, Phosh, a persistent graphical session, or touch input.

The reproducible test is [`scripts/test-dsi-modetest.sh`](../scripts/test-dsi-modetest.sh).

## Weston results

Weston 16 was staged only in temporary overlays. It reached setup in some
attempts but failed before a modeset: DRM-master permission failures,
`weston_drm_format_array_add_format` assertion failures, and refusal of the
attempted atomic-disable option were observed. No Weston 16 output was
produced and no installation was persistent.

Weston 14.0.2 was rebuilt natively for Alpine/musl with the DRM backend,
Pixman renderer, kiosk shell, libseat/seatd, and an isolated
`/opt/weston14-lmi` prefix. The successful r0 package and overlay were:

- APK r0 SHA-256: `38b85fd8720aa99fa2e7d4eb05ffeb9d4b0828862170ea331c0861dc0c0322dc`;
- overlay r0 SHA-256: `926dbe2646d077f7a1b4510f108e26bce0fcf43a94d00894498935f636a659c3`.

With normal Weston 14 atomic modesetting, the commit failed with `EINVAL`.
With `WESTON_DISABLE_ATOMIC=1`, Weston selected the legacy path and remained
alive for the observation window, but the panel stayed black. A separate r1
variant forced only `DSI-1` toward CRTC 129 after checking compatibility and
availability; its overlay SHA-256 is
`5f553036577dc87102a7956bd68bce87e3ff20de315b13c52a767b39cb58e814`.
The journal confirms `DRM: preferring CRTC 129 for DSI-1` and
`Output DSI-1 (crtc 129)`, yet the screen remained black.

During Weston, DSI-1 changed to `enabled`, but the backlight driver reported
`actual_brightness=0` while the requested value was 536. Every temporary run
restored DSI-1 to `disabled`, stopped the private seatd, removed
`/run/seatd.sock`, and left no persistent test process or configuration.

The CRTC-129 recipe, source patch, and packaging/build wrappers are kept as
small, source-only material under [`scripts/weston14-crtc129/`](../scripts/weston14-crtc129/).
The r1 build wrapper invokes the packager explicitly through `bash`; direct
execution had failed with `Permission denied`, while the explicit Bash call
produced the validated overlay.

## Status and boundary

The display hardware and direct legacy KMS path are validated. Weston
integration remains unresolved: both the normal CRTC-184 route and the forced
CRTC-129 legacy route stayed black, with the backlight's actual value at zero.
The Weston reconstruction is therefore intentionally suspended. Further work
continues on the validated OpenRC operating system and applications using the
older functional build. No APK, overlay, source tarball, rootfs, image,
remote journal, temporary state, credential, or secret is stored in this
repository.
