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
