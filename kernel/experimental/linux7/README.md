# lmi Linux7 experimental checkpoint

This branch isolates the7.2.12 bring-up from the working downstream4.19 system.
The operator temporarily booted a RAM observer and recovered its live USB log.
TLMM GPIO exclusions28-31/40-43 were required to cross the earlier binding
stall in this trial. See the [hardware record](../../../docs/validation/lmi-linux7-menu-host-check-2026-10-26.md).

## Accepted and unqualified layers

- Accepted: kernel entry, eight CPUs, observer /init, HS USB RNDIS, journal retrieval.
- Not qualified: display, touch, rootfs boot, GPU, camera, radios or battery life.
- CPUfreq still defers: its EPSS-L3 provider was modular, while this initramfs
  carries no modules. configs/cpufreq-next.fragment is host-Kconfig checked only.
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

All of these are diagnostic RAM boots: no root filesystem is mounted, there is no
Mobian GUI, the GPU and radio firmware are absent, and no battery or suspend
result follows. The permanent Mobian/Lineage installation was not flashed. The
combined display and touch base is the current base of that line; the next step
is a guarded boot of real userspace, reviewing the rootfs and firmware
dependencies first rather than assuming the 4.19 userspace hardware integration
is interchangeable. The artifact identities are recorded in
[CURRENT-BUILD.md](../../../docs/status/CURRENT-BUILD.md).

See [the 7.1 record](../../../docs/validation/lmi-linux7-community-display-2026-10-27.md),
[the 7.2.12 display record](../../../docs/validation/lmi-linux7-community-port-display-2026-10-27.md)
and [the combined display and touch record](../../../docs/validation/lmi-linux7-community-display-touch-2026-10-27.md).


## Linux7 first touch events (26 October 2026)

The RAM observer now binds GPI1, I2C13 and the EDT touchscreen after a
board-specific GPI offset candidate. The operator captured 591 input events
with coordinates in range. Multi-touch release is NOT qualified: four
contacts started, only one ended, despite all fingers being removed.
A board-only release candidate is host-checked but not built or tested.
Display and a graphical Linux7 system remain unqualified; no permanent
installation occurred. See
[the validation record](../../../docs/validation/lmi-linux7-gpi-first-touch-2026-10-26.md).


## Bounded touch release trial (26 October 2026)

The operator booted the release candidate kernel
a44101ed50e7eefea6c793cc477fefa492a01666774161f76d4c1077c8d1afc7.
The captured interval contains 40 tracking-ID starts and 40 releases, empty final
active slots and BTN_TOUCH=0, with no SYN_DROPPED. I2C/EDT bind and the previous
GPI timeout is absent. This passes the release check in the captured interval.
The raw byte cap was reached after 12.901885 seconds of events, before the
30-second hands-off reminder; do not claim a complete minute or quiet final
phase. GUI, display and ten-finger qualification remain pending.
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
