# Outer menu recipe from the 27 November test

This directory contains the menu sources, pinned EDK revisions and warning fixes used in the preparation of menu `1426e2e8…`. The phone booted Mobian after Fastboot reported that image written to `boot`. The exact installed partition was not read back and the Android menu entry was not retested with that image.

The scripts here are adapted to accept caller-provided directories and bundle hashes rather than the original workstation paths. **The adapted wrapper has only been checked in plan mode and has not itself produced a menu.** Its output is a candidate for offline inspection and temporary boot, not an automatic installation. The historical build used the pinned source revisions, the included DevicePath, BaseTools, linker and VFR changes, `ENABLE_LINUX_UTILS=0`, and an x86-64 Debian bookworm build root.

## Inputs kept outside Git

* A pre-existing menu toolchain directory containing `rootfs/.lmi-bootstrap-complete`, `source/edk2-msm` with the objects in `sources.lock.json`, and `inputs/android.img` and `inputs/android-dtbo.img` matching the pinned hashes. Rebuilding that rootfs is covered by the [earlier menu recipe](../README.md).
* An independently verified directory with `lmi-outer-linux7.bin` and `BUNDLE_RESULT.json`. The [kernel recipe](../../../kernel/experimental/linux7/reconstruction-20261127/README.md) can prepare a kernel-only candidate from the retained working bundle; firmware and generated images are not included here.
* A new build directory with at least 3 GiB free. The source clone borrows the existing Git object stores read-only and is not a complete standalone archive.

```sh
export LMI_MENU_TOOLCHAIN_ROOT=/absolute/path/to/menu-toolchain
export LMI_MENU_BUILD_ROOT=/absolute/path/to/new-menu-work
export LMI_MENU_BUNDLE_DIR=/absolute/path/to/verified-bundle
export LMI_MENU_BUNDLE_SHA256=the_64_character_lowercase_sha256_of_the_bundle
python3 preflight.py
sudo --preserve-env=LMI_MENU_TOOLCHAIN_ROOT,LMI_MENU_BUILD_ROOT,LMI_MENU_BUNDLE_DIR,LMI_MENU_BUNDLE_SHA256 bash build.sh --build
```

The wrapper checks the recipe manifest, bundle hash and pinned revisions, refuses to overwrite its output, isolates the mounts and does not contact a phone. The supplied hash establishes integrity against the caller's expectation, not that the new bundle has been qualified. Revalidate the generated Android header, menu entries, Mobian boot and recovery before considering any flash.
