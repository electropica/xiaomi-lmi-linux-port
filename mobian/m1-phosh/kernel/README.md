# Kernel DV43 provenance

Upstream repository:

https://github.com/LineageOS/android_kernel_xiaomi_sm8250.git

Upstream branch:

lineage-23.2

Exact base commit:

a5b3099017ae581aae8bf597b2f9c8c765026af1

Base subject:

power: supply: ti: bq2597x: fix void pointer to int cast

The validated DV43 source adds exactly two project-local commits on top of that base:

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

Reconstruction order:

1. Obtain LineageOS android_kernel_xiaomi_sm8250.
2. Check out exact base a5b3099017ae581aae8bf597b2f9c8c765026af1.
3. Apply patch 0001.
4. Apply patch 0002.

The resulting project-local commit sequence corresponds to the validated DV43 source history.
