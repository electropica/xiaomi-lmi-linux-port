# Xiaomi LMI Linux Porting

Experimental Linux porting work for the Xiaomi Redmi K30 Pro / POCO F2 Pro (`lmi`, Qualcomm SM8250).

This repository collects reproducible source-side work for postmarketOS packaging, downstream kernel diagnostics, DRM/KMS display takeover, and ongoing Mobian/Debian userspace bring-up.

## Current status

Xiaomi Redmi K30 Pro / POCO F2 Pro (`lmi`) now boots into a functional Debian/Mobian Phosh environment.

The current validated foundation includes persistent device boot, Debian GNU/Linux 13 with systemd, the internal DSI display and touch input, Phosh, USB networking and SSH, QCA6390 Wi-Fi, and the validated GPU72 Mesa/Turnip/KGSL acceleration path.

The temporary `fastboot boot`, Weston-only, Pixman-only and earlier GPU experiments documented elsewhere in the repository are historical milestones and do not represent the normal current startup state.

The latest validated userspace image and its hashes are documented in `docs/CURRENT-BUILD.md`.

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
