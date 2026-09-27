# Validated archi-validation-02 userspace lock — 2026-09-27

## Hardware result

`archi-validation-02.img.android-sparse.img` was flashed as userdata and
actually booted on Xiaomi `lmi` with the D-repro D-v43 RAM boot. Their SHA-256
identities are respectively:

- `84182b57edb7be8e49c29e0f0b472e9b6a54f7efa645ef99664dc0e004759f78`;
- `0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad`.

Phosh was visible, unlockable and usable. The real Phoc renderer journal
reported OpenGL ES 3.2 Mesa 25.0.7 and established the accelerated GLES2 →
Zink → Vulkan Turnip → KGSL → Adreno 650 path. GNOME Console and Calculator
were exercised successfully. Chatty remained open but repeatedly emitted
GStreamer diagnostics; that application-specific issue does not invalidate
the GPU or display result and was not investigated for this milestone.

## Reproduction boundary

The text-only lock under
[`reproduction/archi-validation-02-lock/`](../reproduction/archi-validation-02-lock/README.md)
captures:

- 1,086 installed packages with exact versions and architectures;
- 65 persistent, reconstruction-relevant files or links;
- APT sources, policy and extended-state fingerprint;
- systemd activation and the splash → seatd → Phoc/Phosh ordering;
- GPU72 libraries, ICD, A650 firmware, environment and device permissions;
- external artifact sizes and hashes;
- the D-repro boot/kernel, UUID, cmdline and userspace ABI contract;
- explicit secret, identity, cache, journal and runtime exclusions.

The active D-repro RAM boot is not `/boot/boot.img` stored inside the userdata.
The lock identifies both and forbids substituting one for the other.

The existing sparse image can be cloned byte-for-byte. A new functionally
equivalent userdata can be derived while keeping the validated boot/kernel.
Reconstruction bit-for-bit from source is not yet demonstrated because the
complete historical package objects, base tree, GPU sysroot and GPU72 build
closure are not all preserved.

No raw or sparse image, boot image, package archive, rootfs, GPU binary, full
journal, credential or phone-derived secret is stored in Git.
