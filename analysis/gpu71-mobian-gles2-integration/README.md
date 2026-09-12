# GPU72 Mobian lmi GLES2 integration

Validated architecture:

Phosh
→ Phoc 0.46
→ wlroots 0.18.2 GLES2
→ Mesa Zink
→ Turnip
→ KGSL
→ Adreno 650
→ downstream msm_drm display
→ DSI-1 1080x2400 at 60 Hz

## Required A650 firmware

- a650_sqe.fw
- a650_gmu.bin
- a650_zap.mdt
- a650_zap.b00
- a650_zap.b01
- a650_zap.b02
- a650_zap.elf

Install under:

/lib/firmware/postmarketos

Firmware mode:

0644

## Required device permissions

/dev/kgsl-3d0:

root:render
0660

udev rule:

KERNEL=="kgsl-3d0", GROUP="render", MODE="0660"

/dev/ion:

root:render
0660

udev rule:

KERNEL=="ion", GROUP="render", MODE="0660"

User mobian must belong to group render.

## Required Phoc environment

WLR_RENDERER=gles2
WLR_BACKENDS=drm,libinput
WLR_DRM_DEVICES=/dev/dri/card0
LD_LIBRARY_PATH=/opt/mobian-gpu/lib
VK_ICD_FILENAMES=/opt/mobian-gpu/icd.d/freedreno_icd.aarch64.json
MESA_LOADER_DRIVER_OVERRIDE=msm
ZINK_ALLOW_KGSL_DISPLAY_DEVICE=1

## Important architecture finding

The downstream DRM driver identifies as msm_drm.

Mesa native Freedreno DRM rendering cannot use this node because this downstream msm_drm implementation does not expose the upstream MSM GPU ioctl ABI required by Freedreno.

The validated rendering path is therefore:

Zink → Turnip → KGSL

The GPU69 Mesa patch allows msm_drm to pass the initial Freedreno device-name check, but native MSM rendering then fails on missing MSM_GET_PARAM support. It is retained here as source history and for the validated Mesa runtime.

ZINK_ALLOW_KGSL_DISPLAY_DEVICE=1 is required so Zink can select the Turnip KGSL physical device while wlroots uses the msm_drm display device.

## Validation results

GPU57 Vulkan external DMA-BUF self-test:

GPU57_DMABUF_SELFTEST=PASS
CONTENT_MATCH=PASS

GPU66 EGL surfaceless:

EGL initialized: 1.5
ZINK: using explicit Turnip cross-device display override

wlroots GLES2 probe:

WLROOTS_RENDERER_CREATE=PASS
DMABUF_TEXTURE_FORMAT_COUNT=50
DMABUF_RENDER_FORMAT_COUNT=50
PROBE_EXIT_CODE=0

Real Phoc process:

WLR_RENDERER=gles2
MESA_LOADER_DRIVER_OVERRIDE=msm
ZINK_ALLOW_KGSL_DISPLAY_DEVICE=1
VK_ICD_FILENAMES=/opt/mobian-gpu/icd.d/freedreno_icd.aarch64.json

Final validation:

phosh-m0.service active
Phoc active
Phosh active
DSI-1 enabled
1080x2400 at 60 Hz
visible Phosh display confirmed

## Rootfs integration

Run from this directory:

./INSTALL-IN-ROOTFS.sh PATH_TO_ROOTFS

Do not execute this script without supplying the intended future rootfs directory.

## Persistent rootfs permissions

Runtime libraries:

0755

Firmware:

0644

Vulkan ICD:

0644

udev rules:

0644

Phoc configuration:

0644

systemd unit:

0644

The mobian account must be a member of:

render

The installer modifies the render entry in /etc/group directly so this also works while preparing an ARM64 rootfs from an x86-64 WSL host without requiring a chroot.

## Service enablement

The installer creates:

/etc/systemd/system/graphical.target.wants/phosh-m0.service

pointing to:

../phosh-m0.service

This makes the validated Phosh session part of graphical.target in the future rootfs.
