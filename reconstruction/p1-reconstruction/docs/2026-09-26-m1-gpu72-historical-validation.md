# Historical M1/GPU72 hardware validation — 2026-09-26

The strongest previously validated graphical build for Xiaomi `lmi` was the
M1/GPU72 Mobian userspace: Debian 13 (Trixie), systemd, Phosh 0.46 and Phoc
0.46. Its rendering chain was GLES2 → Mesa Zink → Vulkan Turnip → KGSL →
Adreno 650, with Phoc/wlroots driving the downstream `msm_drm` DSI output.

The documented boot image was:

`/home/linuxagent/pmos-d-repro-01/output/D-repro-01-kernel-Dv43-qca6390-v2-complete-fcsource-boot.img`

with SHA-256
`0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad`.
The matching flashable userdata was:

`/home/linuxagent/pmos-d-repro-01/output/Mobian-M1-GPU72-userdata-phosh-4G.android-sparse.img`

with SHA-256
`d3c865f8e51e2006668e22654f2b78e0466c75b2028361f99a23ed4218e85bdc`.
The sparse userdata remains absent locally. The same boot identity is now
available from the separate Windows Downloads copy used for the 2026-09-27
`archi-validation-02` validation; the historical output path above remains
absent.

The hardware evidence is explicit: GPU-55 created and read back an EGL
OpenGL ES 3.2 pbuffer through Turnip/KGSL; GPU-66 and GPU-67 validated the
patched Zink EGL/GLES path and shader draw; GPU-68 produced the first visible
Phosh desktop through GLES2/Zink/Turnip/KGSL, with DSI-1 enabled at
1080×2400@60. Phosh, touch/unlock and GNOME Settings were observed on the
M1/GPU72 family of images. This is materially different from merely finding
graphics packages in an image.

This record must not be conflated with
`archi-validation-02.img.android-sparse.img` (SHA-256
`84182b57edb7be8e49c29e0f0b472e9b6a54f7efa645ef99664dc0e004759f78`). At
the date of this historical note that image had only been inspected offline.
It was subsequently booted and graphically validated on 2026-09-27 with the
same D-repro boot identity; that later result is recorded separately and does
not make it the missing M1/GPU72 sparse userdata.

M1/GPU72 remains the priority historical reference for OS and application
work. Its original sparse userdata must still be recovered or rebuilt; no
binary artifact is copied into this repository.

See [the 2026-09-27 userspace milestone](2026-09-27-archi-validation-02-userspace-lock.md)
for the later `archi-validation-02` hardware validation and reproduction lock.
