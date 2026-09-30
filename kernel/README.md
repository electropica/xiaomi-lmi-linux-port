# Kernel DV43 provenance

Upstream repository:

https://github.com/LineageOS/android_kernel_xiaomi_sm8250.git

Upstream branch:

lineage-23.2

Exact base commit:

a5b3099017ae581aae8bf597b2f9c8c765026af1

Base subject:

power: supply: ti: bq2597x: fix void pointer to int cast

The most advanced retained DV43 source lineage adds exactly two project-local commits on top of that base:

1. 3d6dacc48eda5acd59b40fedb33ae640e3164c1e
   mobian: add boot-safe QCA6390 UART support and restore VFS source fix

2. 40d333444f72188e5daf7860a41b6dfddd981705
   esoc: preserve crash state on late run notification

Canonical patch files:

patches/0001-mobian-add-boot-safe-QCA6390-UART-support-and-restor.patch
patches/0002-esoc-preserve-crash-state-on-late-run-notification.patch

Patch SHA256:

d193cfbaad83811703f5db5990eaa52358e1828af581e09c702f4efa10aec782  0001-mobian-add-boot-safe-QCA6390-UART-support-and-restor.patch
c94fe70ae385e1f74fb56566b9743d4b5df23b6fc42aeabecbdbee9c3a2004aa  0002-esoc-preserve-crash-state-on-late-run-notification.patch

Reconstruction order for the retained source lineage:

1. Obtain LineageOS android_kernel_xiaomi_sm8250.
2. Check out exact base a5b3099017ae581aae8bf597b2f9c8c765026af1.
3. Apply patch 0001.
4. Apply patch 0002.

The validated QCA6390 V2 + fcsource boot built on 5 September 2026 corresponds
to the source changes subsequently archived in patch 0001. Patch 0002 (ESOC)
is a later evolution from 6 September 2026. Applying 0001 + 0002 reconstructs
the most advanced retained historical DV43 source lineage, not the exact source content
of the reference boot below.

## Experimental CCI patch — not yet validated on hardware

`patches/0003-media-cam-cci-reject-file-ioctls.patch` changes only the
NULL-argument return in `cam_cci_subdev_ioctl()` from `rc` (zero) to
`-ENOTTY`. The CCI file-operation wrappers continue to pass NULL; the
valid-argument path is unchanged. This rejects unsupported file ioctls
instead of reporting false success, which can cause endless
`VIDIOC_ENUMINPUT` enumeration in GStreamer discovery triggered by Chatty.

Patch SHA256:

```text
4c8716cce129981c856be91b09ef4ba13bf06ba2fbf3d5e0458e742fa90dd6f0  0003-media-cam-cci-reject-file-ioctls.patch
```

For an experimental source tree, apply 0003 after 0001 and 0002 on the
exact base above. Sequential application was checked against all nine
affected source files from that commit. No kernel was compiled and no
hardware test was performed. The 0001 + 0002 + 0003 lineage is experimental
and is not a validated kernel or boot reference.

## Exact configuration of the 5 September reference boot

`configs/dv43-qca6390-v2.config` contains exactly the decompressed IKCONFIG
bytes extracted from the kernel embedded in the validated QCA6390 V2 +
fcsource boot. This is the configuration actually compiled into that kernel;
its SHA256 matches the final `.config` measured historically on 5 September.

Reference identities:

```text
config size: 174007 bytes
config SHA256: 6512a0c29ebf987d25c0cceb79917df32d6fed4b67e4c3b94bfad9fdb1745e37
boot: D-repro-01-kernel-Dv43-qca6390-v2-complete-fcsource-boot.img
boot SHA256: 0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad
kernel SHA256: 471aeec72355094754a82d478a9c4f8b4e8edb4b0a94368fb8fd594a776bbbfb
```
