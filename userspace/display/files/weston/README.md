# Weston DRM backend for downstream `msm_drm`

The downstream SM8250 DRM driver may report the same fourcc more than once
through the legacy plane-format API when no `IN_FORMATS` blob is available.
Weston 14.0.2 asserts when that indistinguishable format is added twice. The
patch in `patches/` de-duplicates only that legacy fallback list.

There are three distinct evidence levels:

1. The Weston archive and source patch are hash-locked and reproducible.
2. The build recipe has separately locked manifests for the native amd64
   tools and the target arm64/all development sysroot.
3. The exact experimental backend validated on Xiaomi `lmi` hardware is an
   evidence artifact. Its hash is not a promised output of a future build.

## Build contract

`build-drm-backend.sh` requires eight explicit inputs: the locked Weston
archive, both locked `libdisplay-info` Debian arm64 packages, a directory of
locked target development `.deb` files and its manifest, a separate directory
of locked native amd64 `.deb` files and its manifest, and a new output
directory. It constructs both roots only from verified manifest entries and
never uses target libraries from the host filesystem.

The three build layers are deliberately distinct:

1. Meson, Ninja, the cross compiler, and other build-machine programs are
   native amd64 tools. `wayland-scanner` and its runtime closure are extracted
   from the packages in `native-tools-manifest.tsv` and run through their
   extracted loader; `/usr/bin/wayland-scanner` is not used.
2. Headers, libraries, and target pkg-config metadata come only from the 167
   arm64/all packages in `development-sysroot-manifest.tsv`.
3. The Weston archive and downstream-MSM source patch are independently
   hash-locked inputs.

Weston resolves `dependency('wayland-scanner', native: true)` through native
pkg-config metadata. The recipe therefore generates a private
`wayland-scanner.pc` whose tool variable points to a workdir wrapper. Native
pkg-config sees only that private directory; target pkg-config sees only the
arm64 sysroot. Architecture-independent `wayland-protocols` XML data remains
in the target corpus but is consumed by the native scanner.

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
