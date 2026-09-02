# Weston DRM backend for downstream `msm_drm`

The downstream SM8250 DRM driver may report the same fourcc more than once
through the legacy plane-format API when no `IN_FORMATS` blob is available.
Weston 14.0.2 asserts when that indistinguishable format is added twice. The
patch in `patches/` de-duplicates only that legacy fallback list.

There are three distinct evidence levels:

1. The Weston archive and source patch are hash-locked and reproducible.
2. The build recipe is lockable, but refuses to run while
   `development-sysroot-manifest.tsv` is marked incomplete.
3. The exact experimental backend validated on Xiaomi `lmi` hardware is an
   evidence artifact. Its hash is not a promised output of a future build.

## Build contract

`build-drm-backend.sh` requires six explicit inputs: the locked Weston
archive, both locked `libdisplay-info` Debian arm64 packages, a directory of
locked development `.deb` files, its manifest, and a new output directory.
It constructs a clean sysroot only from verified manifest entries and never
uses target libraries from the host filesystem. Producing and reviewing the
complete Weston development closure remains a prerequisite before a fresh
build can be called fully reproducible.

The script verifies package identity and hashes, isolates `pkg-config`, applies
the patch non-interactively without reversal or fuzz, disables Meson network
fallbacks, builds only the DRM backend, and rejects an output that does not
target AArch64, that links against `libdisplay-info.so.3`, or that needs a
glibc symbol newer than 2.38. It is intentionally not run as part of
repository checkout or image assembly.

The exact experimental hardware-tested backend had SHA-256
`546664f37bbc85475a089f4e6cc3aa1f9478093c2e2addd95cc225a37e848fd3`.
Path-dependent debug information, build flags, toolchain, and the complete
sysroot are not yet sufficiently locked to require a new build to reproduce
that hash bit-for-bit.
No compiled backend, sysroot, package, source archive, rootfs, or image belongs
in Git.
