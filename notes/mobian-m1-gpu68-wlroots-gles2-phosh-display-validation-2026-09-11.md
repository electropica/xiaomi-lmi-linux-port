# Mobian M1 GPU-68 wlroots GLES2/Phosh display validation - 2026-09-11

## Scope

GPU-68 validates the first visible desktop integration of the patched Mesa 25.0.7 Zink/Turnip/KGSL path on Xiaomi `lmi` / POCO F2 Pro.

The validated path is:

```text
Phosh
    -> Wayland
    -> Phoc
    -> wlroots GLES2
    -> Mesa EGL
    -> patched Zink
    -> system Vulkan loader
    -> Turnip
    -> Adreno 650 KGSL
    -> msm DRM
    -> DSI-1 1080x2400@60
```

## Validated runtime

The active Phoc session used:

```text
WLR_RENDERER=gles2
WLR_BACKENDS=drm,libinput
WLR_DRM_DEVICES=/dev/dri/card0
LD_LIBRARY_PATH=/opt/mobian-gpu/lib
VK_ICD_FILENAMES=/opt/mobian-gpu/icd.d/freedreno_icd.aarch64.json
MESA_LOADER_DRIVER_OVERRIDE=msm
ZINK_ALLOW_KGSL_DISPLAY_DEVICE=1
```

The isolated runtime provided Mesa EGL/GLES2/Gallium and the Turnip ICD under `/opt/mobian-gpu/`.

## KGSL and ION access

The Mobian user was granted access through the `render` group:

```text
crw-rw---- root render /dev/kgsl-3d0
crw-rw---- root render /dev/ion
MOBIAN_KGSL_ACCESS=PASS
MOBIAN_ION_ACCESS=PASS
```

## EGL/Zink result

The real wlroots session reached:

```text
MESA: info: ZINK: using explicit Turnip cross-device display override
EGL initialized: 1.5
EGL_VENDOR=Mesa Project
EGL_VERSION=1.5
```

The Zink diagnostic reached `zink_internal_create_screen` and completed screen creation successfully.

## Display result

The physical output was verified as:

```text
DSI-1
status=connected
enabled=enabled
modes=1080x2400x60x184345cmd
```

The kernel display path reported 1080x2400 at 60 Hz.

## Phosh result

Phosh 0.46.0 was running as a Wayland client through the active Phoc session.

After a clean restart of `phosh-m0.service`, the session reached:

```text
phosh-m0.service: active (running)
Main PID: phoc
```

**Visible display: OK.**

This is the first validated visible Phosh desktop output using the GLES2/Zink/Turnip/KGSL path.

## Validation boundary

GPU-68 establishes wlroots GLES2 initialization, Zink/Turnip/KGSL integration, Phoc/Phosh session operation and visible DSI-1 output.

It does not yet establish prolonged stability, suspend/resume, performance, power efficiency, video acceleration, complete desktop correctness or production readiness.

