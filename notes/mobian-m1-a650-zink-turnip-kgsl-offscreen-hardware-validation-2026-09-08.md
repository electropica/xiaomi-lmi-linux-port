# Mobian M1 A650 Zink/Turnip/KGSL offscreen hardware validation — 2026-09-08

## Scope

This note records the first validated OpenGL ES render on Xiaomi `lmi`
(SM8250 / Adreno 650) through the complete offscreen stack:

```text
OpenGL ES
    -> EGL surfaceless pbuffer
    -> Gallium Zink
    -> Vulkan Turnip Mesa 25.0.7
    -> Qualcomm KGSL
    -> /dev/kgsl-3d0
    -> Adreno 650
```

Unlike the preceding Vulkan-enumeration milestone, this test created a GLES
context, submitted rendering work, synchronized it, read a pixel back and
verified its value.

## GPU-54 prerequisite

GPU-54 first established that the isolated Mesa Turnip 25.0.7 library could
open `/dev/kgsl-3d0` and enumerate `Turnip Adreno (TM) 650`. That prerequisite
and the exact firmware and Mesa provenance are recorded in
`mobian-m1-a650-turnip-kgsl-hardware-validation-2026-09-08.md`.

The hardware-tested Turnip library remained:

| Property | Value |
|---|---|
| File | `libvulkan_freedreno.so` |
| Version | Mesa `25.0.7` |
| Architecture | AArch64 |
| SHA-256 | `dc46ac80f2322142e5ba17235e7cfd019f13c41157a34965cc5494622b84324d` |

## Isolated Zink runtime

The accepted Mesa build was produced natively in the Debian Trixie ARM64
environment through QEMU/binfmt. It was configured with:

```text
gallium-drivers=zink
vulkan-drivers=freedreno
freedreno-kmds=msm,kgsl
```

The runtime was deployed in an isolated directory on the phone. The test
selected its EGL/GLES libraries, Gallium driver path and Freedreno Vulkan ICD
without replacing the system Mesa installation.

In this Mesa build, Zink is part of the Gallium target
`libgallium-25.0.7.so`. The DRI driver name selects the Zink implementation
from that Gallium target; a small DRI filename or symlink must not be treated
as an independent Zink implementation. The runtime therefore had to keep the
isolated DRI entry and its `libgallium-25.0.7.so` target together.

## GPU-55C surfaceless initialization

The surfaceless section of `eglinfo` succeeded and reported:

```text
Surfaceless platform:
TU: info: Created an instance
TU: info: Found compatible device '/dev/kgsl-3d0'.

EGL vendor string: Mesa Project
EGL version string: 1.5

OpenGL core profile renderer:
zink Vulkan 1.3(Turnip Adreno (TM) 650 (MESA_TURNIP))

OpenGL ES profile renderer:
zink Vulkan 1.3(Turnip Adreno (TM) 650 (MESA_TURNIP))

OpenGL ES profile version:
OpenGL ES 3.2 Mesa 25.0.7
```

The global `eglinfo` return code was 1 only because the tool continued after
the successful surfaceless section and later failed to initialize its Device
platform. That later failure does not invalidate the successful surfaceless
initialization.

The separate `es2_info` attempt was also not a surfaceless test: that utility
tried to open an X11 display. Its failure therefore provides no contrary
evidence about the validated EGL surfaceless path.

## GPU-55E dedicated offscreen render

A dedicated local C test removed those utility-selection ambiguities. Its
transient phone binary identity was:

| Property | Value |
|---|---|
| Path | `/root/gpu55-offscreen` |
| SHA-256 | `ada865102889e3a3f8bc725daaf17ce7f55e547c8dcd77638e99a618af134037` |

The program:

1. initialized EGL through the isolated runtime;
2. selected a surfaceless display;
3. created a 16x16 pbuffer;
4. created and made current an OpenGL ES context;
5. called `glClearColor(0.25, 0.50, 0.75, 1.0)`;
6. called `glClear(GL_COLOR_BUFFER_BIT)`;
7. called `glFinish()`;
8. read a pixel with `glReadPixels()`;
9. compared the returned RGBA value with the requested clear colour.

The hardware output was:

```text
TU: info: Created an instance
TU: info: Found compatible device '/dev/kgsl-3d0'.

Mesa
zink Vulkan 1.3(Turnip Adreno (TM) 650 (MESA_TURNIP))
OpenGL ES 3.2 Mesa 25.0.7

PIXEL_RGBA=64,128,191,255
PIXEL_CHECK=PASS
GPU55_OFFSCREEN_RENDER=PASS
GPU55_RENDER_RC=0
```

The pixel matches the quantized clear colour:

```text
0.25 * 255 ~= 64
0.50 * 255 ~= 128
0.75 * 255 ~= 191
1.00 * 255  = 255
```

The test binary and isolated Mesa runtime are not stored in Git.

## Validated result

GPU-55 validates on real hardware:

- loading the isolated EGL implementation;
- selecting the EGL surfaceless platform;
- loading Gallium Zink from the isolated Gallium target;
- loading Vulkan Turnip 25.0.7;
- opening `/dev/kgsl-3d0` through Turnip's KGSL backend;
- identifying Adreno 650;
- creating an OpenGL ES 3.2 context;
- creating and rendering to a pbuffer;
- completing `glClear` and `glFinish`;
- reading the rendered result back;
- receiving the expected pixel value.

This is a real offscreen rendering milestone, not merely driver enumeration.

## Validation boundary

This milestone does **not** validate:

- Wayland presentation;
- dma-buf interoperability between KGSL and downstream `msm_drm`;
- common buffer formats or modifiers;
- GBM;
- KMS scanout of buffers produced by KGSL;
- accelerated Phoc;
- onscreen rendering;
- Wayland synchronization;
- long-duration stability;
- GPU suspend/resume;
- recovery after a GPU hang or reset.

The next action must be a static audit of the Wayland/dma-buf presentation
path before any attempt to use this renderer with Phoc.
