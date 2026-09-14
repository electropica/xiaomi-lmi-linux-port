# Current validated build

This document identifies the current validated Mobian/Phosh userspace build
for Xiaomi `lmi`.

## Current hardware state

The current validated device state is substantially beyond the early bring-up
described in historical documentation.

Validated current foundations include:

- persistent boot on Xiaomi `lmi`
- Debian/Mobian userspace
- systemd
- Phosh
- functional internal display
- touch input
- USB networking and SSH
- Wi-Fi
- GPU acceleration path validated through the current GPU72 runtime

Temporary `fastboot boot` procedures and early Weston-only display bring-up are
historical milestones rather than the normal current startup procedure.

## Current userspace build

The latest functional userspace build is:

    output/archi-validation-01.img

Its Android sparse image is:

    output/archi-validation-01.img.android-sparse.img

The Android sparse image is the build currently validated on the phone.

### SHA-256

Work ext4:

    60de98660991379cb1d463ebadc7de43b73242d68f73502308e3891d2350844d

Raw userdata image:

    559d6c44f2aa2223f91fd8af1db7a838b8183d7a223ceb80f7bdd13a9b6e31e4

Android sparse userdata image:

    f61c19a09881c9a7ac165cc5e36ab08f146d65acddae2de18a6bb555c10663b3

### Sizes

Final ext4 filesystem:

    4294967296 bytes

Raw userdata image:

    4551868416 bytes

Android sparse userdata image:

    2834813356 bytes

Both `e2fsck` validation passes completed cleanly during this build.

## Build entry points

Repository orchestrator:

    build.sh

Current Phosh/userspace builder:

    phosh/scripts/build-m1-phosh.sh

Optional application installer:

    apps/scripts/install.sh

The optional application layer is enabled with:

    INSTALL_OPTIONAL_APPS=1

## Current optional application set

The current selected optional application packages are:

- epiphany-browser
- gnome-console
- gnome-calculator
- gnome-text-editor
- papers
- showtime
- gnome-clocks
- gnome-weather
- gnome-contacts
- gnome-calls
- chatty
- megapixels
- gnome-calendar
- gnome-maps
- geary
- amberol
- krecorder
- koko

## GPU source state

The active GPU72 runtime is stored under:

    gpu/files/gpu72/

Its canonical source provenance is documented in:

    gpu/files/gpu72/SOURCE-PROVENANCE.md

The validated source reconstruction is upstream Mesa 25.0.7 plus the canonical
GPU72 patch.

## Important separation of concerns

The current M0/base-rootfs chain, current Phosh/userspace chain and kernel
build are separate.

The separate `/home/mobian1/mobian-device` workflow is also not a replacement
for the current `phosh/scripts/build-m1-phosh.sh` image-production chain.

## Known deferred work

The following are intentionally deferred and are not blockers for the current
repository migration:

- phone audio
- Chinese-character rendering in Debian

They should be handled as separate follow-up work after the repository
migration is finalized.
