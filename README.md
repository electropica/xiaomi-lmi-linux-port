# Xiaomi LMI Linux Porting

Experimental Linux porting work for the Xiaomi Redmi K30 Pro / POCO F2 Pro (`lmi`, Qualcomm SM8250).

This repository collects reproducible source-side work for postmarketOS packaging, downstream kernel diagnostics, DRM/KMS display takeover, and ongoing Mobian/Debian userspace bring-up.

## Current status

### Boot

A Qualcomm downstream Linux 4.19 kernel has been booted successfully on the device using a temporary `fastboot boot` workflow.

The working reference uses:

- Xiaomi `lmi` / SM8250
- downstream kernel `4.19.325`
- postmarketOS initramfs
- RNDIS USB networking
- SSH access
- DRM/KMS on the internal DSI panel

Binary boot images and generated userdata images are intentionally not stored in this repository.

### Display

The internal panel is functional through DRM/KMS.

The main display path is:

- DRM device: `card0`
- output: `DSI-1`
- mode: `1080x2400`
- Qualcomm downstream atomic KMS

A major blocker was traced to the bootloader/continuous-splash KMS state.

Before userspace display takeover, the downstream SDE driver retained a continuous-splash association involving CRTC 129 and plane 58. A direct Weston atomic commit could therefore fail even though the panel and DRM device were otherwise functional.

The validated sequence is:

1. perform the historical KMS takeover with `modetest`;
2. release CRTC 129 and plane 58;
3. verify the cleared KMS state;
4. start seat management;
5. start Weston;
6. disable the Qualcomm `Virtual-1` output;
7. enable `DSI-1`.

With this sequence, Weston completes the atomic commit and page flip and renders successfully on the physical display.

### Weston control

A minimal Weston configuration has been validated with:

- Weston 14.0.2
- DRM backend
- Pixman renderer
- kiosk shell
- `DSI-1`
- `Virtual-1` disabled
- no VT requirement
- seatd with VT binding disabled

A solid-colour screen was used as the hardware-visible validation target.

### USB / SSH

The postmarketOS initramfs creates a ConfigFS RNDIS gadget before `switch_root`.

Observed working state includes:

- gadget: `g1`
- function: `rndis.usb0`
- UDC: `a600000.dwc3`
- VID:PID: `0525:a4a2`
- device address: `172.16.42.1`
- host address: `172.16.42.2`

The gadget has been observed to survive `switch_root`.

### Mobian / Debian

A minimal Debian trixie arm64 userspace is currently being prepared as the first Mobian-oriented milestone.

The initial goal is deliberately smaller than a complete mobile desktop:

```text
downstream kernel
    -> Debian/systemd
    -> USB networking + SSH
    -> KMS continuous-splash release
    -> seat management
    -> Weston
    -> visible DSI output
```

Phosh and a complete Mobian environment will be investigated only after this minimal userspace milestone is reproducible.

## Repository layout

```text
pmaports/
    postmarketOS device and downstream-kernel packaging for lmi

mobian/
    Debian/Mobian bootstrap and reproducibility tooling

weston/
    display-control image tooling and Weston/KMS experiments

historical/
    historical porting notes, diagnostics and reproducibility scripts
```

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
