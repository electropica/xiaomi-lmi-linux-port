# Project architecture

This document describes the current repository architecture for the Xiaomi
Redmi K30 Pro / POCO F2 Pro (`lmi`) Mobian port.

Historical experiments remain available under `historical/`, but they must not
be used to infer the current build procedure when an active implementation
exists.

## Active repository

The active repository is:

    /home/linuxagent/ProjetMobian

The repository is organized by functional domain:

- `base/` — M0/base-rootfs construction inputs and scripts
- `display/` — display and Weston integration
- `wifi/` — QCA6390 Wi-Fi integration
- `bluetooth/` — Bluetooth-related integration
- `gpu/` — current GPU firmware, runtime and source provenance
- `phosh/` — current Mobian/Phosh userspace build
- `apps/` — optional application installation
- `kernel/` — kernel-side files and patches used by the userspace project
- `docs/` — current status, architecture and validation documentation
- `historical/` — superseded experiments and historical project material
- `output/` — generated images and other build artifacts

Generated build artifacts belong in `output/` and are not part of the source
history.

## Build layers

The project has three distinct layers.

### Base rootfs

The M0/base-rootfs construction scripts are under:

    base/scripts/

Their associated files are under:

    base/files/

This layer is separate from the current Phosh/userspace build.

### Phosh/userspace

The current Phosh/userspace build entry point is:

    phosh/scripts/build-m1-phosh.sh

The repository-level orchestrator is:

    build.sh

Optional applications are installed through:

    apps/scripts/install.sh

The optional application step is enabled with:

    INSTALL_OPTIONAL_APPS=1

A userspace-only or application-only change does not by itself require a kernel
rebuild.

### Kernel

Kernel development remains separate from userspace image construction.

The active kernel source repository is maintained independently at:

    /home/linuxagent/linux-sm8250-xiaomi-lmi

Kernel rebuilds are performed only when kernel-side changes require them.

## GPU

The current userspace GPU runtime is under:

    gpu/files/gpu72/

It contains the validated GPU72 runtime libraries, ICD configuration, canonical
Mesa source patch and source provenance.

The canonical Mesa source baseline is upstream Mesa 25.0.7.

Historical GPU generations and intermediate experiments are retained under
`historical/` where useful, but are not the current runtime.

## Historical material

`historical/` exists deliberately.

It records previous approaches, failed experiments, diagnostic milestones and
superseded implementations. A historical document may accurately describe the
state at the time it was written without describing the current project state.

Current architecture and build documentation take precedence over historical
procedures.

## Output policy

Large generated artifacts such as root filesystems, raw userdata images,
Android sparse images and build caches are excluded from Git.

The latest validated build artifacts may remain locally under `output/` as
validation references without being committed.
