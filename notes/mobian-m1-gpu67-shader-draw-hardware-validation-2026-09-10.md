# Mobian M1 GPU-67 shader draw hardware validation - 2026-09-10

## Scope

GPU-67 validates one minimal programmable OpenGL ES shader draw on Xiaomi
`lmi` / POCO F2 Pro through the isolated, patched Mesa 25.0.7 path:

```text
Mesa EGL
    -> Gallium
    -> built-in patched Zink
    -> system Vulkan loader
    -> isolated GPU-53 Turnip
    -> Adreno 650 KGSL
```

The probe compiled a GLES2 vertex shader and fragment shader, linked them,
submitted one full-screen triangle with `glDrawArrays(GL_TRIANGLES, 0, 3)`,
finished the work and read back a 4x4 RGBA8 pbuffer. All 16 pixels matched the
shader-selected value `RGBA 0,255,0,255`.

The test was offscreen only. It did not present pixels to Wayland, Phoc, GBM,
DRM/KMS or `DSI-1`, and it did not replace system Mesa.

## Relationship to GPU-66

GPU-66 established EGL and Zink initialization, selection of the isolated
GPU-53 Turnip ICD and KGSL path, GLES context creation, and one 1x1 clear plus
readback. That operation did not exercise an application vertex or fragment
shader.

GPU-67 reused the same hash-verified runtime and selection model. It adds the
first validated programmable pipeline boundary: shader compilation, program
linking, a triangle draw, rasterization, framebuffer writes and multi-pixel
readback through the same Zink/Turnip/KGSL chain.

## Probe identity

| Property | Value |
|---|---|
| Target path | `/root/gpu66-isolated-egl-bundle/bin/gpu67-shader-probe` |
| Architecture | AArch64 |
| SHA-256 | `9398fa97a303008d4f12ab351158b0255d71cc19f2778badf48912ee6b3baaf9` |
| EGL surface | 4x4 RGBA8 pbuffer |
| Depth/stencil | None |
| Multisampling | None |
| Draw calls | One |
| Readbacks | One 4x4 RGBA/unsigned-byte readback |
| Execution count | One |
| Exit code | `0` |

The probe used client-side `vec2` position data for the oversized triangle:

```text
(-1, -1), (3, -1), (-1, 3)
```

All 4x4 pixel centers lie strictly inside that triangle. `GL_DITHER` was
disabled. The pbuffer was first cleared to opaque red (`255,0,0,255`), while
the fragment shader selected opaque green (`0,255,0,255`). The differing
colors make the successful result evidence of shader-produced framebuffer
writes rather than repetition of the clear result.

## Shaders

Vertex shader:

```glsl
attribute vec2 a_position;

void main()
{
    gl_Position = vec4(a_position, 0.0, 1.0);
}
```

Fragment shader:

```glsl
precision mediump float;

void main()
{
    gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0);
}
```

The offline source and ELF audit confirmed exactly one `glDrawArrays`
callsite, exactly one `glReadPixels` callsite, and no rendering or benchmark
loop. The only loop was bounded to validation of the 16 returned pixels.

## Isolated runtime

GPU-67 used the existing isolated directory and the same five per-process
selection variables validated by GPU-66:

```text
LD_LIBRARY_PATH=/root/gpu66-isolated-egl-bundle/lib
EGL_PLATFORM=surfaceless
MESA_LOADER_DRIVER_OVERRIDE=zink
ZINK_ALLOW_KGSL_DISPLAY_DEVICE=1
VK_DRIVER_FILES=/root/gpu66-isolated-egl-bundle/icd.d/freedreno_icd.aarch64.json
```

The bundle supplied the matching Mesa EGL, GLES2 and Gallium libraries plus
the GPU-53 Turnip ICD and its manifest. The normal Debian Vulkan loader and
runtime libraries remained outside the bundle. System Mesa remained installed
at `25.0.7-2+deb13u1` and was not modified.

The probe and all four reused runtime artifacts matched their expected hashes
before execution and again afterward:

| Artifact | SHA-256 |
|---|---|
| GPU-67 shader probe | `9398fa97a303008d4f12ab351158b0255d71cc19f2778badf48912ee6b3baaf9` |
| GPU-66 `libEGL.so.1.0.0` | `1a3f94dd32bf565c91c9d53c0deb6d140236d62ea9b9b47c27cd74484b40e73d` |
| GPU-66 `libGLESv2.so.2.0.0` | `d981fcec76e341a6a4cf898d605c789e09343e7aa1510bc3de283a57f4929782` |
| GPU-66 `libgallium-25.0.7.so` | `4c0b75982a0a16be6fd2ef79aa3fc2d4096dc11f88803b21fe6fb4ff05f1d4c8` |
| GPU-53 `libvulkan_freedreno.so` | `dc46ac80f2322142e5ba17235e7cfd019f13c41157a34965cc5494622b84324d` |

## Hardware result

GPU-67D executed the probe exactly once. Its complete decisive output was:

```text
MESA: info: ZINK: using explicit Turnip cross-device display override
EGL_DISPLAY_CREATED=YES
EGL_INITIALIZE=PASS
EGL_VENDOR=Mesa Project
EGL_VERSION=1.5
EGL_API_VERSION=1.5
CONFIG_SELECTED=YES
CONFIG_RGBA8=YES
CONFIG_DEPTH_STENCIL=0,0
CONFIG_MSAA=NO
API_BOUND=OPENGL_ES
CONTEXT_CREATED=YES
PBUFFER_CREATED=YES
PBUFFER_SIZE=4x4
MAKE_CURRENT=YES
GL_VENDOR=Mesa
GL_RENDERER=zink Vulkan 1.3(Turnip Adreno (TM) 650 (MESA_TURNIP))
GL_VERSION=OpenGL ES 3.2 Mesa 25.0.7
CLEAR_RGBA=255,0,0,255
VERTEX_SHADER_COMPILED=YES
FRAGMENT_SHADER_COMPILED=YES
PROGRAM_LINKED=YES
POSITION_ATTRIBUTE=READY
DRAW_SUBMITTED=YES
RENDER_COMPLETED=YES
PIXELS_VALIDATED=16
EXPECTED_RGBA=0,255,0,255
RENDER_VERIFIED=YES
PROBE_EXIT_CODE=0
```

Together with the statically audited probe, the red initial clear, green
shader output, one submitted triangle and exact 64-byte readback establish:

- successful GLES2 vertex shader compilation;
- successful GLES2 fragment shader compilation;
- successful program linking;
- shader execution;
- one `glDrawArrays(GL_TRIANGLES, 0, 3)` submission;
- triangle rasterization into the 4x4 RGBA8 pbuffer;
- shader-produced framebuffer writes;
- one 4x4 RGBA readback; and
- verification of all 16 pixels as `0,255,0,255`.

The renderer identity and explicit cross-device override message, combined
with the unchanged isolated runtime identities and previously validated
GPU-66 loader/ICD path, establish that the draw used patched Zink, the system
Vulkan loader, isolated Turnip, KGSL and Adreno 650.

## Safety result

Phoc remained running as PID 3254, Phosh remained running as PID 3346 and
`DSI-1` remained connected. No bundle process remained after the probe.

The kernel interval contained the expected A650 ZAP firmware power-up lines:

```text
a650_zap: loading ...
a650_zap: Brought out of reset
```

The latter is normal firmware initialization, not fault recovery. No new GPU,
KGSL, IOMMU or page fault, hang, timeout, fault recovery, Oops, BUG or panic
was observed. No system library, package, service or configuration was
modified.

## Exact validation boundary

GPU-67 validates one small programmable GLES2 triangle draw and deterministic
offscreen readback through patched Zink, Turnip, KGSL and Adreno 650. It does
not establish:

- general GLES2 correctness;
- general GLES3 correctness;
- texture sampling;
- uniform handling;
- VBO or VAO correctness;
- FBO rendering;
- large render targets;
- sustained rendering;
- performance;
- long-term stability;
- Wayland acceleration;
- Phoc acceleration;
- dma-buf interoperability;
- GBM;
- KMS or DSI presentation;
- desktop OpenGL; or
- production readiness.

Visible display acceleration and desktop integration remain separate future
milestones.
