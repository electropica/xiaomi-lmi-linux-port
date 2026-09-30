# Repository architecture

This is the unified source and evidence repository for Xiaomi Redmi K30 Pro /
POCO F2 Pro (`lmi`, Qualcomm SM8250). The tree separates kernel-side work,
userspace integration, build inputs, provenance, hardware-validation records,
and superseded experiments. All paths in this guide are repository-relative.

## Domains

- `kernel/configs/`, `kernel/patches/`, `kernel/diagnostics/`, and
  `kernel/tools/` are reserved for kernel-specific source-side material.
  The tracked D-v43 config and three patches are not a complete kernel source
  tree or a claim of binary provenance.
- `userspace/` holds Mobian/Phosh, GPU, display, Wi-Fi, Bluetooth, base-rootfs,
  application, audio, and camera integration. GPU runtime files are maintained
  under `userspace/gpu/files/`; proprietary Android firmware must not be added.
- `build/userdata/` contains the portable derived-userdata builder, tests,
  profiles, and text manifests. Its golden raw/sparse images, package cache,
  firmware input, outputs, and `state-*` directories remain external or ignored.
- `build/locks/userspace/` contains the text-only archi-validation-02 lock,
  directly at that path, plus package-cache provenance manifests.
- `build/kernel/` documents the kernel build boundary. The currently tested
  D-repro boot is external; the derived-userdata builder never rebuilds it.
- `docs/status/`, `docs/validation/`, `docs/architecture/`, and
  `docs/provenance/` contain current status, dated evidence, design notes, and
  source-history records respectively.
- `historical/` holds superseded D-v43/OpenRC and Weston experiments,
  historical M0/GPU evidence, and imported project history. Such procedures
  do not override later hardware-validated state.
- `tools/` is for generic project utilities; kernel-specific tooling belongs
  under `kernel/tools/`.

## Build layers and validated boundaries

The Mobian image orchestrator is `build/build-mobian-image.sh`; it invokes
`userspace/phosh/scripts/build-m1-phosh.sh`. Optional apps are installed from
`userspace/apps/scripts/install.sh`. M0/base-rootfs construction inputs and
scripts are under `userspace/base/`. These procedures may consume external
inputs and do not imply that a clean source-only image rebuild is currently
possible.

The `archi-validation-02` golden userspace and its `daily-base` derivative
were booted on hardware with the separate D-repro D-v43 boot. Phosh, touch,
DSI-1, and GLES2 → Zink → Turnip → KGSL/Adreno 650 were validated. The
`daily-base-audio-fw-test` derivative is experimental: direct ALSA playback
works, but volume is very low and user-facing PipeWire/UCM2 routing is not
finished. None of the images, boot binaries, or proprietary TFA firmware is
tracked here.

The separate D-v43/OpenRC reconstruction validated direct DRM/KMS test
rectangles, not Weston or a graphical session. Historical M0 Weston success
belongs to a distinct Mobian environment. Likewise, `archi-validation-02`,
the historical M1/GPU72 userdata, and the D-v43/OpenRC rootfs are different
userspace identities and must not be conflated.

The text lock allows manifest verification after clone and records exact
external inputs. The builder can derive functionally equivalent userdata
without rebuilding the kernel; a complete bit-for-bit rebuild from all
historical sources has not been demonstrated. Consult
[`docs/status/CURRENT-BUILD.md`](../status/CURRENT-BUILD.md),
[`docs/status/MOBIAN-STATUS.md`](../status/MOBIAN-STATUS.md), and the dated
records in `docs/validation/` before treating a historical procedure as
current.

## Exclusions

Do not track raw or sparse images, boot images, root filesystems, `.deb`/APK
archives, package caches, generated build states or outputs, proprietary
firmware, device secrets, credentials, private keys, PINs, machine IDs, real
MAC addresses, or complete private logs. Builder-local `.gitignore` files
provide additional protection for private inputs and outputs.
