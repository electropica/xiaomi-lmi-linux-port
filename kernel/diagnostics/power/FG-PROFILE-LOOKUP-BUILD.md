# FG profile lookup: operator kernel-only build

This builds the current qualified kernel configuration and six existing patches
plus the phandle-first lookup candidate. It is not a rootfs build. No firmware,
battery calibration, protection value, profile payload or device tree policy is
changed. The code candidate remains unvalidated on the handset.

## Prerequisites and preflight

The current WSL environment retains the exact a5b3099017ae source archive in
dv43-pmbootstrap-work/cache_distfiles, native Alpine Clang/LLD22.1.8, and the
qualified config in kernel/diagnostics/audio/state-power-rpmh-votes-reviewed.
All archive/config/patch hashes are enforced. An explicit --config may point to
another retained copy only if its bytes match the qualified SHA256. The
compiler archive and package identities remain documented in the original
audio/RPMh recipe; this script reuses its compiler flags and host probes.

Run without --execute for preflight only. The archive hash and seven-patch
application order were checked successfully on October23. This does not compile
or enter the chroot. In build mode, version checks, dynamic/static link probes
and olddefconfig run before the Image target. Any config-byte change aborts.

## Operator command in WSL

```sh
sudo python3 /home/linuxagent/xiaomi-lmi-linux-port/kernel/diagnostics/power/build-fg-profile-lookup-kernel.py --execute --jobs 4
```

The operator launches this potentially long build. Source and object files stay
in one newly marked lmi-fg-lookup-* directory inside the existing native chroot.
At least12GiB free is required. Existing stages, inputs, reference kernels and
boot images are never overwritten or automatically deleted. BUILD_STATE is
printed immediately; BUILD_STATUS remains INCOMPLETE unless the complete Image
and its receipt have been written.

Expected final marker:

```text
FG_PROFILE_KERNEL_BUILD_COMPLETE_NOT_FOR_FLASHING
IMAGE=...
SHA256=...
RESULT=...
```

## Artifact boundary

The output is a kernel Image, NOT a flashable boot image. It must be repacked
later with the qualified dedicated-Mobian ramdisk, DTB and boot metadata. Do
not flash it directly or replace the permanent dualboot menu. Boot packaging
and any temporary device test are separate guarded operations after inspecting
the build receipt. No such action is performed by this script.

Acceptance tests the final recognized j11sun profile and design capacity, not
absence of every transient startup retry. Record learned-capacity changes:
the unmodified successful profile-load path can update that capacity. Standby
measurement is separate and must not include the loading/calibration transition.
