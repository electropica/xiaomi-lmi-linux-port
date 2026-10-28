# lmi Linux7 experimental checkpoint

This branch isolates the7.2.12 bring-up from the working downstream4.19 system.
The operator temporarily booted a RAM observer and recovered its live USB log.
TLMM GPIO exclusions28-31/40-43 were required to cross the earlier binding
stall in this trial. See the [hardware record](../../../docs/validation/lmi-linux7-menu-host-check-2026-10-26.md).

## Current hardware qualification

## Rear camera sensor binding prepared — October 28, 2026

The rear sensor of this board never binds on this kernel, and the cause is
now known: the `ov13b10` driver of the 7.2.12 tree carries only an ACPI match
table, so an OF-described sensor is never matched. The driver is built in and
registers, the i2c client exists with the compatible string, and no probe
happens. The board device tree already satisfies the driver, so the change is
a driver patch.

The deliverable is `patches/0004-lmi-ov13b10-of-match.patch`, together with
`configs/camera.fragment` and `tools/check-camera-patch.sh`. The host check
passes: the patch applies to the pinned tree and to the community tree that
produced the handset kernel, the patched driver compiles, the configuration
resolves, and the device tree needs no change. Nothing has been flashed, so
no binding is claimed on the handset yet. See the
[validation record](../../../docs/validation/lmi-linux7-camera-sensor-binding-2026-10-28.md).

## Permanent Linux 7 boot — October 27, 2026

The operator installed the system5 menu in the boot partition. Its default
entry starts the existing Mobian root with Linux 7.2.12 after 15 seconds;
the prior Mobian 4.19 entry is retained as a fallback. The operator confirmed
that the desktop started, and the first 71,929,856 bytes read back from boot
matched the installed image SHA-256
`c9910703d146da7b98c08f7820f5c4e289c5630e8ba139dd185933a7ace78a61`.
The running initramfs marker also matched
`0e4464414a32df2df943042276ae9f67d77fee3373c9040f4ac3ca7762b88f16`.

The fuel gauge is visible (99% in the captured session). The charger driver is
disabled: plugged-in readings reported discharging, so charging is not
qualified. A runtime logind power-key guard and a narrowly scoped polkit rule
for the `mobian` account are staged by the Linux 7 initramfs; the rule also
applies to non-local sessions of that account and is a workaround for the
unresolved seat/session problem. A reboot worked with that policy in a prior
temporary session; the installed variant's permissions were checked, but its
shutdown action was not separately qualified. Wi-Fi, Bluetooth, camera, torch,
GNSS, suspend and battery endurance require further work on this kernel.
Other entries of this exact installed menu were not requalified after the flash.
The 4.19 kernel/root and Android partitions were not flashed in this operation.

The local build and install inputs are not yet a self-contained repository
recipe. Do not remove the required local inputs on the strength of this note.
No proprietary firmware, image, private device log or credential is committed.


The later community-derived 7.2.12 RAM trials qualify framebuffer display, USB
journal transport and bounded raw touch/release sequences together, and the
latest of them additionally runs the real Mobian userspace shell and compositor
on a read-only rootfs. Those observations describe the historical trial, not the subsequently installed
system5 boot. Radios, camera, suspend, charging and endurance remain unqualified.
See the community milestones below for exact variant and evidence boundaries.

### Earlier minimal observer checkpoint (historical)

- Accepted then: kernel entry, eight CPUs, observer /init, HS USB RNDIS, journal retrieval.
- Display and touch were not qualified on that earlier minimal variant.
- Its EPSS-L3 provider was modular and CPUfreq deferred; this limitation must
  not be attributed to the later community variant, where CPUfreq probes.
- configs/cpufreq-next.fragment remains a host-Kconfig-only historical candidate.
- initramfs/init is the tested observer source. It stays in RAM, serves a bounded
  journal on USB TCP9000 and offers no remote shell. It is not a graphical OS.

The tested source inputs and diagnostic patch are retained here with their
identities. No generated Image, DTB, initramfs, proprietary firmware, keys or
raw handset logs are committed. The DTS reproduces the tested semantic inputs;
a host recompile from this path matches every deployed DT property. Byte-identical
DTB serialization is not required or claimed.

## Reconstruction boundary

This is a source checkpoint, not yet a portable one-command image builder.
The staged menu recipe still depends on the qualified local four-entry menu
inputs and isolated compiler rootfs. Do not delete those ignored build inputs
on the strength of this checkpoint alone. Refactor and lock the full menu and
kernel recipes here before declaring cleanup/reconstruction independence.
Heavy builds remain operator-run. No persistent installer is changed.

Keep working4.19 recoverable. Do not replace its kernel or boot the existing
Mobian rootfs with7.x before qualifying storage, modules, firmware, display and
input. The older branch name developpement is retained for now; no remote
branch or default-branch rename is performed by this checkpoint.


## Community hardware milestones (October 26-27, 2026)

Two RAM-only community boots now produce real display and USB journal output on
the handset. Both reach DSI, DRM MSM and a framebuffer console, with the USB
observer transport working and UFS probing successfully.

- Linux 7.1.0-lmi-ccc-ram1, from community revision
  3a8409fb1020b5952310072713ce97edea5e65d7. DSI binds at 3.425598 s, DRM MSM
  initializes at 3.588207 s, `fb0: msmdrmfb frame buffer device` appears at
  3.808570 s, and observer heartbeats reach 304.74 s.
- Linux 7.2.12-lmi-community-port1, the same community work ported onto the
  7.2.12 tree at cc9de5d4b5ab6459f5774946aa3195ad51236fa8. DSI binds at
  3.067957 s, DRM MSM initializes at 3.212974 s, the MSM framebuffer appears at
  3.428206 s, and observer heartbeats cover uptime 4.34 through 94.38 s with no
  kernel panic, BUG or RCU-stall marker in the capture.

On top of that, the combined display and touch candidate now passes on the
handset. Menu bdd18157d0e9f3e9a83e53c2d10d5f1ee3e2d187947f23937dbb21b187bc36ed
carries kernel
703819e444e378d0de4a79523a7faed2066ada9d514dcabb249a96e1f11938d3 and DTB
306315e8288ea13c4dc10c017eda3c75aefe4a3a189c906c6567ed6b75b602db, with the
uname still 7.2.12-lmi-community-port1 and the hashes distinguishing it from the
display-only candidate. The bounded evdev capture holds 3131 event records over
75144 raw bytes: 46 tracking-ID starts and 46 releases, 1211 XY updates, 484
synchronization reports, no SYN_DROPPED, no active slot left at the end and
BTN_TOUCH=0 over a 12.081312 s event span. Every published figure was
recomputed independently from the retained raw capture before publication.

These display and touch trials are diagnostic RAM boots: they mount no root
filesystem and run no Mobian GUI, the GPU and radio firmware are absent, and no
battery or suspend result follows. The permanent Mobian/Lineage installation was
not flashed. The guarded userspace boot that came after them is recorded in the
Phosh desktop section below. The artifact identities are recorded in
[CURRENT-BUILD.md](../../../docs/status/CURRENT-BUILD.md).

See [the 7.1 record](../../../docs/validation/lmi-linux7-community-display-2026-10-27.md),
[the 7.2.12 display record](../../../docs/validation/lmi-linux7-community-port-display-2026-10-27.md)
and [the combined display and touch record](../../../docs/validation/lmi-linux7-community-display-touch-2026-10-27.md).


## Phosh desktop on Linux 7.2.12 (27 October 2026)

The Mobian desktop appeared during the RAM-only trial and the operator exercised
the drawer. This is a real Mobian userspace session rather than a console: the
dedicated Mobian rootfs is mounted read-only with journal replay disabled, the
home directory is a temporary one in RAM, the session uses a private session bus
and no full systemd or login session is started.

The graphics log is 26,648 bytes, SHA256
5e29281a6ec773d676680144c8aa2ceaa82fe4a5bb787c84192341f6f31ed50a. It records
ID_INPUT=1 and ID_INPUT_TOUCHSCREEN=1, so the touch device is classified for
the compositor; Phoc on the builtin libseat with the MSM DRM backend on
/dev/dri/card0; WLR_RENDERER=pixman with the pixman renderer created; and
GRAPHICS_WINDOW_END elapsed=90 (maximum 90 seconds) followed by TRIAL_FINISHED.
The journal confirms the strict identity of kernel 703819e4, DTB 306315e8 and
diagnostic initramfs d3ec261b, with no kernel panic, BUG or internal error. The
figures were re-checked directly against the retained log and journal before
this entry was written.

Two earlier attempts on the same base stopped before Phosh: the first because
libinput saw no input device, the second because the touch device was not
classified. They are historical failures of those two attempts, not the outcome
of this one. What unlocked the third attempt is a scoped SYSTEMD_IN_CHROOT=0 on
the temporary udevadm trigger and settle calls, so udevadm no longer skips the
request inside the chroot.

Scope: software rendering, a read-only rootfs, an empty RAM home and a session
bounded to 90 seconds. This is not an accelerated GPU test, not a persistent or
autonomous boot, and not a qualification of applications, normal services,
suspend or battery. Portal, missing system-bus and application startup
warnings occur, and an application startup timeout is not evidence that all
installed applications work.

At this historical checkpoint, Linux 7 was not yet the permanent default.
A later system5 boot was installed and verified, as described above.

See [the validation record](../../../docs/validation/lmi-linux7-phosh-desktop-2026-10-27.md).


## Linux7 first touch events (26 October 2026)

The RAM observer now binds GPI1, I2C13 and the EDT touchscreen after a
board-specific GPI offset candidate. The operator captured 591 input events
with coordinates in range. Multi-touch release is NOT qualified: four
contacts started, only one ended, despite all fingers being removed.
A board-only release candidate is host-checked but not built or tested.
On that trial, display and a graphical Linux7 system were still unqualified; no
permanent installation occurred. See
[the validation record](../../../docs/validation/lmi-linux7-gpi-first-touch-2026-10-26.md).


## Bounded touch release trial (26 October 2026)

The operator booted the release candidate kernel
a44101ed50e7eefea6c793cc477fefa492a01666774161f76d4c1077c8d1afc7.
The captured interval contains 40 tracking-ID starts and 40 releases, empty final
active slots and BTN_TOUCH=0, with no SYN_DROPPED. I2C/EDT bind and the previous
GPI timeout is absent. This passes the release check in the captured interval.
The raw byte cap was reached after 12.901885 seconds of events, before the
30-second hands-off reminder; do not claim a complete minute or quiet final
phase. At that point, GUI, display and ten-finger qualification were still
pending.
Evidence remains local/private under work/linux7-touch-20261026T223017387301Z-private.


## Display1 source preparation (26 October 2026) -- host-checked, never built

The display stack for the lmi board is prepared as a source checkpoint plus a
portable kit builder. Nothing here was built, packaged or flashed by the agent.
It is retained as an auditable reference for the display path; the community
kernels above superseded this direction and are the qualified result.

### What this adds to the checkpoint

- `configs/display1.fragment`: the DRM, MSM, DSI, 7 nm PHY and panel Kconfig
  symbols, all of them built-in. It also pins `CONFIG_MODULES=n`, because the
  initramfs carries no module payload and Kconfig otherwise caps the whole
  display chain at `m`.
- `drivers/gpu/drm/panel/panel-samsung-ams667uu01.c`: the lmi AMOLED panel
  driver on the Linux 7.2 DRM panel API, controlling the panel rails itself
  and sending the vendor DCS sequence.
- `patches/0002-lmi-dsi-display.patch`: the observer DTS plus the DSI wiring
  (controller, four-lane output, 7 nm PHY, panel node) and the three panel
  rails (vddio 1.88 V, vci 3.0 V, DSI vdda 1.2 V).
- `patches/0003-add-msm667uu01-panel.patch`: the panel driver file plus its
  Kconfig and Makefile entries.
- `tools/regen-display-patches.py`: regenerates patches 0002 and 0003 from the
  pristine tree and the repository copies, so the patches stay auditable.
- `tools/check-display1-host.sh`: static validation of the patches, the
  configuration, the DTB and the panel driver object.
- `tools/find-modular-selectors.py`: lists the modular symbols that cap a
  tristate chain, the mechanism behind the silent module demotion.
- `tools/build-linux7-bundle.py`: rebuilds the LMIBNDL1 RAM bundle with the
  four linux7 components of a kit, every other component staying
  byte-identical. Its `--self-test` mode re-packs the accepted bundle and
  checks that all nine components decode identically.
- `tools/prepare-menu-recipe.py`: prepares a pinned menu recipe for a new
  bundle, rewriting the three pinned values and regenerating the manifest.
- `build/build-linux7-kit.sh`: the operator recipe that builds the kit
  (Image, DTB, initramfs, command line) and writes its manifest.

### Host validation reproduced on October 27, 2026

`tools/check-display1-host.sh` was re-run against the pinned tree
cc9de5d4b5ab6459f5774946aa3195ad51236fa8 and passes: the three patches apply
cleanly, the merged configuration resolves every required display symbol as
`=y`, the board DTB compiles to 115766 bytes and carries the panel node, the
three supplies, the reset line, the data lanes, the 7 nm PHY and the PM8150L
regulators, and the panel driver compiles to a 11640-byte object. The bundle
self-test re-packs the accepted bundle with all nine components
decoded-identical and valid crc32.

### What is still unqualified

Nothing on this display path has run on the handset. No panel, rail, DSI timing
or GPU firmware load has been observed on this device from these sources, and
no kernel Image was ever produced from them.

What is host-checked covers the patches, the merged configuration, the board
DTB, the panel driver object and the bundle self-test. The complete operator
chain, from the kernel Image through the bundle and the pinned menu recipe to
a firmware build and a handset trial, was never executed, so the reproducible
publication of that path remains to be done.

The escalation plan and the operator procedure are in
[the validation record](../../../docs/validation/lmi-linux7-display-plan-2026-10-26.md).
