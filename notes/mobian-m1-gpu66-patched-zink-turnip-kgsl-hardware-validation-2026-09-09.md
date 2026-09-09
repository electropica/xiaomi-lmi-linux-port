# Mobian M1 GPU-66 patched Zink/Turnip/KGSL hardware validation - 2026-09-09

## Scope

GPU-66 validates that a patched Mesa 25.0.7 Zink implementation can perform
real offscreen OpenGL ES rendering on Xiaomi `lmi` / POCO F2 Pro through:

```text
Mesa EGL
    -> Gallium
    -> built-in Zink
    -> system Vulkan loader
    -> isolated GPU-53 Turnip
    -> Adreno 650 KGSL
```

The test used an isolated runtime bundle and did not replace or modify the
phone's system Mesa installation. It rendered one deterministic green pixel
and read back `RGBA 0,255,0,255`.

This is distinct from the earlier GPU-55 native-build offscreen result. GPU-66
specifically validates the opt-in Zink cross-device selection change and the
corrected Debian Trixie ABI of the cross-compiled EGL/Gallium stack.

## Milestone progression

| Stage | Result |
|---|---|
| GPU-66G | Identified host cross-link contamination through `atan2f@GLIBC_2.43`. |
| GPU-66J | Validated that prioritizing the Debian Trixie sysroot `libm` selects `atan2f@GLIBC_2.17`. |
| GPU-66N | Created a fresh corrected build and validated its Gallium and EGL artifacts offline. |
| GPU-66P | Passively verified the target architecture, ABI, Vulkan loader, KGSL node and isolated-location prerequisites over SSH. |
| GPU-66Q | Transferred and hash-verified the isolated EGL initialization bundle without execution. |
| GPU-66R | Validated isolated EGL initialization through patched Zink, GPU-53 Turnip and KGSL. |
| GPU-66S | Built and statically validated the minimal 1x1 GLES2 rendering probe offline. |
| GPU-66T | Transferred and hash-verified the GLES frontend and rendering probe without execution. |
| GPU-66U | Executed the rendering probe once and validated the deterministic readback on hardware. |

## Zink cross-device change

The GPU-65 source change is opt-in through:

```text
ZINK_ALLOW_KGSL_DISPLAY_DEVICE=1
```

When normal display-device matching does not select a Vulkan physical device,
the change accepts exactly one physical device whose Vulkan driver ID is
`VK_DRIVER_ID_MESA_TURNIP`. It rejects an ambiguous set containing multiple
Turnip devices. GPU-66R and GPU-66U both logged:

```text
MESA: info: ZINK: using explicit Turnip cross-device display override
```

The tested `zink_screen.c` SHA-256 was:

```text
c2a4b24cea19736776db125ec75a700fd1179149eebbb42817a547bffbb19f4b
```

## Direct-linked Mesa architecture

The successful configuration does not use:

- `zink_dri.so`;
- `libdril_dri.so`;
- GBM;
- GLX;
- Wayland;
- X11.

Mesa 25.0.7 exposes the built-in Zink implementation through the Gallium
target. The tested frontend relationships are:

```text
libEGL.so.1
    -> libgallium-25.0.7.so
    -> built-in Zink

libGLESv2.so.2
    -> libgallium-25.0.7.so
```

The EGL surfaceless platform and a 1x1 pbuffer required no window system,
GBM allocation, KMS operation or physical-display surface.

## Cross-link ABI correction

The initial GPU-65 Gallium artifact was rejected because it resolved the
undefined `atan2f` reference against the Ubuntu host cross-toolchain `libm`:

```text
OLD_ATAN2F_VERSION=GLIBC_2.43
OLD_MAX_GLIBC=GLIBC_2.43
```

Adding the Debian Trixie AArch64 sysroot library directory to both C and C++
link arguments, ahead of `-lm`, produced:

```text
NEW_ATAN2F_VERSION=GLIBC_2.17
NEW_MAX_GLIBC=GLIBC_2.38
NEW_GLIBC_2_43=NO
```

The target runs Debian 13.6 AArch64 with glibc 2.41. Its inspected ABI ceilings
were GLIBC 2.41, GLIBCXX 3.4.33 and CXXABI 1.3.15, satisfying the corrected
GPU-66 requirements.

## Validated artifact identities

| Artifact | SHA-256 |
|---|---|
| Corrected GPU-65 `libEGL.so.1.0.0` | `1a3f94dd32bf565c91c9d53c0deb6d140236d62ea9b9b47c27cd74484b40e73d` |
| Corrected GPU-65 `libgallium-25.0.7.so` | `4c0b75982a0a16be6fd2ef79aa3fc2d4096dc11f88803b21fe6fb4ff05f1d4c8` |
| Matching GPU-65 `libGLESv2.so.2.0.0` | `d981fcec76e341a6a4cf898d605c789e09343e7aa1510bc3de283a57f4929782` |
| GPU-53 `libvulkan_freedreno.so` | `dc46ac80f2322142e5ba17235e7cfd019f13c41157a34965cc5494622b84324d` |
| GPU-53 ICD manifest | `636bd4b12e5e9bffa2599aca7cf9792e37103ff7469d0b3174da6e838dd68da7` |
| EGL initialization probe | `8cb72b2c10b549a1fb8373b9e63cff4c1230f8fbd96c365f6d2bff8650e6ecbd` |
| 1x1 GLES2 rendering probe | `5d0b385dfdb8b56c76e5c1dadcc859b1ec5445bd603ed7817584b768a50a2636` |

## Isolated runtime

The validated phone directory was:

```text
/root/gpu66-isolated-egl-bundle/
  bin/egl-surfaceless-probe
  bin/gpu66s-render-probe
  icd.d/freedreno_icd.aarch64.json
  lib/libEGL.so.1 -> libEGL.so.1.0.0
  lib/libEGL.so.1.0.0
  lib/libGLESv2.so.2 -> libGLESv2.so.2.0.0
  lib/libGLESv2.so.2.0.0
  lib/libgallium-25.0.7.so
  lib/libvulkan_freedreno.so
  src/egl-surfaceless-probe.c
```

The per-process selection environment was:

```text
LD_LIBRARY_PATH=/root/gpu66-isolated-egl-bundle/lib
EGL_PLATFORM=surfaceless
MESA_LOADER_DRIVER_OVERRIDE=zink
ZINK_ALLOW_KGSL_DISPLAY_DEVICE=1
VK_DRIVER_FILES=/root/gpu66-isolated-egl-bundle/icd.d/freedreno_icd.aarch64.json
```

The bundle supplied EGL, GLES2, Gallium, the Turnip ICD, its manifest and the
probes. Normal Debian runtime libraries and the system Vulkan loader remained
outside the bundle. The system loader was
`/usr/lib/aarch64-linux-gnu/libvulkan.so.1.4.309` from
`libvulkan1:arm64 1.4.309.0-1` and supported `VK_DRIVER_FILES`.

`SYSTEM_MESA_MODIFIED=NO` throughout the validation.
The installed system Mesa packages remained at version `25.0.7-2+deb13u1`.

## EGL initialization result

GPU-66R executed the initialization probe once. It established:

```text
EGL_DISPLAY_CREATED=YES
EGL_INITIALIZE=PASS
EGL_VENDOR=Mesa Project
EGL_VERSION=1.5
ZINK_SELECTED=YES
GPU53_TURNIP_SELECTED=YES
KGSL_PATH_REACHED=YES
VULKAN_PHYSICAL_DEVICE_EXPOSED=YES
PROBE_EXIT_CODE=0
```

The Vulkan loader selected the isolated manifest and reported one physical
device, `Turnip Adreno (TM) 650`. Zink logged that the explicit Turnip
cross-device display override was used.

## One-pixel rendering result

The GPU-66S probe used the GLES2 API frontend with one 1x1 RGBA8 pbuffer. It
created no Wayland, X11, GBM, DRM or KMS object and contained no device path,
networking, subprocess, filesystem-output, loop or benchmark code.

GPU-66U executed this rendering probe exactly once. Complete decisive output
was:

```text
MESA: info: ZINK: using explicit Turnip cross-device display override
EGL_DISPLAY_CREATED=YES
EGL_INITIALIZE=PASS
EGL_VENDOR=Mesa Project
EGL_VERSION=1.5
EGL_API_VERSION=1.5
CONFIG_SELECTED=YES
API_BOUND=OPENGL_ES
CONTEXT_CREATED=YES
PBUFFER_CREATED=YES
MAKE_CURRENT=YES
GL_VENDOR=Mesa
GL_RENDERER=zink Vulkan 1.3(Turnip Adreno (TM) 650 (MESA_TURNIP))
GL_VERSION=OpenGL ES 3.2 Mesa 25.0.7
RENDER_COMPLETED=YES
PIXEL_RGBA=0,255,0,255
RENDER_VERIFIED=YES
GPU66U_PROBE_EXIT_CODE=0
```

The bounded operation was one green `glClear`, `glFinish`, and a four-byte
`glReadPixels` verification. This establishes actual offscreen GPU rendering,
not only EGL initialization or Vulkan physical-device enumeration.

## Safety result

The rendering validation was deliberately limited to one tiny offscreen
operation. Its recorded safety result was:

```text
PHONE_ACCESSED=YES
ACCESS_METHOD=SSH
ADB_USED=NO
FASTBOOT_USED=NO
PROBE_EXECUTION_COUNT=1
KERNEL_CRASH=NO
GPU_FAULT=NO
PHOC_LEFT_RUNNING=YES
PHOSH_LEFT_RUNNING=YES
DSI1_CONNECTED_AFTER=YES
SYSTEM_MESA_MODIFIED=NO
```

Phoc retained PID 3245, Phosh retained PID 3337 and `DSI-1` remained
connected. No GPU fault, hang, timeout, kernel Oops, BUG or panic was observed.
No service, package or system configuration was modified, and no second
rendering execution occurred.

## Exact validation boundary

GPU-66 proves that the patched, corrected Mesa 25.0.7 Zink build can perform
one real offscreen OpenGL ES render through the isolated GPU-53 Turnip/KGSL
ICD on Adreno 650 while the normal Phoc/Phosh session remains running and
system Mesa remains unchanged.

It does not validate:

- general desktop OpenGL;
- Wayland rendering or presentation;
- Phoc rendering through Zink;
- KMS or DSI rendering through Zink;
- GPU acceleration for the complete desktop;
- production readiness;
- general Vulkan application compatibility;
- all GLES or OpenGL functionality;
- performance;
- prolonged rendering stability;
- suspend/resume or GPU fault recovery.

Those remain separate interoperability, integration and stability milestones.
