# Derived `archi-validation-02` userdata builder

This text-only builder derives a new userdata from the validated GPU72 Mobian
golden image. It does not build or replace the D-repro D-v43 boot/kernel. The
profiles and scripts here are versioned; input images, the 1,086-package cache,
generated images, and timestamped build states are external and are never
stored in this repository.

## Hardware-validated `daily-base` milestone — 2026-09-27

The daily-base sparse userdata
`archi-validation-02-derived-daily-base-20260927.img.android-sparse.img` was
flashed and booted on Xiaomi `lmi` with the durable D-repro boot. Phosh was
visible and usable; the unlock code worked and lock/unlock remained responsive.
DSI-1 was active, and the hardware GLES2 → Zink → Turnip → KGSL/Adreno 650 path
was confirmed. The time-seed floor was active, the restored time was not older
than its seed, and no new PAM “password changed in future” warning appeared.

The profile addresses two demonstrated issues without changing the golden or
kernel: the Poco's RTC is stuck in 1975 and not writable, so the system had
fallen back to 2026-04-13; and automatic startup of Chatty's daemon caused an
approximately one-minute unlock delay. `time-seed` initializes a root-only
UTC epoch from the build host and only advances a clock older than that floor.
`daily-base` additionally adds a per-user XDG autostart mask with
`Hidden=true` for `sm.puri.Chatty-daemon.desktop`. Chatty 0.8.7-2 remains
installed, its system entry is intact, and its manual launcher remains
available. The override is owned by `mobian:mobian`, mode 0644; no Chatty
process was running during validation.

Validated outputs (external to Git):

| Form | Filename | Size | SHA-256 |
| --- | --- | ---: | --- |
| Android sparse | `archi-validation-02-derived-daily-base-20260927.img.android-sparse.img` | 2,960,466,444 bytes | `172a4f950252e810f408bf4d5caf5075c699020e6a2198999f7f0b30c7f19928` |
| Raw | `archi-validation-02-derived-daily-base-20260927.img` | 4,551,868,416 bytes | `5cc226cd96c324b68d74e33eec461a091e7f5dd69b80e0529c2d0267cfa3cad5` |

The sparse expansion matched the raw image; GPT, partition UUIDs, the embedded
boot partition, and the boot/root filesystem UUIDs passed validation. The
build state directory was mode 0700 and owned by `nobody:nogroup`; it could not
be re-read by the operator without interactive sudo. This is an access limit
on retained build evidence, not a functional defect: image identity and the
sparse/raw round trip were checked independently, and the hardware boot was
observed.

## Reproduction boundary and external inputs

The active D-repro D-v43 boot is distinct from `/boot/boot.img` embedded in
userdata. This builder only modifies a copy of the rootfs partition and
requires its GPT, UUIDs, and entire embedded boot partition to remain intact.
Do not substitute another boot arbitrarily; use the lock's
[`BOOT-USERSPACE-CONTRACT.md`](../archi-validation-02-lock/BOOT-USERSPACE-CONTRACT.md).

At build time set these environment variables to external, verified inputs:

- `ARCHI_GOLDEN_RAW`: the 4,551,868,416-byte raw golden image, SHA-256
  `329e2124f97032a2f4b15167bbd9bbbd9395bb422f2794a2117ee610a2368f27`;
- `ARCHI_GOLDEN_SPARSE`: its 2,960,036,280-byte Android sparse source, SHA-256
  `84182b57edb7be8e49c29e0f0b472e9b6a54f7efa645ef99664dc0e004759f78`;
- `ARCHI_DEB_CACHE`: the verified directory containing exactly 1,086 `.deb`
  files (521,861,380 bytes total);
- `ARCHI_DEB_ARCHIVE`: the external deterministic cache archive, size
  523,274,240 bytes, SHA-256
  `65058c4bc74c6aea3854060a8e7b9a7617ea6aee66d503d90564bcee214a69fd`.

By default the text lock is resolved beside this directory at
`../archi-validation-02-lock`; `ARCHI_LOCK_DIR` can override that location.
The source workstation's historical paths are documented in
[`manifests/INPUTS.tsv`](manifests/INPUTS.tsv), not required to be reproduced
on another host. The builder's `--check-only` verifies lock checksums and the
1,086-package fingerprint locally; the lock's separate source-workstation
verifier additionally checks external extracted-rootfs evidence.

## Profiles and safety

- `baseline-nochange`: no declared functional changes. A read-write ext4 mount
  can change filesystem metadata, so byte identity is not expected.
- `time-seed`: host-UTC seed, systemd service and timer; requires explicit
  `--enable-hooks`.
- `daily-base`: `time-seed` plus only the user-level Chatty daemon autostart
  mask; Chatty stays installed and manually launchable. Requires explicit
  `--enable-hooks`.

The build copies raw with `cp --reflink=auto`, discovers partitions from GPT,
mounts only the root partition of the copy, and checks protected GPU72 files,
A650 firmware, display units/configuration, accounts/groups, package versions,
UUIDs, GPT, and embedded boot bytes. Cleanup is ownership-checked and
idempotent. The first-generation profiles deliberately preserve passwords,
PINs, machine-id, SSH/host keys, NetworkManager profiles, DConf and user state;
they are not sanitized automatically.

## Checks and commands

Offline source checks (no build, image copy or mount):

```sh
./verify-derived-userdata.sh --manifest-only
bash ./tests/test-loop-cleanup.sh
```

Example future `daily-base` preflight; use actual external input paths:

```sh
ARCHI_GOLDEN_RAW=/external/archi-validation-02.img \
ARCHI_GOLDEN_SPARSE=/external/archi-validation-02.img.android-sparse.img \
ARCHI_DEB_CACHE=/external/archi-validation-02-deb-cache \
ARCHI_DEB_ARCHIVE=/external/archi-validation-02-deb-cache-1086-20260927.tar \
./build-derived-userdata.sh --profile daily-base --version daily-base-YYYYMMDD --enable-hooks --check-only
```

The equivalent real build requires root and is intentionally not run as part
of this documentation milestone. Output images are created with new names
under `outputs/`; existing outputs are refused. `state-*` and output payloads
are ignored by Git. Review hooks before explicitly enabling them.
