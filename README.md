# Xiaomi LMI Linux Porting

Experimental Linux porting work for the Xiaomi Redmi K30 Pro / POCO F2 Pro (`lmi`, Qualcomm SM8250).

This repository collects reproducible source-side work for postmarketOS packaging, downstream kernel diagnostics, DRM/KMS display takeover, and ongoing Mobian/Debian userspace bring-up.

## Current status

The current validated Mobian/Phosh userspace baseline is the external
`archi-validation-02` golden userdata; its `daily-base` derivative was also
validated on Xiaomi `lmi`. With the original D-repro D-v43 boot, Phosh,
touch/unlock, DSI-1 and the GLES2 → Zink → Turnip → KGSL/Adreno 650 path were
observed working. Their images are external artifacts, not files in this
repository.

The distinct `daily-base-audio-fw-test` profile has progressed beyond the
initial no-card blocker: WCD938x/TFA9874 and direct ALSA playback work, but
the audible level is extremely low and user-facing PipeWire/UCM2 routing is
unfinished. Audio is therefore only partially functional. Proprietary TFA
firmware remains outside Git.

The separate D-v43/OpenRC reconstruction has visible direct DRM/KMS test
rectangles, but no working persistent compositor; Weston D-v43 tests remained
black. This is not the successful Weston 14 result from the distinct
historical M0 Mobian environment.

The latest userspace identities and the boundaries between the golden,
derived, and experimental profiles are documented in
[`docs/CURRENT-BUILD.md`](docs/CURRENT-BUILD.md) and
[`docs/status/MOBIAN-STATUS.md`](docs/status/MOBIAN-STATUS.md). The dated
hardware milestones, including the current partial-audio result, are indexed
under [`docs/validation/`](docs/validation/).

The current repository architecture and active build entry points are documented in `docs/ARCHITECTURE.md`.

## Repository layout

- `base/` — M0/base-rootfs files and construction scripts
- `display/` — display integration
- `wifi/` — QCA6390 Wi-Fi integration
- `bluetooth/` — Bluetooth integration
- `gpu/` — current GPU runtime, firmware, patches and provenance
- `phosh/` — current Mobian/Phosh userspace construction
- `apps/` — optional application installation
- `kernel/` — kernel-side integration files
- `docs/` — current architecture, build, status and validation documentation
- `historical/` — superseded experiments and historical material
- `output/` — generated local artifacts excluded from Git

See `docs/ARCHITECTURE.md` for the authoritative current architecture.

## Reproducibility

The project aims to keep the port reproducible from source and configuration rather than distributing generated device images.

Where practical, experiments record:

- exact kernel and device-tree inputs;
- configuration and patches;
- build commands and scripts;
- relevant package versions;
- hashes of generated artifacts;
- hardware observations and validation criteria.

Generated root filesystems, Android images, build caches and other large artifacts are intentionally excluded from Git.

## Project status

This is an experimental downstream Linux port.

The repository documents successful hardware milestones as well as failed experiments and diagnostic work. Not every historical script or experiment represents the current recommended configuration.

Do not assume that an image or procedure is safe to flash merely because it appears in the historical documentation.

## Contributing

Contributions are welcome, particularly for:

- Xiaomi Redmi K30 Pro / POCO F2 Pro (`lmi`) hardware support;
- SM8250 downstream and mainline investigation;
- postmarketOS packaging;
- Debian/Mobian userspace integration;
- DRM/KMS and DSI display support;
- USB gadget networking;
- reproducible build and diagnostic tooling;
- documentation and independent hardware validation.

Please avoid committing proprietary firmware, generated Android images, private keys, credentials, device identifiers or other sensitive artifacts.

## License

See `LICENSE` and `NOTICE` for licensing information.

Individual imported patches or source fragments may retain their original upstream licensing and copyright notices.
