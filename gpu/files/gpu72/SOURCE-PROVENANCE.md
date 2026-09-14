# GPU72 Mesa source provenance

## Upstream source

Mesa version:

`25.0.7`

Canonical upstream archive:

`https://archive.mesa3d.org/mesa-25.0.7.tar.xz`

SHA256:

`592272df3cf01e85e7db300c449df5061092574d099da275d19e97ef0510f8a6`

The historical GPU72 source tree was compared directly against a freshly
extracted copy of this archive.

The historical tree contained Debian packaging metadata for
`25.0.7-2+deb13u1`, but dry-run verification established that none of the
patches listed in `debian/patches/series` were applied to the Mesa source used
for GPU72.

Therefore the source baseline for the validated GPU72 build is upstream Mesa
25.0.7, not Debian-patched Mesa.

## GPU72 patch

Canonical patch:

`patches/0001-gpu72-lmi-zink-turnip-kgsl-msm-drm.patch`

SHA256:

`d2f522c08b3bc344a371ed9626c15a3e5f77014c19b6cbc805fb6338e550128d`

The patch contains 646 lines and modifies exactly these six upstream files:

- `src/egl/drivers/dri2/platform_wayland.c`
- `src/freedreno/drm/freedreno_device.c`
- `src/gallium/auxiliary/pipe-loader/pipe_loader_drm.c`
- `src/gallium/drivers/zink/zink_screen.c`
- `src/gallium/frontends/dri/dri_util.c`
- `src/gallium/frontends/dri/kopper.c`

The patch includes the diagnostic instrumentation present in the validated
GPU72 binaries and the two identified functional GPU-specific changes:

- recognition of `msm_drm` as an alias for the Freedreno `msm` DRM driver;
- explicit Turnip/KGSL display-device selection through
  `ZINK_ALLOW_KGSL_DISPLAY_DEVICE`.

Binary inspection of the validated GPU72 payload confirmed the corresponding
diagnostic and functional strings in `libEGL.so.1.0.0` and
`libgallium-25.0.7.so`.

## Patch reproducibility check

The canonical patch was tested with:

`patch -p1 --dry-run`

against a freshly extracted upstream Mesa 25.0.7 source tree.

All six files applied cleanly and the command returned exit status `0`.

Thus the canonical reconstruction of the GPU72 Mesa source layer is:

`mesa-25.0.7.tar.xz -> apply canonical GPU72 patch`

No historical modified Mesa working tree is required to reproduce this source
state.

## Host cross-toolchain

The validated GPU72 build uses the following Ubuntu host cross-toolchain packages:

- `gcc-15-aarch64-linux-gnu` — `15.2.0-16ubuntu1cross1` — amd64
- `g++-15-aarch64-linux-gnu` — `15.2.0-16ubuntu1cross1` — amd64
- `binutils-aarch64-linux-gnu` — `2.46-3ubuntu2` — amd64
- `libgcc-15-dev-arm64-cross` — `15.2.0-16ubuntu1cross1` — all

The canonical GCC wrapper resolves `/usr/bin/aarch64-linux-gnu-gcc` to
`/usr/bin/aarch64-linux-gnu-gcc-15` and uses the GCC 15 cross include directory:

`/usr/lib/gcc-cross/aarch64-linux-gnu/15/include`

The target sysroot remains the preserved Debian arm64/trixie historical sysroot documented above.
