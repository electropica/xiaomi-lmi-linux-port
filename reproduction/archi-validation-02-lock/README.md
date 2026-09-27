# archi-validation-02 userspace reproduction lock

This directory locks the validated Xiaomi `lmi` userspace independently from
kernel construction. It contains no image, package archive, binary payload,
credential, log, cache, or phone-derived secret.

## Validated state

The phone was running Debian 13.6 (`trixie`, arm64), systemd 257.13,
Phosh/Phoc 0.46 and the GPU72 GLES2 -> Zink -> Turnip -> KGSL -> Adreno 650
path. Phosh was visible and unlockable; GNOME Console and Calculator worked.
The live Phoc process loaded the four locked `/opt/mobian-gpu` libraries,
opened DRM render/card nodes, KGSL and ION, and reported OpenGL ES 3.2 Mesa
25.0.7 with the Turnip Adreno 650 renderer.

Chatty's GStreamer diagnostics are deliberately outside this lock's scope.

## Four distinct objects

1. The active RAM boot is
   `D-repro-01-kernel-Dv43-qca6390-v2-complete-fcsource-boot.img`, SHA-256
   `0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad`.
2. The flashed userdata source is
   `archi-validation-02.img.android-sparse.img`, SHA-256
   `84182b57edb7be8e49c29e0f0b472e9b6a54f7efa645ef99664dc0e004759f78`.
3. `/boot/boot.img` inside that userdata is a different file, SHA-256
   `1fbfe7cbfd6d8a7faf444409291abb665f7458a36b21cdc3d4438302c66e7e99`.
   It does not identify the RAM boot currently executing.
4. The live filesystem contains generated machine state, user state and
   runtime state. Those data are not source inputs and are excluded.

See `BOOT-USERSPACE-CONTRACT.md` for the compatibility boundary.

## Reproducibility levels

- **Exact clone:** copy the existing sparse image byte-for-byte and verify its
  SHA-256. This is possible now.
- **Functional equivalence:** derive a new userdata from the verified rootfs,
  locked packages and local overlay while retaining the D-repro boot. This is
  feasible without rebuilding the kernel or GPU72.
- **Bit-for-bit source rebuild:** not currently established. The historical M0
  package closure/cache, original base tree, GPU sysroot and complete GPU72
  build invocation are not all present.

`PACKAGES.tsv`, `LOCAL-FILES.tsv`, `SYSTEMD-UNITS.tsv` and `GPU72.tsv` are
stable, machine-readable inputs. `ARTIFACTS.tsv` records absolute paths from
the validated source workstation as documentary provenance; none of those
images or binaries is stored in this Git repository.

`verify-archi-validation-02-lock.sh --manifest-only` validates the versioned
metadata after any clone and does not require the phone or external artifacts.
On the validated workstation,
`verify-archi-validation-02-lock.sh --full` additionally checks every external
artifact, the extracted rootfs, Android sparse magic, ext4 UUID, persistent
files, GPU72 payload and APT extended state. `ARCHI_ROOTFS` may override the
default extracted-rootfs path; paths in `ARTIFACTS.tsv` remain documentary and
must exist exactly for full verification.

## Complete package cache

The complete 1,086-package `.deb` closure and its provenance are recorded in
[`deb-cache/`](deb-cache/README.md). The cache archives and its deterministic
tar are external artifacts and are not stored in Git. After obtaining the
cache directory, verify it offline with:

```sh
deb-cache/verify-deb-cache.sh /path/to/archi-validation-02-deb-cache
```

The verifier accepts the cache directory explicitly, compares its package
triplets with this lock, validates every `.deb` with `dpkg-deb`, and checks
all archive SHA-256 values.
