# Mobian M1 A650 Turnip/KGSL hardware validation — 2026-09-08

## Scope

This note records the first hardware validation of Mesa Turnip using the
Qualcomm KGSL kernel interface on Xiaomi `lmi` (SM8250 / Adreno 650):

```text
Vulkan loader
    -> Mesa Turnip 25.0.7
    -> KGSL backend
    -> /dev/kgsl-3d0
    -> Qualcomm Adreno 650
```

The validated result is Vulkan physical-device enumeration. It is an
important prerequisite for accelerated graphics, but is not yet proof of GPU
command submission or rendered output.

## Why Turnip/KGSL and Zink

The Debian Mesa 25.0.7 source contains Freedreno Gallium and Turnip, but their
kernel interfaces differ. In this release Gallium Freedreno supports the DRM
MSM KMD, while the native Gallium KGSL backend is still described as planned
or in progress. The apparent `kgsl_dri.so` name is only a DRI alias and does
not provide that missing Gallium backend. The stock Debian arm64 build also
leaves `freedreno-kmds` at its default `msm` value, so its Turnip library does
not compile `tu_knl_kgsl.cc` and never opens `/dev/kgsl-3d0`.

Mesa 25.0.7 does, however, contain a real KGSL backend for Turnip. Zink can
provide OpenGL and OpenGL ES above Vulkan without requiring native Gallium
Freedreno/KGSL. This establishes the intended staged path:

```text
OpenGL / OpenGL ES
    -> Gallium Zink
    -> Vulkan Turnip
    -> KGSL
```

Only the Turnip/KGSL portion of that path is validated here.

## A650 firmware provenance and kernel state

The installed A650 firmware was extracted from the exact Xiaomi `lmi` global
Android ROM used by the project,
`lmi_global_images_V14.0.1.0.SJKMIXM_20230317.0000.00_12.0_global`. The
relevant firmware set is:

- `a650_sqe.fw`
- `a650_gmu.bin`
- `a650_zap.mdt`
- `a650_zap.b00`
- `a650_zap.b01`
- `a650_zap.b02`

The downstream Qualcomm 4.19 kernel exposed `/dev/kgsl-3d0`, and opening that
device as the `mobian` user had already succeeded. During the validated GPU
cycle the kernel also reported:

```text
subsys-pil-tz soc:qcom,kgsl-hyp: a650_zap: loading ...
subsys-pil-tz soc:qcom,kgsl-hyp: a650_zap: Brought out of reset
```

No proprietary firmware is stored in this repository.

## Isolated Mesa 25.0.7 build

The source reference was Debian Mesa `25.0.7-2+deb13u1`. The required Meson
selection was:

```text
gallium-drivers=zink
vulkan-drivers=freedreno
freedreno-kmds=msm,kgsl
```

The resulting Turnip compilation enabled both `TU_HAS_MSM` and
`TU_HAS_KGSL`, selected `src/freedreno/vulkan/tu_knl_kgsl.cc`, and retained
Zink, EGL, GLES2 and the surfaceless platform for the next validation stage.
It was staged and transferred as an isolated runtime rather than replacing
the phone's system Mesa installation.

### Cross-build correction

The first WSL cross-build route was rejected as a deployable result after its
standard-library and export audit showed contamination between the Ubuntu
host toolchain environment and the intended Debian Trixie target. It was not
sufficient merely to point selected dependencies at a Trixie sysroot while
the AArch64 compiler continued to resolve parts of its standard environment
from the host cross-toolchain.

The accepted artifact was rebuilt natively inside the Debian Trixie ARM64
environment, executed on the host through QEMU/binfmt. This made the build
environment and runtime ABI match the target distribution and removed the
Ubuntu/Debian cross-environment ambiguity.

## Validated artifact identity

Primary hardware-tested artifact:

| Property | Value |
|---|---|
| File | `libvulkan_freedreno.so` |
| Mesa version | `25.0.7` |
| Architecture | AArch64 |
| Backend | Turnip KGSL |
| SHA-256 | `dc46ac80f2322142e5ba17235e7cfd019f13c41157a34965cc5494622b84324d` |

The isolated ICD and libraries were transferred to a dedicated location on
the phone. System Mesa was not replaced.

## GPU-54F2 hardware result

The test forced the isolated Freedreno ICD and enabled Turnip startup
diagnostics. Turnip reported:

```text
TU: info: Created an instance
TU: info: Found compatible device '/dev/kgsl-3d0'.
```

`vulkaninfo` then enumerated:

```text
apiVersion         = 1.3.305
driverVersion      = 25.0.7
vendorID           = 0x5143
deviceID           = 0x6050002
deviceType         = PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU
deviceName         = Turnip Adreno (TM) 650
driverID           = DRIVER_ID_MESA_TURNIP
driverName         = turnip Mesa driver
driverInfo         = Mesa 25.0.7
conformanceVersion = 1.2.7.1
```

`VULKANINFO_RC=0`.

This directly validates that the Vulkan loader loaded the isolated Mesa
Turnip driver, that its KGSL backend opened `/dev/kgsl-3d0`, and that it
identified the physical GPU as Adreno 650.

## Validation boundary

This milestone does **not** yet validate:

- GPU command submission or rendered pixels;
- EGL context creation;
- OpenGL or OpenGL ES;
- Zink at runtime;
- Wayland presentation;
- dma-buf import/export interoperability (subsequently validated within
  Turnip/KGSL by GPU-58, but not yet with downstream `msm_drm`);
- GBM;
- accelerated Phoc;
- KMS scanout using KGSL-produced buffers;
- long-duration stability;
- suspend/resume;
- GPU reset handling.

That next experiment was subsequently completed as GPU-55: an isolated EGL
surfaceless context rendered and read back a verified pixel through Zink and
Turnip/KGSL without involving KMS output. See
`mobian-m1-a650-zink-turnip-kgsl-offscreen-hardware-validation-2026-09-08.md`.
GPU-58 later validated Turnip/KGSL dma-buf export and same-driver re-import;
see `mobian-m1-a650-turnip-kgsl-dmabuf-hardware-validation-2026-09-08.md`.
