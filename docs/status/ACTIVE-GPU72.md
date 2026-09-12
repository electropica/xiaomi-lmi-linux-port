# Active GPU72 baseline

This is a documentation snapshot for migration planning, not a deployment
instruction. All paths below retain their existing historical names and
locations. The SHA-256 companion file is `ACTIVE-GPU72-SHA256SUMS`; its paths
are relative to `/home/linuxagent/pmos-d-repro-01`.

## Canonical commits and active paths

- `5e6dbb0` - GPU71 integrated the validated Zink/Turnip/KGSL Phosh stack.
- `30505f7` - GPU72 validated Wayland Turnip and fixed the Zink runtime.
- `98d88a9` - GPU72 built the validated rootfs with the `mobian` account;
  this was the canonical `github-export` HEAD and `origin/main` at capture.
- Boot image: `/home/linuxagent/pmos-d-repro-01/output/D-repro-01-kernel-Dv43-qca6390-v2-complete-fcsource-boot.img`.
- Flashable rootfs ext4: `/home/linuxagent/pmos-d-repro-01/Mobian-M0/Mobian-M0-GPU_root.ext4`.
- Unpacked rootfs: `/home/linuxagent/pmos-d-repro-01/Mobian-M0/rootfs-final-gpu72`.
- Active GPU72 integration bundle, historically named GPU71:
  `/home/linuxagent/pmos-d-repro-01/analysis/gpu71-mobian-gles2-integration`.
- GPU72 Meson build tree:
  `/home/linuxagent/pmos-d-repro-01/analysis/gpu72-zink-dmabuf-fd-leak/build`.
- Canonical rootfs recipe:
  `/home/linuxagent/pmos-d-repro-01/github-export/Mobian-M0/build-unshare-330-inner.sh`.
- Local package-closure manifest:
  `/home/linuxagent/pmos-d-repro-01/Mobian-M0/manifests/m0-minimal-closure.tsv`.

The ext4 image has label `pmOS_root` and UUID
`dba94dfe-0fb9-4f95-970e-22949f4e69dc`. The boot image command line
contains `pmos_root_uuid=dba94dfe-0fb9-4f95-970e-22949f4e69dc` and
`pmos_boot_uuid=7bd723c2-51d6-4015-b28b-2b38191bf765`.

The rootfs has user `mobian` UID/GID `1000:1000`. Its group memberships are
`audio` (29), `video` (44), `plugdev` (46), `input` (996), and `render` (992).
The GPU72 validation reported Phoc `FD_TOTAL=100` and `DMABUF_FD=4`.
Those FD values are recorded validation results, not a new measurement made
during this documentation-only phase.

## Validated architecture and runtime selection

Display: Phoc 0.46 / wlroots 0.18.2 -> `msm_drm` -> SDE/DSI.
Rendering: Zink -> Turnip -> KGSL -> Adreno 650. Native Freedreno on the
downstream `msm_drm` node is not the validated rendering path.

The active `phosh-m0.service` records the following GPU/display selection:

```text
WLR_RENDERER=gles2
WLR_BACKENDS=drm,libinput
WLR_DRM_DEVICES=/dev/dri/card0
LD_LIBRARY_PATH=/opt/mobian-gpu/lib
VK_ICD_FILENAMES=/opt/mobian-gpu/icd.d/freedreno_icd.aarch64.json
MESA_LOADER_DRIVER_OVERRIDE=msm
ZINK_ALLOW_KGSL_DISPLAY_DEVICE=1
```

The integration bundle supplies EGL, GLESv2, Gallium, Turnip, the Vulkan ICD
manifest, A650 firmware, Phoc configuration, the Phosh systemd unit, and KGSL
and ION udev rules. Its installer copies these into the rootfs without
requiring the bundle directory to be renamed. The SHA-256 values of the
active Gallium and Turnip libraries match the GPU72 build outputs.

## PROVENANCE GPU72 NON ENCORE AUTONOME

The GPU72 build's `meson-info/intro-buildsystem_files.json` identifies
`/home/linuxagent/pmos-d-repro-01/analysis/gpu69-msm-drm-alias/mesa-25.0.7`
as its configured Mesa source directory. GPU72's cross-file uses the GPU68
`gpu68-aarch64-gcc` wrapper and GPU68 `sysroot-combined` for target headers,
libraries, and pkg-config. The copied build script under GPU72 still names
and points to GPU69; it is not an independent GPU72 build recipe.

The configured GPU69 `zink_screen.c` and the GPU72 source copy differ at the
`DMA_BUF_IOCTL_EXPORT_SYNC_FILE` failure path. The GPU72 copy logs the error
and closes the fd; the current GPU69 file has different error handling. Their
respective hashes are recorded in the companion SHA-256 manifest. This source
divergence must be resolved before claiming source-level reproducibility.

The active bundle and GPU72 build-tree Gallium share SHA-256
`6d06feb371beef2e39b4d386e1ded3b6c17babfac580894f5f779cf84344211e`.
The Gallium in `gpu72-zink-dmabuf-fd-leak/export/lib` instead has SHA-256
`5b06529d18721ba6f7cd54f77c9a6e9bd6f3c873509b24b4a0635acfd7138b76`
and is not the active Gallium artifact. Do not select outputs by directory
name alone.

No GPU68 or GPU69 directory may be archived until the exact GPU72 source,
patch set, toolchain, sysroot, options, and artifact hashes have been captured
and an autonomous replacement build has been verified. Existing Meson/Ninja
build trees must not be moved directly.

## M1 GPU72 userdata build validated on hardware

The canonical M1 userdata recipe has now been updated to embed the validated
GPU72 runtime directly from:

`/home/linuxagent/pmos-d-repro-01/github-export/mobian/m1-phosh/gpu72`

The recipe is:

`/home/linuxagent/pmos-d-repro-01/github-export/mobian/m1-phosh/build-m1-phosh.sh`

The validated M0 source tree used by the recipe was:

`/home/linuxagent/pmos-d-repro-01/Mobian-M0/rootfs-m0-display-work`

The exact M0 base userdata image was:

`/home/linuxagent/pmos-d-repro-01/output/Mobian-M0-userdata-rootfs-330-display-preflight.img`

The successful M1/GPU72 build produced:

- root ext4 size: `4294967296` bytes
- outer raw size: `4551868416` bytes
- sparse image size: `1924112200` bytes
- root filesystem: `37286/241152 files`, `477299/1048576 blocks`
- rootimg SHA-256: `ef7eac1587d22eedcf5d36c6bb0dcfea9a1e58f422b9ccfee63446be117bd48f`
- raw SHA-256: `b238ca99e9e8ed8c83547ed9cb7c4985efe7b4a3b067da43896e360328d8f3e0`
- sparse SHA-256: `d3c865f8e51e2006668e22654f2b78e0466c75b2028361f99a23ed4218e85bdc`

The flashable sparse image was:

`/home/linuxagent/pmos-d-repro-01/output/Mobian-M1-GPU72-userdata-phosh-4G.android-sparse.img`

A copy transferred to Windows was SHA-256 verified before flashing.

The image was flashed to `userdata` in fastbootd and booted successfully on
the Poco F2 Pro. Phosh was functional, GPU rendering was functional, and
GNOME Settings was visible.

### Runtime proof from the running Phoc process

The running `phoc` process mapped the GPU72 runtime from `/opt/mobian-gpu`:

- `/opt/mobian-gpu/lib/libEGL.so.1.0.0`
- `/opt/mobian-gpu/lib/libGLESv2.so.2.0.0`
- `/opt/mobian-gpu/lib/libgallium-25.0.7.so`
- `/opt/mobian-gpu/lib/libvulkan_freedreno.so`

The same Phoc process had the following GPU/display device nodes open:

- `/dev/dri/card0`
- `/dev/dri/renderD128`
- `/dev/ion`
- `/dev/kgsl-3d0`

The Phoc journal provides direct renderer confirmation:

`Initializing DRM backend for /dev/dri/card0 (msm_drm)`

`ZINK: using explicit Turnip cross-device display override`

`Using OpenGL ES 3.2 Mesa 25.0.7`

`GL renderer: zink Vulkan 1.3(Turnip Adreno (TM) 650 (MESA_TURNIP))`

The physical DSI output was detected and modeset at:

`1080x2400 @ 60.337 Hz`

This validates the runtime architecture on the rebuilt M1 image as:

Phoc / wlroots -> msm_drm -> DSI

and:

GLES2 -> Zink -> Vulkan -> Turnip -> KGSL -> Adreno 650

No llvmpipe or softpipe renderer was selected.

### System Gallium coexistence explained

The running Phoc process also maps Debian's:

`/usr/lib/aarch64-linux-gnu/libgallium-25.0.7-2+deb13u1.so`

This is not evidence of a software-rendering fallback.

`ldd /usr/lib/aarch64-linux-gnu/gbm/dri_gbm.so` proves that the Debian
`dri_gbm.so` module directly depends on
`libgallium-25.0.7-2+deb13u1.so`.

Therefore both Gallium libraries legitimately coexist in the Phoc address
space:

- Debian Gallium is pulled in by the system GBM DRI backend.
- `/opt/mobian-gpu/lib/libgallium-25.0.7.so` belongs to the validated
  GPU72 EGL/Zink runtime.

The renderer selected by Phoc remains explicitly confirmed as Zink on Turnip
for the Adreno 650.

### Remaining known GPU72 diagnostic

The session still emits repeated:

`DMA_BUF_IOCTL_EXPORT_SYNC_FILE failed: errno=25`

The error does not prevent the validated hardware-rendered Phosh session from
starting and operating. It remains a known GPU72 diagnostic and does not
invalidate the M1/GPU72 hardware-rendering milestone.

The source-level provenance warning above remains in force: this successful
M1 integration validates deployment and runtime behavior, but does not yet
make the GPU72 Mesa build provenance autonomous from GPU68/GPU69.
