## Linux 7.2.12 community base: display plus touch release PASS — October 27, 2026

The combined display and touch candidate now passes on the handset. The RAM-only
menu bdd18157d0e9f3e9a83e53c2d10d5f1ee3e2d187947f23937dbb21b187bc36ed carries
kernel 703819e444e378d0de4a79523a7faed2066ada9d514dcabb249a96e1f11938d3, DTB
306315e8288ea13c4dc10c017eda3c75aefe4a3a189c906c6567ed6b75b602db and the
unchanged diagnostic initramfs. The uname stays 7.2.12-lmi-community-port1;
the hashes are what distinguish this candidate from the display-only one.

The bounded evdev capture holds 3131 event records over 75144 raw bytes: 46
tracking-ID starts and 46 releases, 1211 XY updates, 484 synchronization
reports, no SYN_DROPPED, no active slot left at the end and BTN_TOUCH=0, over a
12.081312 s event span with X in 227..845 and Y in 801..1825. The capture is
complete and stays below the raw byte cap. The journal shows the GPI, I2C and
touch probes returning 0, the FT5452 touch device bound and the MSM
framebuffer initialized, with no kernel panic, BUG or RCU-stall marker. Every
published figure was recomputed independently from the retained raw capture
before this entry was written.

This combines the display-capable community port with the handset-validated
GPIO72 main supply, PM8150L LDO1 1.8 V IO, FT5452 power ordering and snapshot
release handling. It validates bounded raw touch and release sequences on the
combined base. It does not establish GUI usability, full ten-finger behavior,
coordinate calibration, GPU acceleration, suspend or battery consumption. No
installed Mobian or Lineage partition was changed, and the raw captures stay
private.

The next milestone is a guarded boot of real userspace on this display and input
base, reviewing the rootfs, initramfs and firmware dependencies first: the 4.19
userspace hardware integration must not be assumed to be interchangeable.


## Linux 7.2.12 community port: display and USB PASS — October 27, 2026

The RAM-only 7.2.12-lmi-community-port1 trial reached DSI, DRM MSM and
framebuffer console output on the handset, with the USB journal transport
working. The operator saw a white screen followed by console text. DSI binds
at 3.067957 s, DRM MSM initializes at 3.212974 s and the MSM framebuffer
appears at 3.428206 s; USB and UFS probes complete successfully. Observer
heartbeats cover uptime 4.34 through 94.38 s, and no kernel panic, BUG or
RCU-stall marker appears in the capture. This is bounded evidence, not a
long-term stability test.

Scope: RAM-only diagnostic boot. Touch was deliberately disabled. The a650,
ADSP, Bluetooth and WLAN firmware are absent from this small diagnostic
initramfs, so GPU acceleration is not qualified, and audio still has pending
probe dependencies. No root filesystem or Mobian GUI is mounted, so no battery
or suspend result follows, and the permanent Mobian/Lineage installation was
not flashed. The artifact identities are recorded in
[CURRENT-BUILD.md](CURRENT-BUILD.md). Collecting the journal required a manual
Windows Remote NDIS driver association; that host-side friction is still open.
See [the validation record](../validation/lmi-linux7-community-port-display-2026-10-27.md).


## Community Linux 7.1: display and USB PASS — October 27, 2026

The RAM-only community 7.1.0-lmi-ccc-ram1 boot reached MSM/DSI/DRM framebuffer
output and USB observer heartbeats through 304.74 s. The operator saw a white
screen followed by console text. DSI binds at 3.425598 s, DRM MSM initializes
at 3.588207 s and `fb0: msmdrmfb frame buffer device` appears at 3.808570 s,
which establishes real MSM/DSI/DRM takeover rather than a bootloader
framebuffer. UFS enumeration also succeeds.

Scope: RAM-only diagnostic boot, no root filesystem mounted and no Mobian GUI
tested. Touch was intentionally disabled for this first community trial. GPU
acceleration, Wi-Fi, Bluetooth, audio, cameras and suspend/battery behavior are
not qualified. The existing Mobian/Lineage installation is unchanged. The
artifact identities are recorded in [CURRENT-BUILD.md](CURRENT-BUILD.md). See
[the validation record](../validation/lmi-linux7-community-display-2026-10-27.md).




## Linux7 first touch events — October 26, 2026

The RAM observer now binds GPI1, I2C13 and the EDT touchscreen after a
board-specific GPI offset candidate. The operator captured 591 input events
with coordinates in range. Multi-touch release is NOT qualified: four
contacts started, only one ended, despite all fingers being removed.
A board-only release candidate is host-checked but not built or tested.
Display and a graphical Linux7 system remain unqualified; no permanent
installation occurred. See
[the validation record](../validation/lmi-linux7-gpi-first-touch-2026-10-26.md).


## Bounded touch release trial — October 26, 2026

The operator booted the release candidate kernel
a44101ed50e7eefea6c793cc477fefa492a01666774161f76d4c1077c8d1afc7.
The captured interval contains 40 tracking-ID starts and 40 releases, empty final
active slots and BTN_TOUCH=0, with no SYN_DROPPED. I2C/EDT bind and the previous
GPI timeout is absent. This passes the release check in the captured interval.
The raw byte cap was reached after 12.901885 seconds of events, before the
30-second hands-off reminder; do not claim a complete minute or quiet final
phase. GUI, display and ten-finger qualification remain pending.
Evidence remains local/private under work/linux7-touch-20261026T223017387301Z-private.


## Linux7 display1 preparation: DRM/DSI/panel sources and recipe — October 26, 2026

The live observer journal was retrieved over USB from the handset: the device
runs the Linux 7.2.12 RAM observer, not Mobian, and the running kernel carries
no CONFIG_DRM at all, which is the measured cause of the white screen rather
than a panel, rail or cable fault. A display1 candidate is prepared, not
built: the DRM/MSM/DSI Kconfig fragment, the lmi AMOLED panel driver on the
7.2 DRM API with vendor rails and vendor DCS sequence, the DSI wiring patch, a
portable kit builder and a static validation tool. The Kconfig cap that
silently demoted the whole display stack to modules is measured and fixed in
the fragment.

The host checks were reproduced independently on October 27 against the pinned
tree cc9de5d4b5ab6459f5774946aa3195ad51236fa8: the three patches apply
cleanly, the merged configuration resolves every display symbol as `=y`, the
board DTB compiles to 115766 bytes carrying the expected panel, supply, reset,
lane and PHY nodes, the panel driver compiles to a 11640-byte object, and the
bundle self-test re-packs the accepted bundle with all nine components
decoded-identical and valid crc32. That is host evidence only: no kernel Image
was built, no image was packaged, and no flash or device write ever happened.

This source line is superseded in direction by the community kernels above,
which reached real DSI/DRM/USB output on the handset. It is retained as an
auditable, never-built reference for the display path, not as a qualified
milestone. See
[the plan and evidence](../validation/lmi-linux7-display-plan-2026-10-26.md).

## Linux7 RAM observer and USB journal PASS — October26,2026

Linux7.2.12 reaches /init and publishes its journal over USB. Restoring the
lmi GPIO28-31/40-43 exclusions lets TLMM probe complete; captured heartbeats
reach330.48s without the previous RCU stall. Display/touch/rootfs and autonomy
are not qualified; CPUfreq still defers for missing interconnect paths.
This is a temporary RAM observer, not an installed or usable graphical OS.
See [evidence and limits](../validation/lmi-linux7-menu-host-check-2026-10-26.md).

## Linux7 reset localized to TLMM binding path — October26,2026

Probe markers name sm8250-pinctrl immediately before a stall; RCU later reports
CPU0 stalled. The minimal tree omitted the lmi community GPIO28-31/40-43
reservations. A one-property DTB candidate is prepared with the same diagnostic
kernel; no successful boot or confirmed fix yet. See
[the evidence and candidate](../validation/lmi-linux7-menu-host-check-2026-10-26.md).

## Linux7 kernel entry confirmed; full boot fails — October26,2026

The first rails1 trial reset after a white screen. Preserved pstore proves
Linux7.2.12 entered and activated all eight CPUs, but not that initramfs or USB
started. Installed Mobian recovered normally. A logging-only header candidate
is prepared; no new kernel build, permanent install or power-policy change.
See [the trial evidence](../validation/lmi-linux7-menu-host-check-2026-10-26.md).

## Linux 7 observer menu — October 26, 2026

Only default Mobian4.19 boot is accepted from the first temporary five-entry
menu. Linux7.2.12 has not run on the handset. USB DT bindings and duplicated
reservations were corrected offline; a revised operator menu build is ready,
not compiled or installed. The first menu lacks the accepted FG profile-order
fix and must not be used for autonomy measurement. See the
[validation boundary](../validation/lmi-linux7-menu-host-check-2026-10-26.md).



## Snapshot51 and system-upgrade assessment — October 26, 2026

Snapshot48 remains installed. Flatpak and libostree were added for an isolated
51.0 trial, but runtime deployment failed: the current kernel returns no statx
mount ID required by the path-resolution helper. No security checks were
bypassed. A Trixie full-upgrade simulation lists19 updates/0 removals, not
applied; no switch to Forky or full-system upgrade has occurred. See the
[assessment and retained changes](../validation/lmi-snapshot51-upgrade-assessment-2026-10-26.md).

## Front HAL lifecycle checkpoint — October 26, 2026

ID1 front/270 was confirmed by the HAL and yielded a1280x720 preview buffer
in an isolated supervised cycle. Motion and cleanup succeeded, but the very
dark image is not accepted as useful scene quality. No in-app switch is
installed. See the [validation](../validation/lmi-front-camera-hall-only-2026-10-26.md).

## Native front-camera mechanism accepted — October 26, 2026

The operator confirmed normal extension/retraction in one supervised native
cycle. Endpoint checks and independent sensor shutdown completed; no camera
HAL was opened. Front images and the Snapshot switch remain pending. See the
[scope and journal limitation](../validation/lmi-front-camera-hall-only-2026-10-26.md).

## Front-camera sensor checkpoint — October 26, 2026

The Hall-only path delivered eight valid samples and was explicitly shut down;
independent cleanup and kernel power-down logs were checked. Factory-calibration
replay classifies all eight inside the vendor retracted-position window; no
extended-position or jam trial has run. No motor motion,
front preview or new package/image is qualified. See
[scope and next boundary](../validation/lmi-front-camera-hall-only-2026-10-26.md).

## Search-close runtime update — October 26, 2026

The searchclose1 package is installed. The operator confirms clearing matching
and empty-result queries on completed downward close and full-list restoration.
36 package tests pass; running binary, same kernel and accepted renderer/power
daemon are verified. Rescue timer is cancelled. Complete-image pins remain
preview1; no fresh image or unplugged UI qualification is claimed.
See [acceptance](../validation/lmi-search-clear-on-drawer-close-2026-10-26.md).
Preparation entries below are historical.

## Current checkpoint — October 26, 2026

The [root README](../../README.md) now summarizes current accepted behavior and
pending work. Permanent dualboot and accepted private-target thumbnails remain
qualified. The night record validates sustained quiet returns to suspension;
it does not calibrate residual current. See the [battery checkpoint](BATTERY-RESEARCH-CURRENT.md)
and [overnight validation](../validation/lmi-quiet-wake-night-2026-10-26.md).

Installed Phosh remains irqnames1+drawerpreview1. Clearing every search on
completed drawer close is a new, host-checked candidate, not built or installed;
it supersedes the previous empty-result-only request. See the
[candidate validation](../validation/lmi-search-clear-on-drawer-close-2026-10-26.md).
Complete-image package pins, permanent menu and temporary kernel are unchanged.
Older dated entries below retain their original milestone boundaries.

## October 26: quiet gauge returns sustained overnight

The preserved 9h48m42s marker interval contains 95.824% inferred suspension
and 35 natural gauge return gaps around 15 seconds. Display changed 100 to82.
The historical long awake dwell did not recur in those observed gaps. Raw
counter progression is nearly stable early/late, while software/shadow rates
slow by about33%; this is not a calibrated current reduction or a new peripheral
cause. Current accepted runtime is unchanged and the combined search candidate
is still uninstalled. See [night evidence and limits](../validation/lmi-quiet-wake-night-2026-10-26.md)
and [current research decisions](BATTERY-RESEARCH-CURRENT.md).

## October 24: fuel-gauge profile lookup depends on board-tree order

## Thumbnail source localization, October 24

Raw thumbnail pixels are already striped before Phosh paints them. Standalone GPU controls reproduce corruption in the shared GBM target while the internal target gives twelve exact cases including orientation. The private-target Phoc package is now device-accepted: clear upright Horloges/Fichiers previews plus responsive overview, app activation and horizontal favorite drag. Its running binary is verified and the complete-image Phoc pin updated. GLES2, the same temporary kernel and the published battery profile are preserved; no full image was rebuilt. See [evidence and limits](../validation/lmi-thumbnail-private-target-2026-10-24.md).

## October 24 follow-up: quiet battery comparison remains pending

The temporary old-kernel/intended-profile boot completed a normal deep-sleep diagnostic (295.868715303 seconds), awakened only by USB. The prior 14-second RTC-interrupted counter window is not a valid long-suspend comparison; the RTC diagnostic recorded no battery counter endpoints. No battery fix or calibrated current is established. See [window and RTC follow-up](../validation/lmi-fg-dt-order-window-2026-10-24.md).

Installed Phoc +thumblinear1 still shows striped app cards. The thumbnail-only row-readback candidate was built, activated, visually rejected and rolled back; see [actual outcome](../../userspace/phosh/thumbnail-row-readback-candidate/README.md). A temporary pixman diagnostic was unusably slow and pixel-inconclusive; GLES2 is restored and its runtime override is removed. The same temporary kernel/profile were preserved. No kernel/full image build or pin promotion. The next passive measurement remains planned for tonight.

The qualified menu startup reference remains unchanged. Offline replay of its exact Mobian DTB shows that the old FG name lookup reaches the vendor container rather than the intended SOC profile container. A separate order-only diagnostic image (7425c00b...) has now temporarily started Mobian on the original October7 kernel and published the intended j11sun/design4700000 profile. UI acceptance and battery observation remain pending; no battery-current cause is established. The candidate is not permanently installed, its output paths are isolated, and the qualified reference image remains unchanged. See [the evidence and limits](../validation/lmi-fg-profile-dt-order-2026-10-24.md).

## 2026-10-23: battery work integrated with explicit evidence limits

## October 23: locked power menu package update

The installed Phosh/common pair is now homedrag8. Its 36 package tests,
locked power-menu confirmation and operator-requested restart are validated.
The next complete build selects this pair; the existing installed rootfs and
boot/menu artifacts are unchanged. See
[the validation record](../validation/lmi-locked-power-menu-2026-10-23.md).


The corrected standby collector and UFS policy reader are retained with
offline tests, alongside the MiniMax investigation notes. The publication
review at docs/validation/lmi-battery-evidence-review-2026-10-23.md supersedes
claims that the gauge or all kernel requests have been excluded. Independent
raw-trace replay confirms identical observed apps_rsc SLEEP programming in
the retained window pairs, with differences confined to WAKE programming.
The residual's physical cause and absolute electrical scale remain open.

## 2026-10-23: permanent dualboot installed and read-back verified

The operator installed candidate be9841c76cbe34d0c72606c47877f99582aee224144744349a9e78d15cfd0a94 to boot and confirmed automatic Mobian startup. Read-only SSH verified the installed boot prefix over the complete 81,051,648-byte artifact against its SHA256, the direct outer-v2 marker and the dedicated16GiB root. The permanent installation is confirmed. All four exact-image entries had previously passed temporary handset trials; only Mobian has additionally been confirmed after permanent installation. No kernel/rootfs rebuild or battery policy modification was part of the installation. Private raw receipts remain outside Git. No further menu build is required.

## 2026-10-23: dual-extent menu passed all four temporary handset entries

Candidate be9841c76cbe34d0c72606c47877f99582aee224144744349a9e78d15cfd0a94 (81,051,648 bytes) passed operator tests: Mobian default after15s, LineageOS, Fastboot, Recovery. Read-only SSH independently confirmed the direct outer-v2 Mobian marker and dedicated16GiB root. The Android full-runtime-extent candidate resolves the reported boot failure in this handset trial; an actual collision address was not captured. The pinned installation helper is ready for the operator. No permanent flash or installed readback has yet been performed. Private raw evidence remains outside Git.

## 2026-10-23: board7 Mobian PASS, Android FAIL; dual kernel extent candidate

The operator temporarily booted board7 SHA256 9c7923502a7906470488c06ac5e640c0a1991bafad3a143bbe6f4eb4fcc0fd95. Mobian default boot passed; read-only SSH independently confirmed outer-v2 and the dedicated 16GiB root. Selecting LineageOS instead produced display corruption followed by a reboot to installed Mobian. No pstore record survived. This candidate is NOT qualified for permanent installation.

Offline inspection confirms an Android loader allocation defect: its pinned ARM64 Image file is 53,456,920 bytes, but its header requires 64,811,008 bytes. The generic loader reserves only 54,525,952 bytes after text_offset, leaving 10,285,056 bytes of required runtime extent outside that allocation. The working historical layout does not prove the allocation is sufficient; the added outer bundle changes memory placement. An actual collision is plausible, but not proven without runtime addresses.

The existing full-extent reservation helper previously ran only for Mobian. The candidate now invokes the same helper for both locked OS tags after decompression, before DT/initrd allocations. It preserves the board7 overlay, outer-v2 marker, reset guard, kernel/initrd inputs and Android DT selection. No new kernel or rootfs build is needed.

Host tests execute the exact helper with EFI allocation stubs using both pinned Image sizes: expansion, copied bytes, zeroed runtime tail, repeat-call idempotence, malformed magic refusal and failed-allocation preservation pass. This is host validation only. User-run menu firmware build and fresh temporary tests remain required. No installation or additional phone operation was performed.

## 2026-10-23: direct Mobian failure traced to an omitted board overlay

The outer-v1 image ece3f4c4 displayed its menu and loading text, then went black
after the15s Mobian default. SSH was unavailable; a forced reboot recovered the
unchanged installed Mobian. No flash occurred and no pstore records survived.
Permanent installation remains unqualified.

The bundle carried the generic Kona base DTB,2896 nodes. The functional ABL boot
uses4018 nodes. Offline application of exact pinned Xiaomi DTBO entry7 restores
4017 nodes, including the board display supplies, input and other peripherals;
the only additional runtime node is the fstab exaid entry.13 shared properties
remain different, including normal dynamic bootloader fixups. This is a confirmed
missing board-overlay step, not proof that every possible handoff issue is solved.

The external-mobian recipe now applies this exact overlay offline to the locked
Mobian base before packaging; no runtime DT dump is booted. Kernel, initramfs and
command line are preserved, Android's working loader and32MiB FD are unchanged.
The new direct marker is lmi_menu=outer-v2. Tests on real locked inputs, corrupted
input refusal, critical board nodes, bundle bounds/component preservation and
container construction pass; range/loader/container unit checks also pass. The
content-addressed recipe is prepared; firmware compilation is NOT run by the agent.

Next operator menu-only build: see build/boot-menu/external-mobian/README.md.
New output boot-lmi-outer-mobian-board7-test.img must be host-qualified and
temporarily tested before any installation. The old installation helper still
pins the failed image and must be repinned only after the new candidate qualifies.

## 2026-10-23: permanent menu operator workflow prepared; handset qualification pending

The outer-Mobian candidate was manually built on October22 and host-qualified:
SHA256 `ece3f4c4e6e2f6ed485d159b0b2f3f682ba8f758962a395490937120d44f423e`,
80,654,336 bytes. It retains the32MiB firmware and carries the pinned Mobian
components in the outer ramdisk. No additional firmware build was run for this
preparation. The historical resetguard1 restart-only reference remains unsuitable
for permanent installation over boot.

`build/boot-menu/permanent/` adds plan-only native Windows operator tools,
candidate/rescue hash checks, actual direct-root provenance capture, per-entry
operator evidence, product/partition guards, a qualification-gated boot-only
installer and installed boot-prefix readback. Nine offline tests pass; local
plan mode verifies both existing downloaded images. There has been no phone
contact, reboot, flash or hardware validation by this preparation.

Next: finish and save any battery observation, temporary-boot this exact image,
verify `lmi_menu=outer-v1` and the dedicated16GiB root, then test Mobian default,
LineageOS, Fastboot and Recovery. Only after those actual outcomes are recorded
can the operator installation run. Permanent readback remains unperformed.
See the operator README for the pinned rescue image and rollback procedure.

## 2026-10-22: 32-MiB external Mobian ramdisk candidate prepared, not built

The historical resetguard1 menu has all four operator outcomes confirmed, but
Mobian still restarts the installed boot. Permanent installation is not ready.
A new isolated recipe in `build/boot-menu/external-mobian/` retains the historical
32-MiB Android firmware and uses the outer boot ramdisk for pinned Mobian assets.
It adds early memory reservation, bounded endian-correct input parsing, runtime
reservation/CRC checks, direct Mobian loading and a command-line provenance marker.

Actual C host replays, exact overlay restoration/tamper refusal, container tests
and five actual ARM64 unit syntax checks pass. A real-input container test fits
within the boot-partition limit. No new firmware build or handset trial has been
performed. ABL placement and direct OS handoff remain unvalidated. The current
active menu recipe and installed phone are unchanged. See the candidate README
for the manual menu-only build command and required temporary validation.

## 2026-10-22: resetguard1 Fastboot and Recovery handset validation

The operator reports Fastboot works from the temporary menu, then Recovery
works, and finally confirms Mobian has started again. Tested resetguard1 image:
`40cbcc408b2b07f0b31ab7ef123776e7becacaf9d419bc78707ddd783242d70c`
(25,997,312 bytes, historical 32-MiB baseline plus reset-service guard).

This validates both rescue destinations for this candidate and the return to
installed Mobian. It supports preserving the earlier platform reset service;
it does not independently capture live service ownership. The operator subsequently confirms a fresh LineageOS launch on resetguard1.
All four menu outcomes have now been reported working (Mobian via installed
boot restart, LineageOS handoff, Fastboot and Recovery). The newer 64-MiB direct-handoff
failures remain separate. Text rendering is unchanged from the historical recipe.

The image remains temporary-only: its Mobian entry reboots the installed boot
partition. Flashing it over that partition would not provide direct Mobian
handoff and could cause a menu loop. No persistent-install qualification is made.

## 2026-10-22: older working menu checked; reset-service candidate is host-only

The operator confirms that the older Android-working menu starts Mobian and
LineageOS. Both Fastboot and Recovery selections instead return to Mobian;
text no longer fills the screen. Exact tested image identity remains unverified.
This does not supersede the failed LineageOS handoff of the newer 64-MiB images.

An isolated candidate in `build/boot-menu/reset-guard/` preserves an already
installed platform reset service before generic RELEASE initialization can
replace it. The actual original initializer overwrites a mocked platform
service; the actual patched initializer preserves it, retains fallback when
absent, and propagates lookup errors. Tampered source is rejected. These host
tests pass; the firmware dispatcher and handset have not been tested with it.

No firmware build, phone change or flash was performed. The active build recipe
is unchanged. Integrate against the identified Android-working baseline and
qualify its source manifest before a manual temporary build/test. See the
candidate README for source evidence and remaining runtime uncertainty.


## 2026-10-22: quiet display accepted; identify actual OS at final handoff

The operator reports the quiet native-font display looks good and Mobian loads.
Candidate SHA256:
5726e8917ddb52fee69fee4c6fd3e493758364a3163fd646fdc8cff9bd787ab3.
Its 21 source hashes and native screen filter match the recipe; actual FD PrePi
replay passes. The final image payload matches the freshly built 144-byte
BootShim plus actual 64-MiB FD byte-for-byte. FD SHA256:
629c256312860f93396e6ad6c953196b114d7d9b3f0171b52cab67a21a2bd455.
Native rendering is the retained baseline. Do not re-enable the custom zoom.

Read-only Mobian verification still lacks both explicit provenance markers;
the dedicated root and Phosh work, but direct handoff is not established.
The operator further reports selecting LineageOS returns to Mobian, with text
that looks similar. They explicitly confirm the checkmark moved to LineageOS.
Treat this as a failed LineageOS-entry trial, not a validated Android launch.
Do not confuse it with the earlier successful Android-only 32-MiB candidate.

A host C replay of the actual bootmenu_boot and after_exit functions confirms
that a checked android selection dispatches android even when the prior default
is mobian. The copied target survives subsequent GUI selection changes. The
BOOT_LINUX dispatch table also points to run_boot_linux. This does not prove the
live device follows that path; no source-level selection mapping bug is found.

The next diagnostic adds a fixed native-font panel immediately before execute,
after all RAM component and final DT provenance checks. It names LINEAGEOS or
MOBIAN using the target received by run_boot_linux, remains for exactly three
seconds, and then launches normally. It also logs the selected OS at entry and
identifies the OS on the existing failure panel, replacing the misleading
hardcoded LineageOS label. No new disk writes or settings. The three-second
pause is deliberate diagnostic visibility, not a production boot optimization.

Four actual ARM64 units pass syntax; the syntax harness now overlays the latest
diagnostic and variant headers as well as the bundle header. The 21-source
apply/restore/tamper fixture and bundle parser pass. The new fixed panel has not
been handset tested. There is no new kernel, DT policy or cache-cleanup change.

Next variant: consolequiet1-marker2-extent1-target1.
The operator builds only the menu:

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build --with-dual
```

Qualify the new actual image before a new Windows RAM launcher. Select LineageOS
and observe the final panel's OS name and whether the POCO logo returns before
Mobian. This distinguishes the requested target from the final fallback without
repeating an indistinguishable trial. No agent build/flash/phone policy change.
Persistent installation is still pending direct OS handoff qualification.


## 2026-10-22: prioritize quiet native loading console

At the operator's explicit request, prepare a menu build without the custom
enlarged renderer. The native console font and width-aware wrapping are already
restored. This next variant also draws only NOTICE and higher log levels on
screen: progress-stage notices and warnings/errors remain, while verbose DEBUG
and INFO dumps no longer cause extensive screen updates or scrolling. Filtering
is restricted to the screen branch of logger_write. Existing serial/file output
and the in-memory diagnostic buffer policy are not changed; no new disk logging
is enabled. The custom bitmap scaler is not included by the logger.

Actual ARM64 logger syntax passes. The 21-file apply/restore/tamper fixture and
the pinned bundle parser pass. Handset smoothness is not yet validated and must
not be asserted from these host checks. No build or phone operation by the agent.

Variant: consolequiet1-marker2-extent1. The kernel components, full runtime Image
allocation correction and provenance guard are unchanged. Direct Mobian handoff
still lacks runtime provenance in prior trials; quiet display does not resolve
that finding. Persistent installation remains unqualified.

Operator command:

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build --with-dual
```

Expected marker: DUAL_DIRECT_RAM_HANDOFF_BUILD_COMPLETE_NOT_FOR_FLASHING.
Qualify the new image and use a new hash-pinned Windows RAM launcher before the
handset trial. Older launchers pin older firmware and are not this build's test.


## 2026-10-22: extent1 handset result; restore native console font

The operator launched candidate
0e4d6cb08459e6c17d45126f48279874903ec4fd48f830b3ef3ac13aeeba34f2,
then explicitly repeated the launch after uncertainty about the Fastboot stage.
The retained Windows result reports a successful RAM boot of this exact hash.
Mobian returns to its dedicated root and Phosh runs. Both explicit provenance
markers remain absent in the running command line, live chosen node AND raw FDT.
The complete runtime allocation correction therefore did not establish a direct
Mobian boot. Do not equate this userspace return with direct-handoff validation.

An independent host unpack of the final Android boot image confirms the gzip
payload contains the freshly compiled BootShim followed byte-for-byte by the
actual 64-MiB FD at offset144. FD SHA256:
1dd7c69ab1e24d7173dd3dbfa7e2bca23f2809e8a8f0fa7b9bdd1a617d93f8d8.
This excludes an older firmware being packaged in the tested image. It does
not locate a possible reset during or after the final jump. Runtime config also
has appended DTB and OF overlays disabled; raw FDT provenance remains unresolved.

The operator reports stutter persists with the enlarged font and suspects it
slows loading. Removing the redundant clear did not visibly resolve this.
As requested, the next recipe restores the native console font and output path,
retaining width-aware wrapping and margins. The custom bitmap scaler is no longer
included or called by the logger. Original log text is preserved. The source
header is retained as experimental reference only. Native formatter C tests and
actual ARM64 logger syntax pass. This reversion is prepared, not installed.

Next variant: consolefit2-marker2-extent1. The full Image allocation correction
remains present because its independent protocol defect is established, even
though it has not resolved the observed runtime provenance failure. Do not
request another build solely to repeat this same unsuccessful direct-boot test.
Combine the font reversion with the next justified handoff diagnostic/change.
The requested persistent menu remains pending; no flash or phone policy change.


## 2026-10-22: reserve the full ARM64 Image extent before handoff

The operator confirms the zoom2 font SIZE is correct, but rendering stutters.
Mobian returns from RAM candidate
86adc4fef82f48fbad6f5049893a482914d2b8bbfb53a5f19017635b14b64e5f;
root is the dedicated partition and Phosh runs. Both explicit runtime provenance
markers are still absent. Cached main configuration really uses BOOT_LINUX, so
an unmatched reboot-mode replacement is excluded at the source level. Runtime
messages report a PMIC hard-reset/cold-boot reason; this is not sufficient to
attribute a new reset because the reason can be latched. Direct boot remains
unqualified and this candidate must not be installed permanently.

Source and pinned Image-header inspection found a concrete allocation defect:

| Kernel | File bytes | Declared image_size | Old usable allocation | Shortfall |
| --- | ---: | ---: | ---: | ---: |
| Mobian | 45,359,128 | 56,758,272 | 46,137,344 | 10,620,928 |
| Android | 53,456,920 | 64,811,008 | 54,525,952 | 10,285,056 |

The existing loader rounds the file size and accounts for text_offset, but does
not reserve the complete Image runtime size. The ARM64 boot protocol requires
at least image_size bytes free from the Image start:
https://docs.kernel.org/arch/arm64/booting.html
This may corrupt neighboring boot allocations or cause a reset; a causal link
to this handset's marker loss is a hypothesis, not a measured result.

The next recipe checks the actual ARM64 header after decompression, before DT
selection/finalization. It reserves an aligned allocation covering the larger
of file size and image_size, copies the payload, zeroes the runtime tail and
then frees the old buffer. It preserves text_offset and rejects unexpected
magic/architecture/offset, non-owned memory and excessive extent. Already
sufficient allocations are retained. Allocation failure leaves the old buffer
intact and aborts preparation. No fixed physical address or partition changes.

Actual helper C tests using both pinned Image headers verify payload retention,
zeroed runtime tail, sufficient capacity, allocation failure without freeing
the original, repeated-call reuse, bad magic and oversize rejection. Four actual
ARM64 units pass syntax. Twenty-one source edits apply/restore exactly and reject
tampering; the nine-component bundle parser passes. These are host checks only.

For screen rendering, the accepted 2x size is retained. The redundant visible
black-row fill before each opaque bitmap blit is removed to avoid an exposed
blank frame and an extra panel update. ARM64 logger syntax passes; whether this
eliminates the reported stutter needs handset validation. If it does not, restore
the previous font size as requested by the operator.

Next variant: consolezoom3-marker2-extent1. No firmware, kernel or rootfs build
was started by the agent. No phone policy, boot partition or recovery was changed.
The operator runs only the menu build:

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build --with-dual
```

Expected marker: DUAL_DIRECT_RAM_HANDOFF_BUILD_COMPLETE_NOT_FOR_FLASHING.
Qualify the new artifact, 21-source manifest and PrePi replay, then prepare a new
hash-pinned Windows RAM launcher. Check Mobian provenance before preparing the
requested persistent menu. Do not reuse the old launcher's image qualification.


## 2026-10-22: larger loading text prepared; direct Mobian provenance still absent

The operator tested consolefit1/marker2 candidate
548b06b3aabc4948dfafb1e9fefb7e9bef5e6e7b8a621d61b3aeb8fa69e6cdaa.
Loading text now uses the screen width, but its font remains too small.
Mobian returned to the dedicated partition and Phosh works. Read-only runtime
inspection nevertheless found neither lmi_menu=direct-v2 in the command line
nor /chosen/lmi,menu-os, nor the SimpleInit metadata. No pstore file was found.
Direct handoff is therefore NOT qualified; a fallback or DT replacement remains
unresolved. No persistent menu installation is approved by this result.

The next recipe renders the native HII 8x19 bitmap font at 2x (16x38), using
GOP blits at the existing panel resolution. It wraps fewer columns and scrolls
within margins. Original serial/file log text is preserved; unsupported graphics
services fall back to the existing console formatter. Host tests exercise the
actual pixel doubling function with buffer canaries and the formatter's long
lines/newlines/tabs. The actual ARM64 logger and four boot units pass syntax.
These are host checks, not handset validation of the larger text.

Before handoff the final RAM DT must now contain the exact provenance command
line token; otherwise preparation fails explicitly before kernel execution.
The twenty-source apply/restore/tamper fixture and bundle parser pass.
Variant suffix: consolezoom2-marker2. No firmware, kernel or rootfs build was
started by the agent, and no phone settings or boot partitions were changed.

Operator build command:

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build --with-dual
```

Expected result: DUAL_DIRECT_RAM_HANDOFF_BUILD_COMPLETE_NOT_FOR_FLASHING.
Qualify the new actual hash, source manifest and PrePi replay before preparing
a new Windows RAM launcher. Existing launchers pin older images; do not reuse
their qualification for this candidate. Android in the dual 64 MiB variant also
remains unqualified. Do not flash this experimental menu.


## Console-fit / marker2 image compiled, handset trial pending

The operator built the updated candidate: 47237120 bytes, SHA256
548b06b3aabc4948dfafb1e9fefb7e9bef5e6e7b8a621d61b3aeb8fa69e6cdaa.
All nineteen source hashes match the reviewed recipe. The actual uncompressed
firmware volume contains lmi_menu=direct-v2 and lmi,menu-os. The 64-MiB FD passes
the actual PrePi C replay. Windows transfer and plan-only launcher checks pass.
The new helper starts from Mobian and verifies its dedicated root, persistent
boot hash and absence of the owned trace instance before any reboot request.
It uses only native Windows Fastboot for the RAM boot. No launch/flash has been
performed during qualification. Screen formatting and direct provenance remain
pending hardware checks; the older Mobian userspace return alone is insufficient
to certify persistent menu installation. After launch, verify both marker fields.


## 2026-10-22: Mobian returns; screen-fitting text and provenance marker prepared

The operator reports Mobian started after choosing it in dual candidate
35a8bf8d508d1b7b98f435d871ee50665a6321eaef496feea132bf0815f129c8.
SSH confirms kernel 4.19.325-cip128-st12, Phosh running and /dev/loop0p2 backed
by dedicated /dev/sda35. No pstore file is present. However, the chosen node has
no simpleinit metadata and the command line lacks the compatibility video flag.
The correct userspace return is confirmed; direct handoff versus a reboot fallback
is not conclusively established. Do not promote this to persistent-menu approval.
The new dual image's Android entry also remains untested.

At the operator's request, the next recipe formats screen console logs to the
largest supported text mode with side margins and bounded wrapping. It preserves
the original serial/file log text and does not implement font scaling. Actual
formatter C tests cover a 16000-character line, embedded line breaks/tabs, screen
width and margins; the ARM64 logger unit passes syntax with generated flags.

The same next candidate adds lmi_menu=direct-v2 to the kernel command line and
/chosen/lmi,menu-os to the RAM DT. A later runtime check must find these before
claiming direct handoff. No current phone settings or boot partition were changed.
Nineteen source changes apply/restore exactly and reject tampering; four boot
units and the logger pass ARM64 syntax. No new firmware was built by the agent.

Operator command (same isolated cache, no kernel/rootfs rebuild):

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build --with-dual
```

Expected marker remains DUAL_DIRECT_RAM_HANDOFF_BUILD_COMPLETE_NOT_FOR_FLASHING.
Variant suffix: consolefit1-marker2. After build, qualify the new actual hash
and prepare a new Windows RAM launcher. The existing launcher pins the older
35a8bf image and must not be changed to accept an unverified file. Do not flash.


## 2026-10-22: dual build qualified; Android gauge comparison corrected

Operator compiled the direct dual candidate: 47237120 bytes, SHA256
35a8bf8d508d1b7b98f435d871ee50665a6321eaef496feea132bf0815f129c8.
All seventeen patched-source hashes match. Actual 64-MiB FD PrePi replay passes,
and Windows transfer plus plan-only launcher verification pass. The launcher
refuses an active power-trace instance. No new menu image has been booted or
flashed; direct Mobian, corrected board identification and persistent installation
still need hardware validation. See build/boot-menu/chainload/DUAL-DIRECT.md.

The Android thirty-minute trace was saved and cleaned up. Four qualified retained
sleep-bank windows match twelve Mobian APSS RPMh requests exactly. Early ring
overwrites limit the whole-session trace. Both Android histories show an instant
charge-counter discontinuity at unplug: 86 mAh overnight, 178 mAh in the short
trial. Excluding that jump changes the overnight apparent quotient from the
initial ~26 mA to ~13.84 mA net /15.72 mA summed decreases; the short stable segment
is ~13.99 mA. These are gauge-derived, not calibrated physical current. The actual
overnight precharge percentage was 95%; 96% was read after charging resumed.
See docs/validation/LINEAGE-POWER-TRACE-20261022.md for methods and limitations.


## 2026-10-22: direct dual menu candidate prepared (host validation only)

Android survived overnight without restarting: 100 to 96 percent over 8h31m
on battery, Android accounting 223 mAh (~26 mA), Wi-Fi/Bluetooth enabled.
Charging had resumed before return capture; charge-counter deltas differ.
This is not a controlled radio-isolated Mobian comparison. Raw logs remain private.
Android wall clock was still October 7; corrected to verified October 22 UTC
and Europe/Paris with AlarmManager, without reboot. No battery statistics reset.
Use host elapsed time, uptime and relative battery accounting, not raw Android
calendar timestamps across the clock correction.

A new --with-dual recipe launches Mobian directly instead of rebooting the
installed boot image. Both pinned component sets are embedded; the new 64-MiB
firmware reservation is balanced by shrinking adjacent ordinary RAM. Host source
restoration/tamper checks, nine-component bounds and ARM64 syntax pass. Real
DTB C tests preserve Mobian unchanged and retain the guarded Android correction.
No new firmware build or hardware trial yet; persistent installation remains
unvalidated. See build/boot-menu/chainload/DUAL-DIRECT.md for the operator command.


## 2026-10-21: Android boots from the temporary menu

The operator confirmed a successful LineageOS start after selecting it in the
temporary menu. Native Windows ADB independently reported sys.boot_completed=1,
file-based encryption, and metadata encryption enabled. Tested image: 25993216
bytes, SHA256 71e226f1a8adaf5d0574d1311d686143694404f49ab62df5d343c8a36c3c5196.

Only header offsets 44 and 47 differ from the previous fstab1 image: the OS
version field now matches pinned Android 16 / September 2026. A successful stock
Android boot occurred between the failed and successful menu trials, so the
exact internal vold/keymaster cause remains unproven. No keys or encryption
policy were changed; no flash, wipe or partition change occurred in this trial.

The recipe now applies this header alignment automatically to Lineage menu
outputs and records the OS-version context in its artifact manifest. Host checks
reproduce the tested image from the previous output; shell/Python syntax pass.
No new firmware compilation was run. The existing WSL cached output still has
the old header; the tested derived image is distinct.

The menu remains temporary and MUST NOT be flashed. Mobian currently restarts
the installed boot image; it needs direct chainloading before a persistent menu
can safely replace that image. Touch input remains unqualified; buttons work.


## October 21: full Android initialization captured

Full LineageOS startup and root ADB are confirmed after the dedicated-partition
migration. The plugged-in initialization snapshot also reports calibrate=-22,
no charge_pump_master/parallel supply and no calibration-force property. These
facts alone do not explain the standby gap or justify forced calibration.
Android exposes no debugfs filesystem in the inspected runtime; register/SRAM
comparison remains unavailable. No calibration or hardware data write occurred.
See [bounded evidence](../validation/lmi-android-init-2026-10-21.md).


## October 21: dedicated Mobian boot verified; Android/menu pending

The operator applied the GPT change, formatted Android data, flashed only the
dedicated mobian partition and temporarily booted the adapted Mobian image.
SSH confirms the 16 GiB dedicated backing, expanded root, current homedrag7 /
Phoc / GSD packages and clean package audit; the operator confirms a normal UI.
A guarded temporary Android boot now reaches initial setup; completion and access remain pending. The newly requested handset menu is not
installed: it must offer both OSes with Mobian default after 15 seconds. No
new autonomous boot manager or persistent default change is validated.
See the [first-boot result](../validation/lmi-dualboot-firstboot-2026-10-21.md).


## October 21: pre-installation passive reference retrieved

The existing Mobian completed 9.10 hours unplugged, with 95.3% clock-accounted
suspension. All 38 gauge wakes returned toward sleep without observed software
unblank. Qualified sleep-counter estimates remain about 52.2 mA; late filtered
resume samples have a 49.3 mA median. These are gauge estimates, not calibrated
electrical current. No new cause or saving is established. Cleanup passed.
See the [reference and endpoint limits](../validation/lmi-dualboot-reference-2026-10-21.md).
Dual-boot artifacts exist but have not been installed; the PC selector remains
locked. No phone partition or installed package changed during this reference.


## October 21: dual-boot artifacts completed, target installation pending

The operator-built full image completed its ext4 checks. A finalizer permission
error was corrected without rebuilding the image or changing global permissions.
The boot artifact and manifests now exist; raw/sparse hashes match the build
report. Kernel and DTB remain unchanged. No handset partition, boot or installed
system was modified; the PC selector is still locked pending actual validation.
See the [build result](../validation/lmi-dualboot-build-2026-10-21.md).

## October 21: same-kernel graphical/headless comparison complete

Three qualified phases spent about 99.5% suspended. Software-counter estimates
were 49.87 / 51.49 / 52.04 mA with graphics running, stopped and restored;
no reduction was demonstrated. These are gauge estimates, not calibrated
physical current. Restoration passed. See the [complete result](../validation/lmi-headless-aba-result-2026-10-21.md).

Connected gauge readback matches normal, not rapid-SOC, parameters and shows
released memory requests. No patch or data write follows. The new full-Android
snapshot helper is host-syntax-checked only, not target-validated. See the
[runtime follow-up](../validation/lmi-fg-runtime-followup-2026-10-21.md).

The prior October 20 night observer was not armed; recovered kernel logs show
29 gauge wakes returning to suspend, but no overnight battery baseline exists.
See the [return boundary](../validation/lmi-headless-and-night-return-2026-10-21.md).

## October 20: eight natural-wake read-control probes completed

Four extra counter-read bursts and four direct-current controls produced no
immediate before/after change in either current channel. The millisecond
comparison does not exclude delayed/common read effects or calibrate physical
standby current. Cleanup passed; normal policy remains installed. See the
[result and limits](../validation/lmi-read-control-result-2026-10-20.md).

## October 20: grouped isolation completed; residual remains unresolved

The one-hour grouped software-control observation retained late filtered
gauge samples around 49 mA; 95.96% of the full window was suspended. Settings
and services were restored and checked. Software/shadow/raw counter-derived
rates were approximately 86 mA in qualified sleep brackets at SOC100–96%,
so modeled accounting must remain separate from filtered endpoints and any
claim of physical current. The unbound SMB1390 child has its driver disabled
in both retained Lineage and running Mobian configurations; parent registration
does not prove a fitted chip. No fix or new kernel build is established.
See the [result and limits](../validation/lmi-minimal-scope-result-2026-10-20.md).

# Mobian status

## October 20: first read-control run ended before sampling

An early USB disconnect/reconnect cycle stopped the observer after five seconds,
with zero natural-resume probe attempts. The trace is preserved and inconclusive;
service success is not measurement success. A revised waiting phase tolerates
brief initial cycles by requiring a 20-second USB0 confirmation interval, while
retaining immediate stop on reconnect after measurement starts. All 32 host-only
tests pass. The revision is not installed/armed. See [the result and limits](../validation/lmi-read-control-first-run-2026-10-20.md).

## October 20: offline read-control analyzer ready

The candidate now includes an offline JSONL analyzer with incomplete-stream and
read-error qualification, descriptive timing/wake groups, and input-preservation
checks. All 30 simulated runtime/probe/analyzer tests pass on native Linux.
A cross-check retained eight callbacks emitted by the actual lifecycle engine
with a fake backend. No real read-control result has been fetched yet and the
handset collector was not changed. See [analysis usage and limits](../../userspace/power/diagnostics/gauge-read-control-candidate/ANALYZER.md).

## October 20: read-control candidate validated offline

A separate diagnostic observer candidate now preserves resume-entry timestamps,
probes before parent gauge reads, and stops on reconnect, read error, budgets,
deadlines or eight attempts. All 17 simulated tests pass; no phone service or
physical trial was started. It is excluded from the current build/install path.
See the [candidate and limits](../../userspace/power/diagnostics/gauge-read-control-candidate/README.md).

## October 20: corrected overnight accounting and SRAM access review

The corrected overnight observer has completed: 7 h 17 min unplugged, about 95%
suspended. Late filtered-wake samples remain near 49.3 mA; these are gauge
estimates, not independent physical current. Source review completed the DMA
access/release path and corrected a missing-function claim. No matching SRAM
access errors were found in the retained boot journal. Cached recharge_vbat is
negative, so the dynamic 4380 mV fallback is not active at that snapshot. No fix,
new build or charger-policy change follows. See [the bounded review](../validation/lmi-standby-followup-2026-10-20.md).

## October 19: diagnostic getter correction and UART follow-up

The added charge_done read is not guaranteed passive: its charger getter can
change watchdog/vote/charge state under specific conditions. The kernel's own
FG and uevent paths also invoke it; an observer-caused transition is unproven.
The first night record is preserved with this qualification, and a corrected
collector without the explicit field is now observing after operator unplug.
Retained QUP histories end in zero requests and the driver has a zero bucket;
no new UART fix, kernel build or residual-drain solution is demonstrated.
See [the bounded review](../validation/lmi-standby-followup-2026-10-19.md) for the source findings and measurement limits.

## October 19: residual accounting isolated from awake gaps

Forty-two qualified suspend brackets still give 47.86 mA software-counter
estimates; the residual is not confined to the initial awake wait. Static
analysis found a real, conditional BMS calibration caller in Android hvdcp_opti.
Its applicability and execution on lmi remain unproven; no calibration or charge
setting was changed. The long recovery test remains deferred. See the
[bounded analysis](../validation/lmi-standby-followup-2026-10-19.md). No new build or flash is required by this finding.

## Daytime follow-up: quiet natural resumes — 2026-10-19

All 42 natural gauge resumes returned toward suspension within 15.209–15.442 s.
No unplugged WakeUpScreen request was observed; UI versus MSOC differed by at
most one percentage point. Residual demand remains unresolved. The specific
newer UFS bulk-clock bug is absent from the retained downstream lane helpers.
A separate FG calibration interface remains an unverified comparison question,
with read-only follow-up now completed and no calibration or power-policy write.
The cached level is -22; the parallel-measurement vote and hardware bit are off.
These plugged readbacks do not establish an Android initialization omission.
See [the bounded review](../validation/lmi-standby-followup-2026-10-19.md) for evidence and limits.

## Passive daytime observation — 2026-10-19

The unchanged homedrag7/qualified Phoc Mobian installation completed a passive
10 h 11 min unplugged observation. Displayed capacity was 100% at unplug and
79% at the last unplugged sample, about 2 min 40 s before detected USB return.
The initial current still carried the preceding charging transition; it is not
an instantaneous discharge measurement.

There were 43 paired suspend/resume windows, accounting for 35,078.686 seconds
actually suspended within 36,668.696 seconds from unplug to replug (95.66%).
This includes the normal initial fifteen-minute awake delay. Resume reasons
were 41 msoc-delta, one msoc-high and one USB return. No unpaired callback was
found. These clock deltas establish suspension, not physical panel power.

Qualified unplugged counter intervals give software 51.05 mA and shadow
50.67 mA estimates. Raw nominal-scale accounting gives 90.39 mA; it is not a
second independent ammeter. Learned capacity stayed 2710 mAh, design 4700 mAh.
Across 37 resume endpoints more than an hour after unplug, filtered current
had a median of 49.322 mA (49.273–51.787 mA). Endpoint readings are not continuous
interval-average measurements. This is consistent with the residual order of
demand in the half-hour recovery control; the sessions are not matched causal
A/B tests and do not identify a responsible peripheral or prove calibration.

The same handset boot was retained. The observer exited successfully, no RTC
alarm or pending NPU restoration state remained, and Wi-Fi remained enabled.
No build, flash, forced suspend, scheduled RTC wake, media capture or power-policy
change was introduced for this observation. Residual standby drain remains
unresolved despite working automatic suspension and gauge-wake resuspension.

## Recovery kernel control: residual demand reproduced — 2026-10-18

An attended test in the existing Lineage 23.2 recovery measured 180.094 seconds
of deep suspend within a 181.140-second unplugged interval. Its kernel and base
DTB match the retained official Lineage boot image. This did not install a new
Mobian image, kernel or userspace package; the installed Mobian reference below
is unchanged. The operator has since returned normally to Mobian; kernel, installed package
versions, 900-second sleep timeout, empty RTC alarm and charging were verified.

For the control only, sleep_disabled was set to N and the three NPU devfreq
clients used powersave with zero requested frequency. Original recovery values
(Y and three performance governors) were restored and read back; the owned RTC
alarm was cleared, USB charging resumed, and the collector finished. Bluetooth
was blocked and no WLAN interface was present in recovery.

The software counter estimates approximately 52.8 mA. The nominal-scaled raw
counter estimates 91.7 mA, equivalent to 52.8 mA when expressed on the same
2710/4707 learned/nominal capacity scale. Shadow accounting gives 69.1 mA.
These are correlated gauge estimates, not independent calibrated measurements.
The filtered current was still affected by the preceding charge transition and
is not a steady-state result. The interval was short and started at displayed
100%; it is not directly equivalent to the prior long Android idle trials.

This reproduces roughly the corrected Mobian order of demand without Phosh or
GNOME settings daemons, using the Lineage recovery kernel. It argues against a
cause requiring those userspace services or only the Mobian kernel additions,
but does not establish a specific hardware leak or exclude shared kernel,
firmware, gauge behavior, runtime-tree or full-Android initialization differences.
Residual drain remains unresolved. See the power diagnostics README for details.

## Short automatic-suspend control after homedrag7 — 2026-10-18

An attended control with the installed homedrag7/qualified Phoc stack used a
battery inactivity timeout of 60 seconds, restored automatically to 900 seconds
on completion. Wi-Fi remained enabled. No forced suspend, RTC alarm, media
activity or CPU/NPU policy change was introduced by this collector.

Automatic PrepareForSleep arrived 60.219 seconds after unplug detection.
BOOTTIME minus MONOTONIC deltas establish 151.410 seconds actually suspended;
the only observed resume was USB return (`typec-cc-state-change`). The detected
unplug-to-replug interval was 216.413 seconds, including the initial awake wait.
The collector exited successfully, charging resumed, the handset boot identity
was unchanged, and no RTC alarm, trace instance or pending NPU recovery state
remained. The operator confirmed normal touch, application launch and scrolling
afterward.

This validates one accelerated automatic-suspend transition after the interface
updates. It does not revalidate the normal fifteen-minute delay, gauge-wake
resuspension or sustained battery drain. No natural gauge wake occurred in this
short interval. USB-return current is charging-contaminated; no calibrated
consumption or autonomy claim is made. ScreenSaver Active is lock state, not
a physical panel-power measurement. Residual standby demand remains unresolved.


## Restart button and cancellable confirmation validated — 2026-10-18

The operator built the homedrag7 pair with all 36 package tests passing.
It is now installed, with the running executable verified, empty dpkg audit,
quiet opt-in retained and no diagnostic overlay. Only Phosh restarted; the
compositor PID and handset boot ID stayed unchanged. The homedrag6 fallback
pair is retained, and the rollback timer was stopped after health checks.
Package SHA-256:

- Phosh arm64: `e04f6d8348d4ca9b3a23208bf60f8591b5414f28ccc34c3f30dd2d7e764c1760`.
- Common all: `3ef839c1f5ec25d4e3d8d6ce7a4fe7e955eb1a8345249a9c35410af6efded8f9`.

The operator confirms the Restart button is present and its confirmation can
be cancelled. Actual reboot execution has not been tested in this check.
No reboot action has been triggered by the agent. Preparation notes below
are historical where they describe the package as not yet installed.

At the operator's request, homedrag7 adds a Restart button to the long-press
power menu. It calls the existing phosh_session_manager_reboot method, using
GNOME Session's normal end-session flow rather than forcing a reboot. The
existing French catalog translates Restart as Redémarrer. The action is
disabled while locked, matching the existing Power Off policy.

The new manager/resource code compiles. XML/action/locked-state checks and the
9 stable + 6 complete profile staging checks pass. No restart action was
invoked, no package was built autonomously and nothing was installed on the
handset for this addition. The operator-run homedrag7 pair build and physical
menu/confirmation checks remain pending. The next complete recipe selects
homedrag7 with the previously qualified Phoc; the handset remains on qualified
homedrag6. All home/favorite fixes and quiet-gauge source pins are retained.


## Homedrag6 installed; bidirectional shortcut transfers confirmed — 2026-10-18

The operator subsequently built homedrag6 with all 36 package tests passing.
The new pair is installed; only Phosh restarted, while the Phoc PID and handset
boot ID stayed unchanged. Package audit and running executable checks pass.
The homedrag5 pair is retained for explicit recovery, and the transient timer
was stopped after health checks. Verified homedrag6 package SHA-256:

- Phosh arm64: `074e1aa1282b485ca65d36a1bcbb1af4b777e39d0bcc1bd261b433a183cec302`.
- Common all: `9bafbb64d3a0db9718e41861b1cca7734b20b7a8dc5c8526866b983b6de84f18`.

**Operator-confirmed:** Contacts moves from favorites to an empty home cell
and disappears from favorites; the reverse move restores it to favorites and
clears its home cell. Saved settings after that round trip confirm five
favorites with Contacts present and no Contacts shortcut on home. The earlier
five-icon screen fit remains qualified. Drawer copies, existing home shortcut
removal and a rejected cross-surface drop at capacity have not all been
physically retested on this exact pair; the corresponding source tests remain
separate evidence. No battery, camera or new full-image validation is implied.

The operator built homedrag5 with 36/36 package tests passing. The pair was
installed and only the user shell restarted; Phoc PID and handset boot ID did
not change. Running executable/package checks pass, dpkg audit is empty, quiet
opt-in is preserved and no temporary GTK module/resource overlay is loaded.
Verified package SHA-256:

- Phosh arm64: `75582138890c0a849b1fb95507f51bb11c265f9aace2022f6fd36241b53104a7`.
- Common all: `d97e103657f541cf670f2eae8b106ac3c3d9477b59fd0d734884d2a941ccc437`.

**The operator confirms all five favorites now fit entirely on screen.** The
reported intermittent removal problem was not declared fixed by the operator.
Further clarification identifies a shortcut remaining in favorites after a
drag to home. Settings confirm Snapshot in both favorites and one home slot:
this is the implemented cross-surface copy behavior, not duplicate home-slot
entries. These statements do not prove that every earlier menu-delay report
had the same cause; no separate menu-delay success is claimed.

Homedrag6 marks saved shortcut origins and transfers between dock and
home instead of copying. Drawer drags still copy, and same-surface drags still
reorder/move. Destination and source snapshots are checked before writing;
delayed GSettings updates are committed together or reverted if either write
is refused. A full dock or failed destination does not remove the source.
Existing destination shortcuts permit removing the other saved copy without
adding another destination entry. Compiled tests cover commit and cancellation
on a concurrent source edit, source removal/list shape, geometry and the
existing shortcut-removal protections. The subsequent package build and bidirectional physical transfer checks pass
as detailed above; older homedrag5 state below is historical.

The complete-image recipe now selects homedrag6 plus the same Phoc correction.
Actual homedrag5/Phoc/camera inputs passed temporary profile staging; no full
image/kernel build or flash was performed.


## Five-favorite dock installed; width and removal-delay follow-up — 2026-10-18

The homedrag4 pair was operator-built with 36/36 Phosh tests passing and
installed without changing the compositor PID or handset boot ID. Verified
package SHA-256:

- Phosh arm64: `cd7f3400e8deaf348f6839bedb00b37a0f00543a7abaf54dd79bca6c91596141`.
- Common all: `fb3fa9f5956aaced9eaa55acb0648cbc86616eec6e6a7f7b1bfe5bb70af940fd`.

The operator successfully added a fifth favorite. The initial replacement
report was withdrawn; settings retained five favorites without replacement,
while the attempted extra Settings shortcut was in the separate home grid.
The fifth dock icon nevertheless extends beyond the right edge. A private
screenshot confirms clipping. Runtime measurements show 90px allocations for
84px home cells and 69–70px favorite cells despite their 64px requested size:
GtkFlowBoxChild theme padding expands the layout beyond the 360px display.

Shortcut removal also showed intermittent delays of several seconds. A shell
restart with a read-only observer made it work again; no removal fix had been
installed at that point. The observer recorded matching slot/desktop IDs on a
successful activation. The low-priority deferred removal is a possible delay
mechanism; the user's exact intermittent trigger is not established. The
observer/drop and its rollback timer have since been removed.

Prepared homedrag5 removes theme padding from home/favorite cells only and
schedules deferred removal at normal main-loop priority, still after menu
activation returns. Compiled regression tests pass: four real home buttons
need 354px and five favorites 344px (plus 6px external dock margins). Removal
also passes with a continuously ready normal-priority source; concurrent
settings protection is retained. **The homedrag5 package build and hardware
validation are pending.** The phone remains on normal homedrag4. No kernel or
image was rebuilt. The next complete recipe selects Phoc lmishelldnd1 plus
homedrag5; real homedrag4/Phoc/camera inputs also passed temporary full-profile
staging before that selection was advanced.


## Five favorites by drag prepared — 2026-10-18

The operator requested up to five favorites added directly by drag. Candidate
homedrag4 accepts a new desktop ID on a favorite or dock whitespace, preserves
existing reorder and rejects a sixth entry. Menu addition observes the same
limit. The dock uses 48px icons, 64px clamps and a five-column maximum. Source
preparation and ordering/limit host tests pass; package creation and physical
five-icon checks remain pending. The handset still runs the physically checked
homedrag3 plus Phoc lmishelldnd1. The next complete-image recipe selects these
Phoc fixes and homedrag4 so it cannot silently omit dock additions.


## Phoc DnD and homedrag3 installed; shortcut removal confirmed — 2026-10-18

The operator built the homedrag3 pair with all 36 normal Phosh tests passing.
Verified package SHA-256:

- Phosh arm64: `a4bb37f88da8f42f4073395006e851fad934581f8821a75315135e5a2ccfc294`.
- Common all: `7529cac7002fc28342277afa573e26d6b09bf3a394966d9078ae3f42eabcd82b`.

Both were installed; the apt simulation selected only the pair. The running
Phosh executable matches the new installed binary, the package audit is empty,
quiet-gauge opt-in remains active and no diagnostic module/resource overlay
is loaded. Restarting only the user shell kept the same Phoc PID and handset
boot ID. The rollback timer was stopped after health checks; paired homedrag2
packages and the explicit rollback script remain available.

**The operator confirms “Retirer de l’accueil” removes the shortcut.** The operator also confirms direct lateral reorder with a visible preview,
compact label spacing, return from an application by the bottom-edge swipe,
and drawer opening. Persistence across another session has not been retested. No complete image
was rebuilt or re-flashed. The next full-image recipe selects Phoc lmishelldnd1 and the homedrag4
five-favorite follow-up; no new image has been built.

The operator built Phoc `0.46.0-1+lmishelldnd1`; package SHA-256 is
`e862d58b20aa274b01184e89e0b3d25048de951fb70f161235854fe4fe970ac6`.
Installed dependencies were already satisfied and only Phoc changed. The stock
0.46.0-1 package was retained and verified for recovery. Activating the session
was followed by a complete handset reboot (uptime confirmed); the cause is not
established and no reboot command was issued. After reconnecting, both Phoc
and Phosh were active with running executables matching their installed files,
an empty package audit and quiet-gauge opt-ins retained. The transient rollback
timer did not survive the reboot; the explicit rollback script/package remains.

The operator confirms home drag/drop now works. Favorite reorder initially
required an upward detour. Temporarily forcing the global home drag mode to
NONE enabled direct lateral reorder; the probe was then removed and normal
Phosh restored. This confirms a second gesture arbitration issue in addition
to the compositor routing defect.

Phosh `homedrag3` adds a home-only “Retirer de l’accueil” menu action,
compact icon/name grouping, an explicit 48px drag preview in every direction,
and disables the global layer drag while the overview is fully unfolded.
Folded app-edge behavior remains unchanged in source; its physical validation
is pending. Removal checks the exact slot and desktop ID, runs after menu
activation returns, and rejects an intervening settings change. It does not
uninstall the application or alter favorites.

The updated app-grid-button test (including removal and concurrent-settings
protection) was compiled and passes. A no-rebuild run of the 36 available Phosh
tests passes; other statically linked tests were not all rebuilt in that run.
The subsequent operator package build passed all normal tests; remaining
physical checks are listed above. The retained complete-image profile still selects homedrag2 and has
not yet been promoted to this new candidate.

The Phoc package's upstream test command was space-indented and parsed as a
Make variable assignment, so packaging alone had not run the tests. The recipe
now uses a tab, an unused Xvfb display, and private /dev/shm. Running the 17
already-built tests with those resources passes all 17; initial missing-shared-
memory failures are not counted as compositor regressions.

## Native drag v2 hardware failure; Phoc routing candidate — 2026-10-18

The operator confirms that homedrag2 still cannot deposit shortcuts or reorder
favorites: a small drag icon appears, but releasing has no effect. A real
callback trace observed drag begin and home reveal, with no destination receive
or settings-apply callback. Two reversible gesture isolation probes failed to
restore drops; all probe overrides and timers are removed.

The pinned Phoc 0.46.0 source bypasses grabs on shell layer surfaces, including
potentially the data-device grab. A targeted candidate preserves DnD grabs and
yields layer swipe arbitration during DnD. Its host routing regression test
fails on the original and passes after the patch; preparation/resume/tamper
checks pass. **Package build, upstream tests and handset validation remain
pending.** No kernel change or new image is required for this trial. See
[Phoc DnD candidate](../../userspace/phosh/phoc-layer-dnd-candidate/README.md).
The handset remains on normal homedrag2; the complete image previously flashed
still contains homedrag1. Earlier pending-test statements below are historical.

## Native drag v2 installed; physical retest pending — 2026-10-18

The operator built the homedrag2 Phosh/common pair. Verified package SHA-256:

- Phosh arm64: `0f614db3616380c0935b298c6a975e0c47437931a57998d6e29ad91f2db555d7`.
- Common all: `e26cdcc6ff9dc9ce8d0fc856dc71fb9ac18bfb09a1dbb83824da829c6e70a57b`.

The two packages were installed on the complete-image handset. Apt's simulated
plan selected only that pair, but real local installation hit an internal path
error. The armed fallback restored v1 successfully. A subsequent offline dpkg
installation of the same verified pair succeeded and the package audit is empty.

Phosh restarted with a stable PID and an executable matching the installed
file; its automatic-home-reveal marker is present. Both quiet-gauge opt-ins
remain active, the old UI overlay is absent, the normal 900-second suspend
default is preserved and no NPU recovery is pending. The temporary restart
permission override was removed. The rollback timer was stopped after these
health checks; the old pair remains available for explicit recovery.

This qualifies package installation and shell startup only. Real automatic
drawer dismissal, shortcut deposition/persistence and favorite reorder await
the operator's physical test. No camera acquisition, new flash or kernel
change was performed.


## Complete-image boot and failed drag test — 2026-10-18

The operator flashed and booted `mobian-lmi-complete-20261018`. SSH inspection
confirmed the expected homedrag1 Phosh/common, quiet-gauge GSD, UPower and
Snapshot versions, an empty dpkg audit, both quiet-resume opt-ins, 900-second
battery suspend default, all-apps mode and absence of the old home overlay.
Chatty was not running; metadata indexing remained masked. The document portal
reported a FUSE mount failure and getty@tty1 lacked its terminal; these remain
separate open issues, not successful app qualification.

An initial positive drag report was withdrawn by the operator. Home-slot
settings remained empty. The icon followed the finger but the drawer did not
hide and no shortcut was deposited. **Native home drag is not validated.**
Candidate homedrag2 now reveals home on drag start and removes the broad deck
drop target. All 36 Phosh tests and the profile staging checks pass; package
creation, installation and the new hardware trial remain pending. The next
complete-image profile selects the paired homedrag2 packages. The already
built/flashed image remains identified as homedrag1, with its original checksum.


## Complete image successfully built — 2026-10-18

The operator completed `mobian-lmi-complete-20261018` with exit status zero and
the `COMPLETE_IMAGE_WITH_NATIVE_HOME_AND_SNAPSHOT` marker. Filesystem checks
and the builder's raw/sparse roundtrip passed. The sparse artifact is
3,660,046,632 bytes with SHA-256
`67413598eab1cf646e9f8c22606aa29d33a52d8e9d37a933c2571e8cc97d7a85`;
its checksum was independently re-read after build completion.

Offline rootfs inspection confirms Phosh/common
`0.46.0-3+deb13u1+lmigaugewake3+homedrag1`, GSD
`48.1-1+lmiquietgauge3`, UPower `1.90.9-1+lmi1` and Snapshot `48.0.1-1`.
The complete-profile marker, camera bundle manifest, launcher and service are
present. The old resource-only home overlay is absent as required by the native
widget bindings. The existing RPMh boot/kernel is reused, not rebuilt.

This is a successful integrated image build, not post-flash hardware
qualification. Native touch drag, Snapshot foreground/background/exit behavior
and retained application/battery behavior must be checked after installation.
Front-camera, camera zoom/flash, reliable video and corrected autonomy are not
claimed. No phone flash or acquisition was performed during artifact checks.


## Complete-build chroot terminal repair — 2026-10-18

The operator's next attempt completed the native Phosh packages, then stopped
while installing camera build dependencies in the retained ARM chroot. The
chroot lacked mounted devpts and proc; apt reported `posix_openpt (19)` and
the inspected processes were stopped. A private live mount repair passed its
PTY probe, but resuming exposed a pending KeyboardInterrupt and ended the
build. No automatic full-build restart was performed.

The recipe now prepares private proc/devpts mounts and a matching ptmx bind,
probes the chroot PTY, and disables apt's optional PTY logging for this dependency
step. Repeating mount preparation passes. The interrupted chroot's dpkg audit
is empty. Camera preparation can resume only after all source/runtime assets
match fresh preparation; a tampered partial bundle is rejected. The existing
partial bundle passes those checks. Completed Phosh packages are reused by
the same complete-build command. Image generation remains pending.


## Native drag null-application regression fixed — 2026-10-18

The operator's combined package/image build stopped at the upstream
`app-grid-button/null_app_info` test. Native drag setup called
`g_app_info_get_id(NULL)`, which is invalid although constructing a Phosh
button without app info is supported. Both launcher and favorite paths now
preserve that contract. The existing null-info test also exercises a favorite.

The failed build tree and prepared-input identities were repaired together.
A fresh preparation from the verified original sources matches those repaired
inputs exactly; the quiet-gauge source hash remains unchanged. After targeted
recompilation/relinking, all **36 Phosh tests pass**, with zero failures or
skips. No test was disabled. The full package/image build remains operator-run;
restart the same complete-build command. No phone state was changed.


## Combined full-image recipe prepared — 2026-10-18

The [complete operator entry point](../../build/profiles/lmi-current/COMPLETE-BUILD.md)
now combines native Phosh home/favorite drag package compilation, experimental
Snapshot rear-camera bundle compilation and full image generation. It retains
the current battery and application fixes and reuses the installed RPMh kernel.
The native UI and schema are paired; the older resource overlay is omitted.
No build, flash or acquisition was started by the agent. Native drag gestures
and the newly integrated camera lifecycle remain pending post-flash tests.


## Favorites home and separate drawer — 2026-10-18

The operator requested hiding the complete grid from the home page. A scoped
resource overlay now keeps favorites in a bottom dock and the full app grid in
a vertical drawer; its chevron is below the favorites. The operator confirmed
drawer access and favorite launch/close/return, and the final alignment was
checked with a native Phosh screenshot. All applications are shown and the
adaptive-only filter button is hidden using the native setting.

The layout is persistent on the handset and staged for the next image. The
flashed `20261018-r1` image predates this adaptation. Quiet-gauge opt-in remains
active, but no new battery result after the UI change is claimed. No package
or kernel build was needed. Global lateral minimization is unimplemented.

## Fresh-image automatic sleep and gauge wake — 2026-10-18

The first passive observation of `mobian-lmi-current-20261018-r1` lasted
1,104.60 seconds cable-free, with the normal 900-second battery suspend delay
and Wi-Fi left enabled. The screen lock became active about 13 seconds after
the unplug poll; automatic PrepareForSleep followed at 913.20 seconds.

Boottime-minus-monotonic deltas show 174.60 seconds actually suspended over
two cycles. The first sleep lasted 157.80 seconds and ended on `msoc-delta`.
No WakeUpScreen or unlocked-state signal appeared between that gauge wake
and the next sleep request, which followed about 15.21 seconds later. The
second sleep lasted 16.80 seconds and ended on the USB Type-C cable return.
These are software transition observations, not a direct optical screen trace.

The journal confirms two NPU zero-target applications and two original-policy
restorations. Awake governors/targets match their reviewed performance
baseline, no recovery is pending, the RTC alarm is empty and the passive
collector finished. The operator then confirmed normal touch/application
interaction and screen power-button behavior.

This qualifies automatic sleep, one quiet gauge resume and recovery after
USB return on the integrated fresh image. It does not establish long-duration
autonomy or calibrated physical drain. The prior residual-consumption
investigation remains unresolved; USB-return battery endpoints may already
be affected by charging.

## Fresh current image boot validation — 2026-10-18

The operator successfully built and flashed `mobian-lmi-current-20261018-r1`
(userdata only) and reported a responsive, normal interface. Build exit status
was zero; filesystem checks and the builder's raw/sparse roundtrip passed.
The 3,648,024,868-byte sparse image has SHA-256
`d89ac3319e94a57955f560875cc15fbaf2fa2d728d1112de1b5d9b644460163b`.

SSH inspection after this fresh boot confirmed Phosh/common
`0.46.0-3+deb13u1+lmigaugewake3`, GSD/common `48.1-1+lmiquietgauge3`
and UPower `1.90.9-1+lmi1`. Both quiet-resume service opt-ins are active;
package audit is empty. Chatty's daemon autostart is hidden, its desktop
activation guard is present, and no Chatty process started automatically.
The incompatible indexer is masked. The NPU suspend opt-in is present with
no pending recovery. The existing RPMh kernel was retained.

The normal battery suspend delay is 900 seconds, with no automatic suspend
on AC. A first automatic-sleep observation is now pending; this boot check
does not yet qualify fresh-image suspend/resume, application functionality,
long-duration drain or the experimental camera bridge. Earlier October 18
preparation/interruption entries below describe superseded build attempts.

## Measurement interpretation update — 2026-10-16

The latest overnight record spent 95.03% of the observed interval suspended.
Filtered gauge endpoints were near 50 mA. A present SRAM nominal-capacity
read of 4,707 mAh versus 2,733 mAh learned numerically explains much of the
raw/software counter-scale difference; 85.923 mA raw becomes 49.889 mA after
that numerical normalization. These correlated quantities are not independent
current calibration. The displayed percentage follows a separate MSOC/smoothing
path, so its observed decline cannot simply be divided by the capacity ratio.
Residual standby drain remains unresolved; no new power-saving fix is claimed.
See [the consolidated measurement limits](../validation/quiet-gauge-night-2026-10-13.md).

## Current installed handset and next-image pins — 2026-10-15

The handset now runs Phosh/common `0.46.0-3+deb13u1+lmigaugewake3` and
GSD/common `48.1-1+lmiquietgauge3`, with persistent quiet-resume opt-ins and
debug off. The existing RPMh diagnostic kernel and suspend-only NPU policy
are unchanged. USB cycles and repeated quiet gauge resumes passed. The latest passive night
(14–15 October) lasted 9 h 17 min with 95.29% actual suspension; all 40 exact
msoc-delta wakes stayed blank and returned to suspend. Displayed capacity was
100% at departure and 79% at the charging return poll. Counter estimates remain
model-dependent; residual standby drain is unresolved. This observation does
not qualify a new image build.

The current image profile now pins this v3 pair. Debian package identities,
private input sums, installed-version checks and host rejection/staging tests
are updated together. Existing rollback packages are retained. This is a
host-checked recipe update, not a newly built or hardware-validated image.
Heavy image builds remain operator-run. Earlier dated sections are historical.
See [the consolidated validation and counter limits](../validation/quiet-gauge-night-2026-10-13.md).

## Historical daytime boundary — 2026-10-12

An eleven-hour return showed 97% to 59%, but only 16 min 39 s of actual sleep.
The initial explicit suspension began before screen blanking and therefore did
not qualify for quiet resume; no later automatic suspension was recorded.
This is an invalid quiet-night comparison and an unresolved automatic-sleep
boundary. The USB-cycle source draft is tested locally but remains unbuilt and
uninstalled. The installed versions above/below remain unchanged.
See the [protocol and transition evidence](../validation/quiet-gauge-overnight-2026-10-12.md).


## Overnight installed-userspace observation — 2026-10-12

An 8 h 51 min cable-free observation retained the qualified quiet-resume pair,
the same kernel/NPU policy and Wi-Fi enabled. The handset stayed in the same
boot, slept about 95.52% of the interval and recorded 32 gauge-only resumes
without software screen unblank. Displayed charge fell from 100% to 83%.
Differently modelled counters estimate about 49 and 87 mA; neither is calibrated
physical current. The correction persists, but standby drain remains unresolved.
See the [overnight result](../validation/quiet-gauge-overnight-2026-10-12.md).
This does not qualify a newly built image.


## Historical handset boundary — 2026-10-11

The handset is back on Mobian after the LineageOS battery comparison. It
retains the installed RPMh diagnostic kernel and the NPU suspend policy.
The qualified Phosh/GSD quiet-resume packages are now installed with
persistent opt-ins and without trial debugging: Phosh
0.46.0-3+deb13u1+lmigaugewake2 and GSD48.1-1+lmiquietgauge1.

Two observed gauge wakes kept the software screen state blank, released the
Phosh delay inhibitor and returned to actual deep sleep without the former
five-second timeout. USB wake, power-button operation, touch and application
interaction passed. This is a userspace correction, not proof of resolved
standby drain or a newly qualified image. The overnight result above supersedes the pending long-duration observation;
standby drain remains unresolved. See the [power record](../../kernel/diagnostics/power/README.md).

The earlier Android overnight/daytime comparison remains historical evidence
of lower apparent idle drain than Mobian, with its gauge and timing limits.
The operator's Android installation did not preserve a snapshot of the
then-current Mobian userdata. Historical Mobian image identities below do
not identify the subsequently modified handset filesystem.

## Current Mobian userspace state — updated 2026-10-03

The current validated Mobian/Phosh userdata family is based on the external
`archi-validation-02` golden image and its `daily-base` derivative. The
golden image booted with the durable original D-repro D-v43 boot; Phosh,
touch/unlock, DSI-1, GPU72 GLES2/Zink/Turnip/KGSL acceleration, GNOME Console
and Calculator were exercised. `daily-base` separately validated the
time-seed correction and responsive unlock with only Chatty's daemon
autostart hidden. Exact image identities and boundaries are in
[`current build status`](CURRENT-BUILD.md).

`daily-base-audio-fw-test` is an experimental userspace profile paired with
a temporary reset-GPIO diagnostic boot, not a replacement for the durable
original boot. WCD938x and TFA9874 now bind, ALSA registers, and direct S16_LE
and S24_LE playback completes. Later S32_LE frontend tests produced clear
music, confirmed through a local PipeWire speaker route on 2026-10-03.
Microphone capture and KRecorder WAV saving were subsequently tested on
2026-10-04 (see the audio integration record below). Full UCM2, headset/earpiece
routing and durable boot deployment remain pending.

The proprietary TFA firmware is external and is never tracked. Neither the
diagnostic boot nor any userdata image is stored in Git. Kernel and userdata
bit-for-bit reconstruction from all sources is not demonstrated. See the
[`2026-09-29 audio progress note`](../validation/archi-validation-02-audio-progress-2026-09-29.md).

The M0 Weston result below belongs to a distinct Mobian/M0 environment. It is
not evidence that Weston works on the separate D-v43/OpenRC system, whose
Weston experiments remained black.

## M0 BASE — validated on hardware

Validated on Xiaomi `lmi` hardware with the downstream D-v43 kernel.

Confirmed:

- Debian GNU/Linux 13 (trixie)
- systemd as PID 1
- root filesystem on `/dev/loop0p2`
- USB RNDIS preserved across switch_root
- `usb0` configured as `172.16.42.1/16`
- SSH root login by public key
- kernel `4.19.325-cip128-st12-perf`

The M0 BASE image is intentionally not stored in Git.

## M0 DISPLAY — VALIDATED ON HARDWARE

Validated on Xiaomi `lmi` hardware:

- KMS continuous-splash release with Debian `modetest` works
- seatd with `SEATD_VTBOUND=0` works
- Weston 14.0.2 DRM/Pixman with kiosk shell works
- `DSI-1` drives the physical panel
- a red background is physically visible
- downstream `msm_drm` requires the tracked Weston workaround that
  de-duplicates indistinguishable formats in the legacy no-`IN_FORMATS`
  fallback

See `docs/validation/mobian-m0-display-hardware-validation-2026-09-02.md` for the exact
experimental evidence and backend identities.

This success is specific to that M0 Mobian rootfs and display setup. It must
not be merged with the later D-v43/OpenRC Weston 14 tests; see
[`D-v43 Weston boundary`](../validation/d-v43-weston14-boundary-2026-09-26.md).

## M1 PHOSH — VALIDATED ON HARDWARE

The M1 graphical session and basic Phosh interaction were validated on Xiaomi
`lmi` hardware. The clear-KMS marker was visible, Phoc acquired `DSI-1` with
the Pixman renderer, and the Phosh lock screen appeared. Touch input and the
swipe-up gesture worked, the passcode prompt allowed the session to be
unlocked, and the Phosh desktop was then displayed with its applications and
icons.

This milestone validates the graphical bring-up and basic Phosh interaction.
It does not validate GPU acceleration, every Phosh function, or readiness for
daily use.

## M1 GPU — TURNIP/KGSL VULKAN ENUMERATION VALIDATED ON HARDWARE

An isolated native Debian Trixie arm64 build of Mesa 25.0.7, configured with
Gallium Zink, Vulkan Freedreno and `freedreno-kmds=msm,kgsl`, successfully
loaded Turnip's KGSL backend on Xiaomi `lmi`. Turnip opened
`/dev/kgsl-3d0`, identified `Turnip Adreno (TM) 650`, and completed
`vulkaninfo` physical-device enumeration with exit status zero. The validated
`libvulkan_freedreno.so` SHA-256 is
`dc46ac80f2322142e5ba17235e7cfd019f13c41157a34965cc5494622b84324d`.

This validates Vulkan enumeration only. GPU command submission, rendered
output, EGL, OpenGL/OpenGL ES through Zink, Wayland/dma-buf interoperability,
GBM, KMS scanout and accelerated Phoc remain unvalidated. See
`docs/validation/mobian-m1-a650-turnip-kgsl-hardware-validation-2026-09-08.md`.

## M1 GPU — ZINK/TURNIP/KGSL OFFSCREEN RENDER VALIDATED ON HARDWARE

The isolated native Debian Trixie arm64 Mesa 25.0.7 runtime has now completed
a real OpenGL ES 3.2 offscreen render through EGL surfaceless, Gallium Zink,
Vulkan Turnip and KGSL on Adreno 650. A dedicated 16x16 pbuffer test submitted
`glClear`, synchronized with `glFinish`, read a pixel back and obtained
`PIXEL_RGBA=64,128,191,255` for the requested `(0.25, 0.50, 0.75, 1.0)`
colour. `PIXEL_CHECK=PASS` and the process returned zero.

This supersedes enumeration as the strongest validated GPU milestone, but it
remains offscreen. A subsequent GPU-58 test validated process-local dma-buf
export/re-import through Turnip/KGSL; Wayland presentation and interoperability
with downstream `msm_drm` remain separate. See
`docs/validation/mobian-m1-a650-zink-turnip-kgsl-offscreen-hardware-validation-2026-09-08.md`.

## M1 GPU — GPU-66 PATCHED CROSS-DEVICE ZINK RENDER VALIDATED ON HARDWARE

GPU-66 separately validated the corrected cross-compiled Mesa 25.0.7 path.
Its opt-in Zink change selected the isolated GPU-53 Turnip/KGSL device when
the surfaceless EGL display could not be matched through the normal DRM
display-device path. The isolated stack created an OpenGL ES context, cleared
a 1x1 RGBA8 pbuffer to green, completed the work and read back the exact value
`0,255,0,255` with exit status zero.

This path directly links the matching `libEGL.so.1` and `libGLESv2.so.2`
frontends to `libgallium-25.0.7.so`, where Zink is built in. It does not use
`zink_dri.so`, `libdril_dri.so`, GBM, GLX, Wayland or X11. The system Vulkan
loader remained in use, while EGL, GLES, Gallium and the GPU-53 Turnip ICD
were selected from an isolated bundle. System Mesa was not replaced. Phoc and
Phosh stayed running and `DSI-1` stayed connected; no GPU fault or kernel
crash occurred. This validates one tiny offscreen GLES operation only, not
desktop acceleration or presentation. See
`docs/validation/mobian-m1-gpu66-patched-zink-turnip-kgsl-hardware-validation-2026-09-09.md`.

## M1 GPU — GPU-67 PROGRAMMABLE GLES2 SHADER DRAW VALIDATED ON HARDWARE

Building on GPU-66's isolated clear/readback boundary, GPU-67 compiled a GLES2
vertex shader and fragment shader, linked them, and submitted exactly one
full-screen triangle through the same patched Mesa 25.0.7 Zink, system Vulkan
loader, isolated Turnip, KGSL and Adreno 650 path. The draw rasterized into a
4x4 RGBA8 pbuffer and all 16 read-back pixels matched the shader-selected
green value `0,255,0,255`; the process returned zero.

This validates one bounded shader execution, triangle rasterization,
framebuffer-write and readback path only. It does not validate general GLES2
or GLES3 correctness, textures, uniforms, VBOs/VAOs, FBOs, large targets,
performance, sustained rendering, Wayland or Phoc acceleration, dma-buf
interoperability, GBM, KMS/DSI presentation, desktop OpenGL or production
readiness. System Mesa remained unchanged, Phoc and Phosh stayed running,
`DSI-1` stayed connected, and no relevant GPU or kernel fault occurred. See
`docs/validation/mobian-m1-gpu67-shader-draw-hardware-validation-2026-09-10.md`.

## M1 GPU — TURNIP/KGSL DMA-BUF EXPORT/REIMPORT VALIDATED ON HARDWARE

The isolated ARM64 GPU-57 self-test created a 4096-byte exportable Vulkan
buffer through Turnip/KGSL, wrote a deterministic pattern with the GPU,
exported its allocation as a dma-buf, imported the same dma-buf into a second
Vulkan allocation, accessed it through the imported buffer and verified every
word through an independent readback buffer. All capability, ownership,
submission, content and cleanup checks passed; `GPU58_SELFTEST_RC=0`.

This validates Turnip/KGSL dma-buf export and same-driver re-import on real
hardware. It does not validate PRIME import by downstream `msm_drm`, KMS
framebuffer creation or scanout, display formats/modifiers, UBWC, cross-driver
synchronization, Wayland or accelerated Phoc. See
`docs/validation/mobian-m1-a650-turnip-kgsl-dmabuf-hardware-validation-2026-09-08.md`.

## M1 PHOSH SPONTANEOUS DISPLAY WAKE — USERSPACE CAUSE AND WORKAROUND VALIDATED

WAKE7 through WAKE17 traced the spontaneous display-on cycle to the
`gnome-settings-daemon` power plugin's session-idle policy. A Mutter
`IdleMonitor` watch owned by `gsd-power` fired immediately before the
ScreenSaver/DisplayConfig activity that re-enabled `DSI-1`; the display was
disabled again roughly 15 seconds later. Changing the configured inactive
timeouts from 900 to 1200 seconds moved the long watches from 900000/450000 ms
to 1200000/600000 ms, establishing the causal mapping.

Setting both `sleep-inactive-ac-type` and `sleep-inactive-battery-type` to
`'nothing'` removed those long autosuspend watches. A passive 700-second
validation then observed no spontaneous `DSI-1` on/off event and no new
`gsd-power` error. The final validated runtime state restores both timeouts to
900 seconds while retaining type `'nothing'` for AC and battery. This explains
the observed symptom through userspace policy; it does not establish a general
kernel wake-source result or validate every suspend/resume path. See
`docs/validation/mobian-m1-gsd-power-spontaneous-wakeup-validation-2026-09-06.md`.

## M1 WIFI — VALIDATED ON HARDWARE

Manual bring-up on `lmi` with D-v43 completed the QCA6390 CNSS/WLFW sequence,
created `wlp1s0`, scanned nearby BSS entries, associated with WPA2, obtained a
DHCP lease and default route, and preserved the independent `usb0` SSH path.
The kernel dynamically selected `bd_j11gl.elf`; it must not be overridden with
the older historical `bd_j11.elf` default.

The systemd implementation under `userspace/wifi/files/systemd` and
`userspace/wifi/scripts`, together with the integrated Debian `wpasupplicant`,
is now validated on hardware in M1 REPRO v3. The image
completed firmware bring-up, `FW_READY`, qcacld probe, WLAN creation,
automatic SSID listing, CLI WPA2 association, DHCP, DNS, and Internet access
while preserving USB SSH. No Wi-Fi profile or credential is tracked. See
`docs/validation/mobian-m1-wifi-hardware-validation-2026-09-03.md`.

## M1 REPRO v2 IMAGE — HARDWARE-TESTED / CORRECTIONS REQUIRED

The reproducible M1 Phosh/Wi-Fi rootfs and phone images were built and
validated on the host. The final ext4 has the expected `pmOS_root` label and
UUID, passes `e2fsck -fn`, and the Android sparse image round-trips bit-for-bit
to the final raw image. Package installation, service enablement, Phosh/Pixman
configuration, the AArch64 property shim, and the absence of proprietary
Android payloads in the image were checked.

This exact image subsequently booted on the phone. Its low-level systemd Wi-Fi
automation succeeded, and its Phosh/Pixman stack worked when the splash unit
was started without its stale `dev-dri-card0.device` dependency. Automatic
display startup was blocked by that inherited dependency; Wi-Fi association
needed runtime installation of `wpasupplicant`; and time synchronization
needed runtime installation of `systemd-timesyncd`. Those findings produced
the recipe corrections subsequently validated in v3. See
`docs/validation/mobian-m1-repro-v2-hardware-validation-2026-09-04.md`.

## M1 REPRO v3 — VALIDATED ON HARDWARE

The v3 userdata image booted on Xiaomi `lmi` with D-v43 and reached Phosh
automatically without SSH intervention. The corrected splash unit has no
`dev-dri-card0.device` dependency; its bounded wait for the real character
device allowed clear-KMS, seatd, Phoc/Pixman on `DSI-1`, the lock screen, and
the unlocked Phosh desktop to start normally.

The integrated low-level QCA6390 automation and `wpasupplicant 2:2.10-24`
provided WLAN discovery, scanning, CLI WPA2 association, DHCP, routing, DNS,
and Internet access. Integrated `systemd-timesyncd 257.13-1~deb13u1`
synchronized the system clock after networking became available; this does
not repair the incorrect hardware RTC.

After the v3 image validation, a clean runtime experiment additionally
validated `PAMName=login` with `XDG_SEAT=seat0`: logind created an active
Wayland `Class=user` session on graphical `seat0` with `VTNr=0`, Phoc remained
functional through seatd, and the Phosh Polkit agent registered for that
session. NetworkManager scan, radio and network-control authorization passed
for the real GNOME Settings PID and D-Bus name, and Wi-Fi controls worked in
the UI. This setup is now tracked by the M1 recipe but still requires
post-rebuild hardware validation; it was not present in the original v3
image. `settings.modify.system` correctly remains an administrative action.

That persistent session setup was subsequently validated in v4. Still open
are timezone control, UPower/battery reporting, colored boot rectangles,
power-button suspend/wake, screenshot integration, touch/UI latency, observed
Settings launch instability, and the eventual default application set.
Administrative system-connection editing continues to require its expected
authentication rather than a policy bypass. See the v3 hardware note and
`docs/validation/mobian-m1-phosh-logind-polkit-validation-2026-09-04.md`.

## M1 REPRO v4 — VALIDATED ON HARDWARE / KEYRING INTEGRATION TO REVALIDATE

M1 REPRO v4 was built from commit `d1469e8`; its Android sparse userdata
SHA-256 is `84361c4d7a1bced22046e8359d17865a55983ab730a15bd0489ed98d40fa8c92`.
It booted automatically into the validated clear-KMS, seatd, Phoc/Pixman and
Phosh path. The persistent PAM/seat configuration created an active Wayland
logind user session on graphical `seat0` without a VT, and the Phosh Polkit
agent registered correctly. The lock screen, touch, swipe-up, passcode unlock
and desktop remained functional.

The remaining Wi-Fi GUI failure was not caused by Phosh's process retaining
the lingering user manager's audit session. NetworkManager registered the
Phosh NetworkAgent and sent `SaveSecrets` and `GetSecrets` on the fixed
SecretAgent D-Bus path. Phosh returned
`org.freedesktop.NetworkManager.SecretAgent.Failed` because
`org.freedesktop.secrets` was unavailable: v4 contained `libsecret` but not
`gnome-keyring`. Installing Debian `gnome-keyring 48.0-1` at runtime supplied
the activatable Secret Service, and GNOME Settings Wi-Fi connection worked
immediately without reboot or manual daemon startup.

The recipe now pins `gnome-keyring 48.0-1`. Its presence and automatic Secret
Service activation remain to be validated in the next rebuilt image. No
credential, connection profile, permissive Polkit rule or forced daemon start
is tracked. Detailed evidence is in
`docs/validation/mobian-m1-repro-v4-hardware-validation-2026-09-04.md`.

## M1 REPRO v5 — RUNTIME STARTUP FIXES VALIDATED / REBUILD REQUIRED

M1 REPRO v5 was built from commit `593676f`; its Android sparse userdata
SHA-256 is `b4adb244c686dcbbc1c10cce9087c792f69b8410080995893336ddd1f6a3f142`.
It retained the validated automatic display, PAM/logind/seat, Phosh, touch and
GUI Wi-Fi paths, including first-time PSK entry through the Secret Service.

The integrated keyring package initially added a roughly 90-second delay:
three legacy XDG autostarts requested GNOME startup notification after the
systemd user service had already started the same daemon. Runtime overrides
adding `X-GNOME-HiddenUnderSystemd=true` to the `secrets`, `pkcs11`, and `ssh`
entries removed the timeout while preserving `org.freedesktop.secrets` and GUI
Wi-Fi operation.

UPower separately delayed Phosh by two 25-second D-Bus timeouts because
systemd 257.13 could not create the `PrivateUsers=yes` user namespace on D-v43
and exited with `217/USER` before starting `upowerd`. A drop-in changing only
`PrivateUsers=no` started UPower successfully; all other sandboxing remained.
With both corrections applied, Phosh reported ready after 1.65 seconds and the
lock screen appeared at roughly 40 seconds from boot.

Both hardware-tested corrections are now represented in the recipe but still
require validation from a rebuilt image. Detailed evidence is in
`docs/validation/mobian-m1-repro-v5-hardware-validation-2026-09-05.md`.

## M1 REPRO v6 — VALIDATED ON HARDWARE

M1 REPRO v6 was freshly built from commit `d054ba8`; its Android sparse
userdata is 1,881,808,716 bytes with SHA-256
`b6e7c3bbb57e4edd1f17c829ded37b7c8ce94b883329d34d983cb05f44a30a00`.
The build completed with a clean filesystem check, the Windows transfer hash
matched, and all three sparse userdata segments flashed successfully.

This image reproduces both persistent startup corrections. The three GNOME
Keyring autostarts no longer cause their roughly 90-second registration
timeout, while the systemd user daemon and `org.freedesktop.secrets` remain
available. The UPower drop-in reports `PrivateUsers=no`; `upower.service`
starts successfully without `217/USER`. GNOME Session started in about 120 ms,
UPower acquired its D-Bus name in under one second, and Phosh reported ready
in 1.60 seconds.

The active Wayland logind session remained attached to graphical `seat0` with
no VT. The lock screen, touch and passcode unlock worked. From a freshly
flashed image, GNOME Settings displayed the Wi-Fi secret prompt, accepted a
user-entered credential, connected successfully, and allowed automatic NTP
synchronization. No SSID, profile or credential is tracked.

The observed lock screen appeared around 50 seconds from boot. The difference
from the corrected v5 runtime boot occurred before `phosh-m0.service` and is
not attributed to Keyring or UPower. Dynamic battery tracking remains
unvalidated despite Phosh displaying 100%; `getty@tty1.service`, colored
clear-KMS rectangles, onscreen GPU presentation beyond the subsequently
validated Zink/Turnip/KGSL offscreen render, and modem/SIM remain open. See
`docs/validation/mobian-m1-repro-v6-hardware-validation-2026-09-05.md`.

## M1 REPRO v7 — VALIDATED ON HARDWARE / FRENCH OSK DEFAULT TO REVALIDATE

M1 REPRO v7 was built from commit `d054ba8`; its Android sparse userdata
SHA-256 is `3b514d386b486137d8c730a0c6f1e970f1aa10116720669f9b66d920902d1015`.
Flash and D-v43 boot passed. The lock screen, touch, unlock, USB SSH, GUI
Wi-Fi, GNOME Keyring Secret Service, UPower with `PrivateUsers=no`, the active
Wayland logind session on `seat0`, and network-triggered NTP synchronization
remained functional. The former Keyring and UPower timeout messages did not
recur.

The measured critical chain corrects an earlier analytical assumption: WLAN
bring-up was on the path to Phosh on this boot. The effective chain was
`lmi-wlan-on.service` -> `NetworkManager.service` -> `network.target` ->
`systemd-user-sessions.service` -> `user@1000.service` ->
`phosh-m0.service`. The eight-second `fs_ready` delay and bounded WLAN wait
therefore contributed directly. Clear-KMS completed on a separate branch at
about 5.4 seconds and was not critical. This milestone does not change any of
those dependencies.

Battery data was dynamically validated while physically unplugged: capacity
fell from 100% to 95%, battery and BMS sysfs values agreed, and UPower exposed
`discharging`, `on-battery=yes`, an energy rate and a time-to-empty estimate.
Raw downstream inconsistencies remain: `battery/status` still said `Charging`
and USB still reported present/online while unplugged. Reconnection, charging,
return to 100% and low-battery behavior are not yet tested.

The French OSK cause was also validated at runtime. Changing
`org.gnome.desktop.input-sources sources` from `[('xkb', 'us')]` to
`[('xkb', 'fr')]` changed Squeekboard immediately from QWERTY to AZERTY and
survived a complete reboot without reflashing userdata. The recipe now
provides this as a textual GSettings schema override and compiles it without a
user D-Bus session or a prebuilt dconf database. Delivery from a fresh rebuilt
image remains to be validated. Full evidence is in
`docs/validation/mobian-m1-repro-v7-hardware-validation-2026-09-05.md`.

## M1 REPRO v8 — AZERTY VALIDATED / XDG USER DIRS FIX TO REVALIDATE

The recipe-provided `[('xkb', 'fr')]` default reached Squeekboard on hardware;
the French layout loaded and AZERTY was functional. A distinct startup barrier
was then isolated: the Debian `xdg-user-dirs.desktop` entry ran in GNOME
Session's `Initialization` phase, while GLib's child watcher failed with
`waitid(..., pidfd=...) = EINVAL` on D-v43. Because process exit was not
observed, GNOME Session waited about 90 seconds before reporting that the
application had failed to register. Squeekboard started immediately after the
timeout.

The recipe now hides only that legacy autostart under systemd and preserves
`xdg-user-dirs-update` as a device-specific user oneshot before
`gnome-session-pre.target`. The global GNOME timeout, Phosh session definition,
Squeekboard, Keyring, UPower, networking and boot ordering are unchanged. The
new oneshot and removal of the 90-second barrier require validation from a
fresh image.

## M1 REPRO v9 — XDG USER DIRS FIX VALIDATED ON HARDWARE

M1 REPRO v9 was freshly built from commit `e7e63ba`; its Android sparse
userdata SHA-256 is
`17e5c0427358803beac9f2313caa008fd3303119c0020ebacc42a45a15f9b401`.
Userdata flash and D-v43 boot passed.

The device-specific `xdg-user-dirs-lmi.service` completed successfully with
exit status zero. All eight localized user directories were created under the
`mobian` home. The legacy `xdg-user-dirs.desktop` registration timeout was
absent, Squeekboard appeared immediately after unlock, loaded `Resource: fr`,
and provided the integrated French AZERTY layout on the fresh image.

This validates the targeted workaround without changing GNOME's global phase
timeout or removing `xdg-user-dirs-update`. The broader D-v43 incompatibility
where GLib child watching through `waitid(..., pidfd=...)` returns `EINVAL`
remains open for other short-lived processes. See
`docs/validation/mobian-m1-repro-v9-hardware-validation-2026-09-05.md`.

## M1 BLUETOOTH SLIM/PDR — VALIDATED AUTOMATICALLY ON HARDWARE

A bounded post-v9 runtime experiment validated the previously missing
Qualcomm process-domain path without changing the M1 image. Before the test,
the ADSP was not running, QRTR exposed no Service Registry Locator `64/1/1`,
NGD had never runtime-resumed, and no BTFM SLIM device existed. D-v43's
service-locator client otherwise waits `3000000` ms (3000 seconds) before its
late SSR fallback, so booting the ADSP first could not provide NGD with a
timely `appsngd1` / `avs/audio` domain resolution.

The stock Android `pd-mapper`, given a private read-only view of the existing
stock `firmware_mnt`, published `64/1/1`. It consumed the stock PDR maps,
including `adspua.jsn`, and resolved `avs/audio` to
`msm/adsp/audio_pd`, QMI instance 74. After exactly one ADSP boot, the ADSP
reached `ONLINE` with `crash_count=0`; QRTR exposed notifier `66/1/74` and
SLIM control service `769/1/0`; the audio domain notified UP; and NGD recorded
runtime activity. SLIM then created `btfmslim_slave` and
`btfmslim_slave_ifd`, with the QCA6390 slave bound to `btfmslim-driver`.
Phosh, touch, Wi-Fi and general device stability were unchanged after the
experiment.

M1 REPRO v11 subsequently validated the persistent implementation from a
freshly flashed image with no manual radio-domain intervention. The three
tracked units prepared the stock firmware links, kept the stock pd-mapper
running behind a private read-only bind, passed the bounded locator/PDR
barrier, and performed exactly one guarded ADSP boot. ADSP reached `ONLINE`
with `crash_count=0`; all three QRTR services and both BTFM devices appeared;
and the QCA6390 slave bound automatically. The integrated `codex-lmi` public
diagnostic key also provided root SSH with the expected permissions and no
private key was installed by the recipe. No proprietary binary or map is
stored in Git.

Phosh, unlock, French OSK, Wi-Fi and general stability remained functional.
`getty@tty1.service` remains the sole known failed unit and is non-blocking on
the `CONFIG_VT=n` kernel. `/sys/class/bluetooth` is still empty, so HCI creation
is the next distinct problem. Occasional USB/RNDIS recovery by cable reconnect
also remains an open observation. See
`docs/validation/mobian-m1-bluetooth-slim-pdr-runtime-validation-2026-09-05.md`.
See also `docs/validation/mobian-m1-repro-v11-hardware-validation-2026-09-05.md` for the
fresh-image evidence.

## M1 BLUETOOTH HCI/HASTINGS — ACTIVE HCI VALIDATED

The layer following the validated BTFM SLIM binding has now been identified
statically. On `lmi`, Bluetooth HCI uses QUPv3 SE6 at `0x998000` through the
`qcom,msm-geni-serial-hs` device `/dev/ttyHS0`; there is no Bluetooth serdev
child in the Xiaomi DT. The stock QTI HAL opens that UART directly, uses the
separate `/dev/btpower` interface and identifies the controller as QCA6390
`hastings`, revision `HASTINGS_VER_2_0`.

D-v43's `btfmslim-driver` supplies only the separate SLIM audio/FM path and is
not expected to register an HCI controller. HCI uses the GENI UART and N_HCI
line discipline. The V2 micro-backport now adds the QCA6390 type, Hastings
firmware selection, protocol adaptations and a NULL-safe non-serdev path. It
enables HCI UART, H4 and QCA while keeping `SERIAL_DEV_BUS=n` and controller
power external to `hci_qca`.

The first rebuilt candidates exposed an unrelated historical downstream VFS
defect: legacy block mounts lost `fc->source` and failed with `ENOENT` before
the filesystem driver. Those failures are not Bluetooth-discriminating. The
previously hardware-validated `do_new_mount()` safety net was restored, after
which HCI UART plus H4, generic QCA without the lmi selector, and the complete
QCA6390 V2 configuration each RAM-booted through rootfs and userspace. The
complete candidate behaved normally on hardware, establishing static
integration boot-safety.

The controlled Phase A attach has now also passed. Userspace opened
`/dev/ttyHS0` at 115200 with RTS/CTS, selected `N_HCI=15`, flags `0x2` and
`HCI_UART_QCA=8`, and obtained `hci0`. Automatic `qca_setup()` selected and
successfully downloaded the stock `qca/htbtfw20.tlv` and `qca/htnv20.bin`,
then completed its final HCI Reset. Cleanup restored N_TTY and termios,
removed `hci0` and left the UART, Phosh, RNDIS and Wi-Fi stable.

The reported controller value `0x02000200` is the driver's composite
`get_soc_ver()`, not the raw Hastings `soc_id` expectation `0x400a0200`:
the 32-bit calculation combines the shifted low 16 bits of `soc_id` with
`rome_ver=0x0200`. It yields `rom_ver=0x20`, directly selecting the correct
Hastings 2.0 files; this is not an endian issue or fallback.

Levels A (boot-safety), B (controlled N_HCI attach), C (version, PATCH, NVM
and final Reset) and controlled HCI activation are therefore PASS. Phase B
brought `hci0` UP and bound a raw HCI socket. After three seconds idle, one
explicit Read Local Version command (`0x1001`) returned status `0x00` with HCI
and LMP version `0x0b`, Qualcomm manufacturer `0x001d` and LMP subversion
`0x27ec`. `CMD_TX` and `EVT_RX` each increased by exactly one, proving a real
bidirectional controller exchange rather than a cached kernel query.

No IBS debugfs counters were available. Successful traffic after an idle
period longer than the two-second IBS timeout supports only an indirect
`IBS_FUNCTIONAL=INFERRED` result, not direct sleep/wake proof. The observed
Bluetooth address `[REDACTED-DEVICE-MAC]` has now been traced through the stock Android
provisioning path. The stock `/vendor/bin/nv_mac` opens Xiaomi's proprietary
QMI service `0xffe4`, sends message `0x0002` with Bluetooth NV operation
`0x01bf`, receives the six-byte address payload and writes
`/data/vendor/mac_addr/bt.mac`. `init.mi.btmac.sh` then converts that binary
value and sets `persist.vendor.service.bdroid.bdaddr`, which is consumed by
the QTI Bluetooth HAL. Static decoding also identified WLAN operation
`0x1246`. The tested `htnv20.bin` contains the same observed address in its BD_ADDR
field. Separately, static analysis establishes the stock Android QMI
provisioning mechanism, but because no QMI request was executed it does not
yet prove what operation `0x01bf` returns on this individual handset. `HCIDEVDOWN` and attach rollback restored N_TTY and
termios, freed the UART and removed `hci0` without affecting Phosh, RNDIS or
Wi-Fi. BlueZ, scan, pairing and real Bluetooth connections remain untested.

One attempted re-attach without resetting the already initialized controller
timed out during PATCH. A controlled `bt_power` OFF/ON cycle disabled and
re-enabled reset, SW_CTRL and all five QCA6390 rails; the subsequent continuous
setup and Phase B passed. This establishes a power-cycle prerequisite for a
fresh repeated bring-up, not a protocol regression. A transient
`Frame reassembly failed (-84)` during the successful retry did not prevent
version, PATCH, NVM, Reset, HCI activation or later traffic.

See `docs/validation/mobian-m1-qca6390-hastings-hci-design-2026-09-05.md` and
`docs/validation/mobian-m1-qca6390-v2-boot-safety-validation-2026-09-06.md`. The
stock Android BD_ADDR provisioning mechanism is now statically established.
The next Bluetooth milestone is BlueZ integration followed by controlled scan
and pairing validation.

## M1 EXTERNAL MODEM SDX55 — NOMINAL ESOC/MISSION-MODE PATH VALIDATED

DV121 reached the Qualcomm Sahara loader environment on the external SDX55M.
The validated runtime DT/ESOC identity is `qcom,ext-sdx55m`, `SDX55M`, PCIe,
link information `0306_02.01.00`; `/dev/esoc-0` and `/dev/subsys_esoc0` are
present. The userspace request engine must register before opening the SSR
subsystem device because that open remains blocked in `mdm_subsys_powerup()`
during boot. DV119 implements the required split: its main thread waits for
ESOC requests while a second thread opens `/dev/subsys_esoc0`. The validated
ARM64 helper SHA256 is
`966a1810f7e43fc398e10d91fd7f3c5db25eb9d6485c3ecf67a09cbfec852bbf`.

The Xiaomi
`lmi_global_images_V14.0.1.0.SJKMIXM_20230317.0000.00_12.0_global` ROM stores
the SDX55 firmware in the FAT16 `images/NON-HLOS.bin` container under
`image/sdx55m`. Eighteen files were extracted for analysis. The MHI driver
maps PCI device `0x0306` to `sdx55m/sbl1.mbn`; the extracted SBL1 is 548056
bytes with SHA256
`0fd2fdaf19831c8ff482ca77ca236ee282101c9bdf5ab7b46dc4e24a484e84dc`.
It was exposed as `/lib/firmware/sdx55m/sbl1.mbn` and revalidated after the
current RAM boot. The earlier `Error loading fw, ret:-2` is therefore no
longer the active blocker.

The historical delayed `ESOC_RUN_STATE` experiment exposed an ESOC state race:
a late run notification overwrote an already recorded `CRASH`, causing the
following forced SSR shutdown to skip its crash teardown and leaving the SSR
worker blocked in a second `mdm_subsys_powerup()`. DV166 captured the sole
`ssr_wq` worker in that exact stack. The B1 kernel correction preserves
`CRASH` and `PEER_CRASH` on a late run notification while still completing
`pon_done` and `ssr_ready`.

B1 was reviewed adversarially, built, packaged with unchanged ramdisk/DTB and
RAM-booted. Mobian, Phoc, Phosh, USB and Wi-Fi remained functional. DV179 then
reached `ESOC_REQ_IMG`, PCI `17cb:0306`, MHI BL and Sahara with zero crashes.
A one-shot no-reset validation client completed the 17-entry Sahara transfer;
QMI0/QMI1, RMNET_CTL, DIAG, IP_HW0, `rmnet_mhi0` and the SSCTL service appeared.
DV186 sent one nominal `ESOC_BOOT_DONE`: the power-up thread returned, the
subsystem became `ONLINE`, mission mode remained present and `crash_count`
stayed zero without a new kernel error.

This validates the complete nominal SDX55 ESOC path under B1, not cellular
service, voice, SMS or data. The precise `CRASH -> late RUN_STATE -> SSR` race
has not been reproduced on B1 hardware, so it is not claimed as materially
closed. See `docs/validation/mobian-m1-sdx55-dv121-sahara-milestone-2026-09-06.md` and
`docs/validation/mobian-m1-sdx55-esoc-b1-validation-2026-09-06.md`.

DV191 through DV207 then audited the post-crash `remotefs_sahara` path and the
runtime EFS synchronization design entirely offline. The exact Xiaomi
`/vendor/bin/ks` was recovered and shown to write received EFS regions directly
to persistent `mdm1m9kefs*` destinations with the historical Qualcomm
invocation, so that invocation is not treated as read-only and was not
executed. Static tracing also rejected host-side close as a demonstrated
Sahara termination mechanism.

DV207 therefore extends the validated DV196 in-memory consume-all/write-none
model with the normal Sahara terminal sequence
`TRANSFER_COMPLETE -> RESET -> RESET_RESP -> PROTOCOL_COMPLETE`. RESET cannot
be constructed before exact coverage of all declared regions, RESET_RESP is
strictly validated, and the extension does not add filesystem, device or MHI
transport capability. Both 32-bit and 64-bit synthetic paths pass 290 tests
with zero failures in normal and ASan/UBSan builds. This is an offline protocol
model only: no real EFS MHI probe is authorized and `REAL_PROBE=NOT_SAFE`.
See
`docs/validation/mobian-m1-sdx55-dv207-remotefs-reset-offline-validation-2026-09-07.md`.

## Repository policy

Generated `.img`, `.ext4`, Android sparse images, root filesystems, private
keys, caches and other build artifacts are intentionally excluded from Git.

## Battery, speaker and torch updates — 2026-10-03

The full Debian ARM64 UPower `1.90.9-1+lmi1` package and phone-local activation
are installed. Seven explicit ARM64 integration tests passed; the installed
service tracked a real unplug/replug cycle correctly over 90 observations.
Capacity accuracy and autonomy remain unresolved. Automatic battery suspend
is locally enabled; frequent msoc-delta wakes remain under investigation. A bounded follow-up
returned to deep suspend about six seconds after one gauge wake, but still
measured about 106 mA over a ten-minute interval with 98.8% suspend occupancy.
Autonomy remains unresolved; this diagnostic is not permanently enabled.
See the [guarded wake trial](../validation/lmi-gauge-resuspend-trial-2026-10-06.md).

A subsequent October 6 unplugged history interval lost 42 percentage points
(97% to 55%) in 10.97 hours, approximately 3.83 points/hour, despite about
95.9% deep-suspend occupancy. No reboot occurred; autonomy remains unresolved.
See the [October 6 observation](../validation/lmi-battery-overnight-2026-10-06.md).

The October 7 night on the temporary touch-notifier candidate again showed
substantial discharge: 99% to 66% over 8 h 51 min, approximately 3.73 points/hour,
with 96.74% suspend occupancy over the journal-covered interval. No reboot or
UPower restart occurred. A normal Wi-Fi shutdown check cleared the five
CNSS/PCIe power votes, but its suspend-current comparison was invalidated by
an early gauge wake. Autonomy remains unresolved; see the
[power diagnostic record](../../kernel/diagnostics/power/README.md#wi-fi-shutdown-isolation-and-october-7-overnight-observation).

A subsequent nearby three-minute comparison measured approximately 92.1 mA
with normal radio shutdown and 94.8 mA with Wi-Fi enabled, both above 99.6%
suspend occupancy. This single pair does not establish a stable Wi-Fi penalty;
stopping the radio did not remove the residual consumption. Both collectors
and alarms are cleaned up; the enabled-radio trace is complete.
A further three-minute trial exposed APSS/ADSP master sleep counters: they
report 99.65% and 99.95% asleep respectively while the gauge still measures
approximately 93.7 mA. This narrows the investigation but neither measures
all physical loads nor validates an autonomy fix; the complete result is in
the power diagnostic record.
A subsequent RPMh trace confirms final APSS sleep votes of zero for CX/MX/XO
and three inspected bus resources, while the gauge still reports about 94.9 mA.
These software requests do not establish all physical rail currents; the
residual discharge remains unresolved. The trial and alarm are cleaned up.






Clear speaker music was operator-confirmed through an installed PipeWire
route using the S32_LE frontend and S24_LE backend on the temporary GPIO
diagnostic boot. ALSA controls restore on close. The graphical torch app's
Allumer and Éteindre buttons were operator-confirmed. Camera capture remains
blocked. These are live-phone customizations, not newly locked golden images.
See the [validation record](../validation/lmi-battery-audio-torch-2026-10-03.md).

## Additional operator confirmations — 2026-10-03

MP3/MP4 playback, hardware volume buttons and Chinese filenames in Files
are confirmed. Noto CJK fonts were installed and Files relaunched. A controlled
RTC deep-suspend test succeeded, but the gauge-derived current remained about
102 mA versus 218 mA awake idle; acceptable long-term autonomy is still not
established. See the latest battery/audio/torch validation record.

## Next-build language support — 2026-10-03

The next M1 recipe includes broad Noto core/CJK/emoji font coverage and all
Debian locales by default. Initial interface locale and XKB layout are build
parameters; document scripts do not depend on the selected interface language.
This is prepared recipe work, not a new image or phone deployment. Input
methods and runtime language switching remain separate validation work.

## CPU idle improvement — installed 2026-10-03

A legacy `lpm_levels.sleep_disabled=1` boot parameter blocks deeper CPU idle
between activities. A controlled test reported awake-idle current dropping
from 208.4 to 100.8 mA with 831 C1 entries after a runtime opt-in. Touch,
music, volume and USB remained functional. The phone-local opt-in service is
installed and enabled; stopping it restores the original parameter. Boot
images/cmdline and the historical golden are unchanged. Reboot and long-run
validation remain pending. Deep-suspend current still reports about 97 mA;
acceptable autonomy and fuel-gauge accuracy are not yet established. See
`userspace/power/README.md` and the 2026-10-03 validation record.

A subsequent private tracefs collection recorded 121.761 seconds of deep
suspend without new failures, with APSS/ADSP asleep almost throughout
and approximately 96.2 mA reported consumption. Static DDR counters
do not identify a memory-power fault; the residual consumer remains
unresolved. The trace instance was removed after reconnect. A subsequent
unplugged inspection confirmed USB runtime suspend and its power domains
disabled; an always-on boost/shared GPIO is a review lead, not a proven cause.


## Application checklist and Chatty incident — 2026-10-03

An inventory of 21 visible applications and one-at-a-time functional checks
is recorded in `docs/validation/lmi-app-checklist-2026-10-03.md`. Chatty
0.8.7-2 exhausted memory during camera enumeration through GStreamer and
libpurple. An isolated test excluding two video plugins stayed active at
approximately 108 MiB. The phone-local desktop/D-Bus helper was then installed
with an isolated registry and a requested 384 MiB systemd-user memory limit;
user memory delegation was checked after restart at 384 MiB and zero swap.
The operator subsequently confirmed normal opening, menu access and relaunch;
shortcut-window sizing remains defective. SMS/MMS remain unvalidated. SMS is not validated and no modem was detected. The new helper
is not automatically installed by the generic image recipe.

The restart interrupted the six-hour battery observer. CPU-idle and UPower
were active after restart, but no ALSA card was detected; previous music
confirmations apply to the temporary diagnostic boot, not this restart.


## Application follow-up — 2026-10-03

The operator's application and menu defects are preserved in the app checklist.
Koko's missing Qt/QML dependencies were installed on the test phone and made
explicit in the application recipe. Photos now has operator-confirmed image
opening, working Back navigation and no unsolicited keyboard. A bounded
standard-thumbnail-cache helper restores the gallery preview in a remote
screenshot; the lmi launcher uses the tested Zink runtime when available.
The bottom folder header, truncated labels and broader gallery functions remain
open. Helpers and dependencies are recorded in the recipe.
This is a live userspace repair, not a newly built or hardware-validated image.
No automatic rotation sensor or usable GPS was established in this follow-up.
See the [application checklist](../validation/lmi-app-checklist-2026-10-03.md).


The text editor's off-screen GTK Save dialog was reproduced. GNOME file-chooser
portal routing and a per-app launcher now give an accessible Save button.
Remote tests passed create/save, reopen, Save As, edit/save and normal close;
the operator also confirmed the Save As dialog usable by touch. Recipe and
builder staging include these userspace fixes; no new image was built.


## Calendar and Contacts functional follow-up — 2026-10-03

Calendar passed month navigation, Today, explicitly authorized local test-event
creation, reopening, removal and a normal close with retained exit status 0.
No test event remains; remote synchronization and reminders are unvalidated.
Contacts passed local dummy-contact creation, persistence and search, but
initial deletion crashed with SIGSEGV. An app-only Cairo launcher then passed
two deletion/normal-close cycles. This workaround is installed locally and
included in the next-build application recipe/staging; no new image was built.
No personal contacts were modified. Broader contact operations remain untested.
Console’s incomplete pidfd/waitid kernel interface remains open, with no
persistent syscall filter or global library replacement installed.
See the [application checklist](../validation/lmi-app-checklist-2026-10-03.md).


## Settings functional follow-up — 2026-10-03

Settings passed navigation to its overview, Mouse and Touchpad, Keyboard and
System pages, plus two normal closes with retained exit status 0. No system
settings were changed. Reopening still restores the last panel even after
closing from the overview; overview-on-launch remains unresolved. The mouse
test dialog has no visible close button on this display; Escape closes it,
but touch-only dismissal remains unvalidated. No renderer workaround or
launcher modification was installed. Temporary test services and USB-only
screen inhibition were stopped. See the
[application checklist](../validation/lmi-app-checklist-2026-10-03.md).


## Window close controls and mail/call UI — 2026-10-03

The live window button layout omitted Close (`appmenu:`). It is now
`appmenu:close`; Calls' VoIP dialog and the Calls/Settings main windows passed
touch-simulated close checks. A Phosh schema default and builder validation
are prepared for the next image, without running a build. Custom-header
dialogs can still omit Close; Settings' mouse-test dialog remains open work.
Geary passed empty-account startup, add-form cancellation, reopening and
normal closure; no mail account or message was created. Calls has no usable
modem/VoIP account in its UI; no actual call was attempted. See the
[application checklist](../validation/lmi-app-checklist-2026-10-03.md).


## Editor shortcut dialog recheck — 2026-10-04

The restored Close layout persists in the live session, but Text Editor's
shortcut dialog is still wider than the display and lacks a touch-accessible
dialog close control. Hiding the keyboard does not fix its width. App-local
Phoc scale-to-fit did not visibly help and was returned to false; global
scaling and embedded resources were not changed. Escape exits the dialog,
then the main window's Close button gives retained exit status 0. No test
document was changed. Other apps' shortcut dialogs remain unverified after
the layout change. See the
[application checklist](../validation/lmi-app-checklist-2026-10-03.md).


## Chatty shortcut-dialog adjustment — 2026-10-04

Phoc's oversized-window adjustment is now enabled in the live session and
prepared as a next-build schema default. Chatty's shortcut dialog fits and
passed touch-simulated close/reopen checks with the restored Close layout.
No message/account was created. Text Editor's shortcut dialog shrinks but
still clips horizontally; its touch-only exit remains unvalidated. Both
test applications closed normally and test units were stopped. Transient
black line artifacts after the preference toggle were absent on the next
Chatty capture, without establishing GPU stability. See the
[application checklist](../validation/lmi-app-checklist-2026-10-03.md).

## Root SSH build policy (2026-10-04)

The Phosh image recipe no longer embeds the workstation diagnostic public key.
It clears inherited root authorizations in the derived image by default; an
external public key can be explicitly selected with `M1_SSH_PUBLIC_KEY_FILE`.
Private keys and multi-key inputs are rejected. Existing phone access and input
rootfs trees are unchanged. Isolated tests cover defaults, explicit access and
invalid inputs; no complete image build or deployment was performed.

## Recorder and missing-card audio startup — 2026-10-04

KRecorder 25.04.0-2 opened, navigated to Configuration and returned to its
recording list. The Audio Input chooser was empty. Two simulated-touch
main-window closes, including a reopening after the service correction,
returned Result=success, ExecMainCode=1, ExecMainStatus=0. No recording was
started, no existing recording was changed and temporary test units stopped.
Configuration labels were French in the captures; full translation untested.
The on-screen keyboard appeared in Configuration without a text-entry action;
that usability defect remains open. Codec, container and recording operations
have not been validated.

This runtime had no ALSA card: /proc/asound/cards reported no soundcards and
/dev/snd contained only timer. The installed speaker adapter failed to open
lmi_speaker; PipeWire terminated with exit status 234 and WirePlumber stopped.
This does not overturn earlier clear-speaker validation on the separate
temporary diagnostic boot, nor identify the currently loaded boot image by
hash. The displayed kernel release alone cannot distinguish those images.

The adapter now declares flags = [ nofail ], as specified by the
[PipeWire configuration documentation](https://docs.pipewire.org/page_man_pipewire_conf_5.html).
After installation of this single configuration change and an audio-service
restart, PipeWire 1.4.2, pipewire-pulse and WirePlumber stayed active through
the recorder reopening/close test. wpctl showed only Dummy Output and no
audio source. The correction restores server availability when the card is
absent; it does not restore physical speaker or microphone operation. The
missing-card warning remains expected. Physical-card playback with the new
flag awaits the diagnostic boot retest. No kernel/image build or flash ran.

## Diagnostic-boot speaker retest — 2026-10-04

After a temporary Fastboot load of the preserved diagnostic boot, the ALSA
card returned and the revised nonfatal speaker adapter loaded. The operator
confirmed ten seconds of clear music without distortion. Standard ALSA
capture produced eight seconds of data with all tested controls restored;
recognizable microphone sound and application integration remain unvalidated.
No kernel was installed durably and no microphone source was installed.
See the [application checklist](../validation/lmi-app-checklist-2026-10-03.md).

## Microphone and Recorder result — 2026-10-04

Native eight-second capture was operator-recognized after amplified playback.
An opt-in PipeWire microphone source and numeric KRecorder WAV/PCM settings
then produced two complete 8.96-second recordings. The final saved trial
survived normal close/relaunch and displayed `0:08`. After replaying it,
the operator confirmed that the application-produced recording was good. Both hardware PCMs
closed at idle. This supersedes earlier no-source/microphone-unvalidated
observations on this diagnostic boot only. Full UCM2, headset/earpiece and
durable boot deployment remain pending. See the
[audio integration record](../../userspace/audio/README.md#microphone-and-recorder-capture--2026-10-04).

## Timer feedback and offline clock correction — 2026-10-04

A real five-second Clocks timer now gives an operator-confirmed audible alert
after adding Feedback and the PulseAudio backend to the app recipe and phone.
The timer test was removed; no rebuilt image is claimed. The phone clock was
aligned from Windows and saved using the existing seed service, because NTP
had no Internet route. Wi-Fi and battery settings were unchanged. See the
[validation and remaining limits](../validation/lmi-clock-feedback-2026-10-04.md).

## Files and Calculator functional checks — 2026-10-04

Simulated touch validated Files Copy/Rename/Trash on disposable fixtures and
Calculator arithmetic, angle conversion and Preferences closure. Both apps
closed normally; file/trash fixtures were removed after exact scoped checks.
Files keyboard dismissal and Calculator's clipped Shortcuts dialog remain
unresolved. Resetting Settings' last-panel preference did not provide the
requested overview; the original value was restored and no fix installed.
See the [checklist](../validation/lmi-app-checklist-2026-10-03.md#files-operations-calculator-menus-and-settings-trial--2026-10-04).

## Papers search — 2026-10-04

Positive/negative PDF text search and touch navigation to the second result
passed on the synthetic fixture, with keyboard dismissal and normal exit.
A Pixman invalid-rectangle warning remains recorded; no crash was observed.
See the [checklist](../validation/lmi-app-checklist-2026-10-03.md#papers-search--2026-10-04).

Papers Save As also created an identical test PDF through the mobile chooser;
the Save control remained visible above OSK. Keyboard dismissal and normal
closure passed, and only the disposable copy was removed after comparison.

## Keyboard home-bar gesture — 2026-10-04

A two-second simulated hold centered on the bottom white bar toggled OSK in
Text Editor and Files, with DBus visibility checks. No preference or launcher
was changed. The Files rename replay hid OSK automatically in this attempt,
so the earlier persistent-keyboard symptom was not reproduced. Operator
gesture confirmation and other dialogs remain pending. See the
[checklist](../validation/lmi-app-checklist-2026-10-03.md#keyboard-home-bar-gesture--2026-10-04).

## Files touch multiselection — 2026-10-04

The deletion report was clarified as difficulty selecting multiple files.
Terminal OSK's latched Ctrl plus touches selected three folders; Ctrl was then released and the grouped selection reduced to one item. No data was deleted and grouped Trash remains
untested. The keyboard-assisted workaround is recorded in the
[checklist](../validation/lmi-app-checklist-2026-10-03.md#files-touch-multiselection--2026-10-04).

## Portfolio mobile selection — 2026-10-04

The official Debian `portfolio-filemanager` package is installed on the test
phone and added alongside Nautilus to the next app recipe. Long press followed
by taps selects multiple disposable files without OSK. Grouped permanent
removal preserved the unselected third fixture; Trash and operator usability
confirmation are not inferred from that result. The confirmation's poor icon
and truncated label remain recorded. No new image or default-handler change.
See the [checklist](../validation/lmi-app-checklist-2026-10-03.md#portfolio-native-touch-multiselection--2026-10-04).

The operator subsequently rejected Portfolio as providing no useful
improvement. Its next-build package addition was withdrawn; the trial remains
historical evidence, not a completed fix. Existing Files touch selection is
still open. After clarification that a second app was unnecessary, Portfolio
was also uninstalled without autoremove; no user files were removed.

## Core app priority and camera blocker — 2026-10-04

The operator confirmed Files as functional. Additional features are last,
after basic operation, essential menus and translation; no second file manager
is required. Megapixels remains nonfunctional: a bounded launch exited with
status 1 due to the absent lmi-compatible configuration. Targeted source
review supports the downstream/private-interface blocker, without establishing
a usable capture backend. No camera configuration or image was changed.
See the [functional recheck](../validation/lmi-app-checklist-2026-10-03.md#functional-priority-and-camera-recheck--2026-10-04).

The camera follow-up found OEM HAL objects and a usable Android loader already
present, but missing Binder nodes/properties and a broken HIDL-manager target.
A read-only probe is now preserved; no Android service or capture was started.
The alternate CAMSS/OV13B10 source is distinct from the running kernel and is
not a validated camera. See the [backend prerequisites](../../userspace/camera/README.md#oem-backend-feasibility--2026-10-04).

The isolated HIDL follow-up located the manager in system_ext and obtained
private Binder registration with a test-only synthetic context. No camera
device/provider was exposed. High CPU and missing properties remain blockers;
all runtime processes, mounts and loop mappings were removed. Details and
source-only diagnostics are in the [camera milestone](../../userspace/camera/README.md#isolated-hidl-registration-milestone--2026-10-04).


Camera follow-up (2026-10-04): the private HIDL startup spin was traced to
waiting for an unavailable Android readiness property. A local diagnostic
token removed the spin. Real client IPC still fails: this non-SELinux kernel
cannot supply the requested transaction security context, and omitting the
request triggers Android 16's missing-caller-context assertion. All test
processes/mounts were removed; no camera provider or physical capture was
started. Megapixels remains nonfunctional. See the [measured results and
remaining runtime prerequisite](../../userspace/camera/README.md#readiness-spin-resolved-client-ipc-blocked--2026-10-04).


Camera OEM follow-up (2026-10-04): the private runtime can now query HIDL
interfaces and load CamX with the real qcom/kona properties. Correcting the
private ICP firmware lookup produced a kernel-confirmed firmware download;
several real candidate EEPROM probes succeeded. The direct camera module
now returns eight OEM IDs when the unavailable NCS/IMU service is disabled privately. These are backend
milestones, not a working photo application. See the [sensor progress and
capture gates](../../userspace/camera/README.md#oem-module-and-sensor-probe-progress--2026-10-04).


Rear camera diagnostic (2026-10-04): a real 320 x 240 JPEG request returned
an OK buffer and a decodable JPEG via the verified Qualcomm allocation
bridge. The first image was nearly black; scene/exposure remains unvalidated.
This does not make Megapixels functional. Sources and limits are documented
in [first rear JPEG diagnostic](../../userspace/camera/README.md#first-rear-jpeg-diagnostic--2026-10-04).


Rear camera update (2026-10-05): the isolated PREVIEW backend now captures
1280 x 720 rear images with adaptive automatic exposure. The verified CVP/synx
interfaces and temporary host-visible OEM firmware segments resolve the prior
configuration failure; three fifteen-frame runs completed, including the final
consolidated sources. A privately inspected image shows the scene correctly.
The helper cleans up its links/runtime and is not installed persistently.
Live preview and Megapixels integration remain pending; video, focus quality and generic-image support are not validated.
See [automatic rear preview capture](../../userspace/camera/README.md#automatic-rear-preview-capture--2026-10-05).

An opt-in GTK rear snapshot app is now installed on this exact diagnostic boot.
Two automated end-to-end app runs saved user-owned 1280 x 720 PNGs in Images/
Camera. The app runs unprivileged; a fixed demand-started backend service has
bounded execution and a narrowly scoped local-user rule. No generic-image or
Megapixels support is claimed. Operator capture and upright portrait display
are confirmed; opening the saved photo in Photos remains pending. The HAL-based
rotation saves 720 x 1280 portrait pixels. Explicit private-manager shutdown
reduced one full UI trial from 14.610 to 10.048 seconds. Replacing fixed
startup/result pauses then yielded two successful trials at 8.625 and 8.623
seconds, including smoke-mode startup/exit delays. Per-shot initialization
and live preview remain unresolved. See [application and validation scope](../../userspace/camera/README.md#opt-in-rear-snapshot-application--2026-10-05).


A bounded rear live-preview prototype now displays successive rotated frames
without reopening the sensor. A 45-frame diagnostic returned eleven images
about 0.725 seconds apart after warmup; a separate 120-frame preview published
36 frames and stopped automatically. The normal photo button saves the displayed
frame directly; operator save-responsiveness confirmation remains pending.
The fixed early-stop action now leaves no runtime directory or CVP links.
The operator reports that preview is too slow for normal use; no PipeWire
video source is currently exposed for an alternative standard frontend. Preview is slow and limited to about 30 seconds per launch.
See [bounded rear live preview](../../userspace/camera/README.md#bounded-rear-live-preview--2026-10-05).


Preview follow-up (2026-10-05): automatic preview now works on fresh launch and
reactivation of an existing window after completion. Publishing every live
frame yielded 106 displayed frames with a mean 0.242-second interval, versus
about 0.725 seconds with every-third-frame sampling. Instrumentation measured
about 235–242 ms request/result wait and 14 ms conversion/write for published
frames. The client still submits requests serially; queued-buffer capture is
not yet validated. Operator confirmation of the visual improvement is pending.
See [cadence measurement](../../userspace/camera/README.md#preview-cadence-measurement-and-automatic-reactivation--2026-10-05).


Queued-preview follow-up (2026-10-05): automatic startup and noticeably smoother
preview are operator-confirmed. Three genuine buffers now keep requests in
flight instead of waiting serially. A rear diagnostic yielded 106 images at a
mean 0.0444-second interval; the final real-UI run displayed 423 images at a mean
0.0581-second interval (about 17 fps). Queueing stops after 25 seconds and drains
outstanding requests, under the existing outer timeout. Normal and early-stop
cleanup passed; the original snapshot path still succeeds. No kernel change.
Full-resolution stills, autofocus, video and standard-app integration remain
pending. See [queued rear preview](../../userspace/camera/README.md#queued-three-buffer-rear-preview--2026-10-05).


Foreground-preview follow-up (2026-10-05): the normal app no longer requires a
restart every 25 seconds. Preview runs while its GTK window is active, pauses
in the background and resumes automatically on return; the operator confirmed
the return path. A real session ran 137.8 seconds and published 3,034 images.
A fresh PID/start-time/UID-checked lease and watchdog replace the normal session
cap; the diagnostics retain their bounds. Background and GUI-exit cleanup tests
passed after extending the firmware wrapper teardown wait. No kernel change.
See [foreground continuous preview](../../userspace/camera/README.md#foreground-owned-continuous-preview--2026-10-05).


### Existing camera application trial — 2026-10-05

Debian Lomiri Camera 4.0.8+dfsg-5 was installed experimentally. Its Wayland/OpenGL
interface launches, but the operator and a screenshot confirmed a black
viewfinder. No photo/video was validated; the Android camera bridge is not
installed. This is not a replacement for the validated rear HAL3 preview and is
not added to the image recipe. See `docs/validation/lomiri-camera-app-installation-test-2026-10-05.md`
(repository-root-relative) for installation findings and limitations.


### Current camera status — 2026-10-06

Snapshot rear preview is experimental. The operator found the native PipeWire
preview fluid but mirrored and delayed; its measured publication rate was about
18.8 fps. The preview target is 25 real images/s. A rear-identity and fresh-file
polling correction is prepared and passes synthetic tests at about 25 fps;
rear orientation is now operator-confirmed, while visible preview delay is now confirmed. A one-minute follow-up measured
16.68 fps upstream and 16.90 fps at the native producer; sensor profiling found 60 ms exposure with a 12–30 fps range. The supported
fixed-30 fps trial reduced sensor-to-RGB age to 86.5 ms; the operator confirmed
reduced delay and adequate brightness. Preview publication reached only 19.34 fps
and production integration remains pending. Real recording has
unresolved preservation and quality defects. Megapixels was removed and the
lmi-camera prototype remains provisional. A private NEON trial reduced conversion
to 9.3 ms, but delivered only 18.81 fps. The operator estimates remaining visible
delay at 0.2-0.5 seconds; a preview queue experiment has no demonstrated gain.
A later two-buffer/10 ms polling trial reached 21.62 fps but was reported
saccadic by the operator; it remains rejected for production integration.
No camera test or recording is active.
See the [camera implementation status](../../userspace/camera/README.md) and
[complete validation record](../validation/snapshot-pipewire-rear-preview-2026-10-05.md)
for distinct operator, hardware and synthetic results.


### Battery diagnostic follow-up - 2026-10-06

The active 416-byte J11 battery-profile payload matches OEM-style DTBO entry 7
exactly. This does not independently validate battery health or gauge calibration.
A separate [power debugfs candidate](../../kernel/diagnostics/power/README.md) is prepared for inspecting
clock/regulator summaries, retaining the reset-GPIO audio correction. External-input preflight and native Kconfig checks pass. It includes the
Qualcomm idle statistics required by this source when debugfs is enabled, with
optional Bluetooth/block debug interfaces disabled. The operator subsequently built the separate diagnostic boot successfully
(54,652,928 bytes; identity in the linked record). Temporary hardware startup is confirmed by the matching live IKCONFIG hash
and readable clock/regulator debugfs interfaces. USB SSH and existing CPU-idle
service work. Short suspend/current results are documented below; no hardware
power policy or durable boot was changed.
Residual deep-suspend consumption remains unresolved.


The first debugfs-boot trial confirms approximately 181 seconds in deep suspend
through both clock accounting and Qualcomm suspend statistics. Gauge-derived
consumption remains approximately 96.4 mA; there is no demonstrated autonomy
improvement. USB power votes drop after unplugging, while PCIe/shared rails
require interpretation rather than forced shutdown. The transient trial ended,
its RTC alarm was cleared, and charging resumed after reconnection.


The revised trace trial confirms 181.26 seconds of sleep with a complete,
loss-free trace and approximately 95.63 mA gauge-derived consumption. Display,
UFS and PCIe clock-disable transitions precede machine suspend, with no nonzero
device-PM callback result. This narrows the diagnosis but provides no autonomy
fix. The transient collector and RTC alarm are cleaned up; see the linked power
diagnostic record for measurement limits and the invalidated earlier trial.


A separate touch shutdown-notification candidate has now been manually built
and temporarily started. Its live build banner and IKCONFIG match the verified
candidate; USB SSH and charging work. The first unplugged trial now shows
the expected touch suspend/resume path and 181 seconds of deep sleep. The operator
confirmed normal touch response after wake; an autonomy improvement is not
established. This covers one suspend/resume cycle only. The power diagnostic record gives its exact
identity and experimental scope; this is not a production boot update.


### RPMh observer diagnostic follow-up ? 2026-10-07

The operator manually built and temporarily booted the read-only RPMh observer
variant (54,652,928 bytes; SHA-256
`a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50`).
All 47 provider attributes, USB SSH and charging were checked. The inner builder
completed successfully despite the outer wrapper's inability to read its
root-owned status directory. A roughly 10 h 20 min uncontrolled unplugged period
still lost 37 capacity points. Kernel logs show approximately 96.54% deep sleep
between the first recorded suspension and reconnection, predominantly interrupted
by battery-gauge interrupts. There is no demonstrated autonomy improvement and
no production boot replacement. The bounded observer/trace comparisons subsequently completed, as recorded
below. See the
[power diagnostic record](../../kernel/diagnostics/power/README.md) for identity,
measurement boundaries and wrapper reporting details.


The first bounded aggregate-observer trial completed with all 47 snapshots
readable and a loss-free trace. It measured approximately 94.787 mA by the gauge
with 99.617% suspend occupancy; no autonomy improvement is established.
Pre-suspend supply requests must be reconciled with late suspend transitions:
L17 is explicitly disabled and L12 receives a zero sleep-enable request.
The collector, trace instance and RTC alarm are cleaned up; Wi-Fi is enabled
and charging resumed. The power diagnostic record contains the consumer mapping
and remaining limitations. The instrumented radio-off comparison subsequently completed: four Wi-Fi VRM
sleep-enable requests are zero, yet the gauge still reports approximately
93.135 mA with 99.612% suspend occupancy. L5/L6 receive low-power-mode commands;
L17 is disabled before machine suspend. Wi-Fi was restored and the collector,
trace and alarm cleaned up. No autonomy fix is demonstrated. Reported 2,822 mAh
full capacity and cycle count one are gauge state, not verified physical health;
the operator confirmed the original battery. See the diagnostic record for the
charge-counter scaling and measurement limits.

The constructor's private-status reporting issue has a host-validated fix:
16 metadata cases and a newly prepared observer preflight passed without a
kernel build. Existing diagnostic images and historical prepared recipes were
not modified; interactive sudo and a full manual build remain to be retested.
A powered-off battery comparison is pending after an invalid first attempt
that restarted the phone. There is no new battery result or autonomy fix.
See the power diagnostic record for return-measurement and kernel-identity limits.

## Integrated current-image entry point — 2026-10-09

The operator-selected [`lmi-current` profile](../../build/profiles/lmi-current/README.md)
is installed during the userdata build through `build/build-current-lmi.sh`.
It incorporates the validated application launchers, torch, audio/microphone,
UPower status and CPU-idle opt-ins. The operator-built image boots Mobian with working USB SSH, registered ALSA
card and active UPower/CPU-idle services on the existing RPMh kernel. Full
application, audio and vendor-runtime validation remain pending; battery
autonomy is unresolved and the experimental Snapshot bridge is not
production-integrated. See the [first-boot power record](../../kernel/diagnostics/power/README.md#integrated-userspace-first-boot-and-bluetooth-readback--2026-10-09). Reuse the
existing RPMh boot; no additional kernel build is required.


Current-image follow-up (2026-10-09): a shortened 128.528-second idle observation
gave 86.38 mA from the gauge with 99.455% suspended; it is not a completed
180-second comparison. High idle consumption remains unresolved. The current
recipe now reuses the reviewed time-seed floor omitted from the first image;
its helper and timer are active on the handset, without a direct RTC write.
No rebuild or reboot validation of this recipe revision has been performed.
See the [qualified idle and clock record](../../kernel/diagnostics/power/README.md#integrated-userspace-short-idle-observation-and-clock-floor--2026-10-09).


The current profile also exposes the mounted stock Venus firmware through
validated loader references. Both downstream codec nodes passed a bounded
open/QUERYCAP/close check on the handset. Media streams and idle-power effects
remain unvalidated; no camera-ready or autonomy-fix claim follows from this.
See the [Venus correction record](../../kernel/diagnostics/power/README.md#current-image-venus-firmware-reference-correction--2026-10-09).


A complete follow-up idle interval lasted 181.416 seconds with 99.617%
suspended and 86.103 mA derived from the gauge. The RTC-delay guard passed
and collection cleanup completed. All PCM streams were subsequently closed
and codec DAPM bias levels Off. Idle autonomy remains unresolved.
See the [complete idle observation](../../kernel/diagnostics/power/README.md#complete-current-image-idle-observation-after-clockcodec-preparation--2026-10-09).


### Current-image indexer correction — 2026-10-10

The first same-boot overnight return showed 100% to 65% over 9 h 22 min,
with only about six minutes of system suspend. A metadata-indexer failure
accumulated 28609 zombie children and exhausted user process resources.
Stopping/masking `localsearch-3.service` removed those children and restored
user command operation without reboot. The persistent handset mask and
current-profile recipe correction disable background metadata indexing;
files and indexing databases were preserved. Automatic return to suspend
and improved autonomy remain unvalidated. No kernel build was required.
See the [qualified overnight and resource-exhaustion record](../../kernel/diagnostics/power/README.md#overnight-return-and-metadata-indexer-resource-exhaustion--2026-10-10).


### Automatic-suspend notification loop workaround — 2026-10-10

The integrated handset could remain awake because GSD's critical impending
suspend notification woke Phosh and recreated the idle sleep watch. A scoped
60-second comparison reproduced the loop; disabling notification screen
wakeup allowed automatic deep suspend at 60 seconds, lasting about 136
seconds until USB return. The 900-second normal timeout is retained.
The handset and next-image profile disable notification-triggered screen
wakeup; alerts remain available. This broad workaround requires long-interval
validation and does not establish normal standby consumption. No new kernel
or image build was needed. See the [qualified diagnostic record](../../kernel/diagnostics/power/README.md#automatic-suspend-warning-wakes-the-screen--2026-10-10).


The normal-timeout observation now confirms automatic deep suspend at about
900 seconds, followed by a second deep-suspend entry about 16 seconds after
an intermediate wake. The 18-minute interval contains about 176 seconds of
suspend because the initial 15-minute timeout is intentionally retained.
This is a validated suspend-policy correction, not a deep-sleep-current or
overnight-autonomy result.


The attended NPU bandwidth isolation completed with the software target zero,
but yielded 88.036 mA from the gauge versus the previous 86.103 mA reference.
No visible battery improvement was demonstrated; the original governor was
restored. Automatic suspend is validated separately, while residual deep-sleep
consumption remains unresolved.


A three-client NPU bandwidth isolation yielded about 49.2 mA from the gauge;
an immediate return to the original policy yielded 86.6 mA with comparable
suspend duration. This supports a causal power-policy lead, but remains a
short diagnostic comparison. Original governors are restored; no permanent
NPU policy is enabled and overnight autonomy is not yet validated.


A bounded suspend-only NPU policy trial reproduced about 50.6 mA from the
gauge, with original performance policy restored before user-session thaw.
Touchscreen and application scrolling were confirmed normal after resume.
The temporary hook was removed; permanent build integration and overnight
validation remain pending.


### Suspend-only NPU bandwidth policy (2026-10-10)

The current profile includes the suspend-only three-client bandwidth policy,
with exact kernel/baseline guards and independent post-suspend recovery.
Production files are installed; awake governors/targets remain unchanged and
out-of-lifecycle apply is rejected. Fifteen failure/recovery tests pass.
The permanent hook passed an attended 181.258-second sleep cycle: 99.607%
suspended, 2,497 uAh loss, gauge estimate 49.593 mA, original governors/targets
restored and recovery state removed. Wi-Fi stayed enabled; alarm and trace
instances were cleaned.

One automatic cycle with the permanent NPU hook is now validated: deep
suspend began 900.419 seconds after the unplugged baseline, with 274.239
seconds suspended in the 1,202.132-second observation. The hook applied once
and restored the original policy once on wake; recovery state and RTC alarm
were absent. No forced suspend or RTC alarm was used. The unchanged 100%
capacity and charging return do not establish calibrated current or autonomy.
Multiple automatic cycles, night-long and fresh-image validation remain pending.
Short gauge results near 50 mA versus 86.6 mA original-policy do not establish
night-long autonomy or calibrated current. See
[power policy details](../../userspace/power/README.md#suspend-only-npu-bandwidth-policy-2026-10-10).

With the NPU correction active, Wi-Fi isolation measured 50.150 mA from the
gauge versus 49.593 mA with the radio enabled: no visible reduction in these
short intervals. Wi-Fi and original awake NPU performance were restored. See
[the qualified comparison](../../userspace/power/README.md#wi-fi-isolation-with-the-npu-correction-active).

A planned thirty-minute follow-up was interrupted by the second gauge wake
after 22 minutes 22 seconds. Its valid unplugged counter interval gives
69.015 mA, so sustained consumption near 50 mA is not established. Three NPU
sleep/recovery pairs were observed and cleanup passed. A diagnostic retry
interface typo was found and corrected privately; no new trial was started.
See [the interruption and limits](../../userspace/power/README.md#longer-observation-interrupted-by-gauge-wakeups).


### BMS measurement qualification — 2026-10-10

A completed 721-second corrected-policy observation and an interrupted
620-second original-policy reference corroborate the NPU benefit: sleep
raw-counter rates were approximately 83–84 versus 145 mA, and instantaneous
wake readings approximately 49 versus 86 mA. This supports about 42% lower
readings within each method; neither method is an independently calibrated
physical ammeter. Software counters can be reprimed and use a different
capacity scale, so their reported mA values must not be treated as exact
physical consumption. The reference did not complete its planned 12 minutes.
Its cleanup ran twice and the second invocation failed on an already removed
timer; production-policy restoration was independently confirmed. Residual
standby consumption remains unresolved and a fresh image has not validated
this integration. See [the power diagnostic record](../../kernel/diagnostics/power/README.md) for segment values,
source qualifications, and restoration evidence.


### Next targeted power candidate — 2026-10-11

All four L3 frequency voters currently request their maximum under performance
governors. Source review supports a bounded suspend-only isolation at the
existing minimum, with original awake requests restored and the validated NPU
correction retained. Nineteen Linux restoration/guard tests pass. This remains
an uninstalled, unmeasured diagnostic candidate, not a confirmed residual-power
fix or a current image-profile change. See [the power diagnostic record](../../kernel/diagnostics/power/README.md).


### L3 candidate outcome — 2026-10-11

An attended first sleep segment with all four L3 requests at their existing
minimum showed no visible additional benefit beyond the NPU correction:
raw-counter rate 84.24 mA, instantaneous wake reading 50.292 mA. The collector
then double-counted prior wake metadata and ended before its three-minute
target. A reviewed detection guard passes seven cases plus the retained-log
replay, but has not been deployed. All original L3 policies were restored,
and the temporary hook, alarm and trace instance were removed. No permanent
L3 policy is adopted; see [the diagnostic record](../../kernel/diagnostics/power/README.md) for qualifications.


### CPU dynamic-governor usability — 2026-10-11

A temporary schedutil trial passed touch, application launch and scrolling,
with all original CPU limits preserved and original governors restored.
The preceding twenty-second probe confirmed dynamic frequency selection.
No consumption reduction is demonstrated yet; this candidate targets awake
operation before automatic suspension. No permanent CPU policy is installed.
See [the diagnostic record](../../kernel/diagnostics/power/README.md).


### CPU governor comparison completed — 2026-10-11

Two screen-off awake phases completed, with no suspend and identical CPU
limits. Schedutil gave about 4% lower gauge-counter rates, but instantaneous
medians were close (90.331 versus 89.355 mA). This small sequential difference
does not explain residual suspended drain; no permanent governor change
is adopted. Original policies were restored and the owned inhibitor removed.
The next source review concerns unconfigured core_ctl busy thresholds.
See [the diagnostic record](../../kernel/diagnostics/power/README.md).


### core_ctl mechanism verified — 2026-10-11

A twenty-second plugged probe changed only the larger CPU groups' busy
thresholds, retaining their minimum counts and all CPU frequency policies.
The three-core group reduced its active count to one at rest and returned
to three after verified restoration. No consumption benefit or deep-suspend
effect is established. Application validation precedes a battery comparison;
the candidate is not installed permanently.
See [the diagnostic record](../../kernel/diagnostics/power/README.md).


### core_ctl comparison closed — 2026-10-11

Applications and touch passed the temporary threshold trial. A complete
six-minute screen-off awake comparison confirmed reduced scheduler-active
core counts but no coherent consumption gain: gauge-counter rates increased
slightly while instantaneous current declined slightly. All original policies
were restored and the owned inhibitor removed. No permanent core_ctl policy
is adopted; this does not solve the residual deep-suspend drain.
See [the diagnostic record](../../kernel/diagnostics/power/README.md).


### Elapsed-since-unplug confound in the short recovery control — 2026-10-18

Re-reading the retained long Android daytime trial adds an important boundary:
its first hourly gauge quotient was44.99 mA, then18.00,15.00 and10.00 mA in
subsequent hourly windows. Early rounded history charge updates went from2626
to2625 mAh at10.547s and2620 mAh at229.279s after departure. The history is too
coarse for a synchronized three-minute comparison and includes gauge behavior;
these values are not independently calibrated current measurements.

Consequently, the approximately53mA short recovery result demonstrates the
quantity under that short protocol, not persistently elevated recovery demand
or proof of missing Android initialization. A future discriminating control
must match elapsed time since unplug and gauge/SOC conditions, preferably using
already scheduled longer observations rather than repeating short controls.
Retain shared-platform and initialization hypotheses without treating either as
established by the recovery result. No additional hardware trial was started.


### Passive overnight observation after recovery return — 2026-10-19

No collector was armed for this unplugged night. At the attended return,
Mobian retained the same boot as the prior recovery-return check and reported
84% while already charging. This is not a discharging return endpoint and no
precise loss/current or autonomy estimate is derived from it.

The retained journal contains31 complete deep-suspend pairs. Their rounded
wall-clock durations sum to31124s within a31596s observed window, approximately
98.51%; this window excludes unobserved initial unplug/idle time. Firmware sleep
records show31 entries and31116000ms accumulated for the named aosd/cxsd/ddr
records, corroborating extensive sleep without calibrating electrical demand.
Thirty wakes were msoc-delta and the final wake was USB typec-cc-state-change.
Journal resuspension delays were15-16s. All31 NPU zero-target markers and31
restoration markers were present. The RTC alarm was empty on retrieval.

This supports continued operation of automatic resuspension and the NPU hook
after returning from recovery. It does not resolve residual demand or create
a matched consumption comparison with Lineage/recovery. No new test, policy
change, build, flash or recording was started during retrieval.


## Recovery half-hour control and offline time repair — 2026-10-19

R3 completed1801.29s between USB-off/Discharging endpoints, with1795.751s
actually suspended (99.693%). Seven resumes: six RTC and one msoc-delta.
Original recovery sleep/NPU settings were restored, RTC cleared, charging verified.
Operator returned normally to Mobian; kernel, homedrag7/Phoc/GSD versions,900s
inactivity timeout and NPU hook were verified. No further trial is active.

Software-counter rates in successive ten-minute windows were51.14,50.88,50.99mA;
overall51.00mA. Raw nominal-scaled rates were88.05,88.38,88.03mA on a different
capacity scale. Filtered endpoints rose from charging history toward19.51,47.60,
49.88mA. They are not integrated interval current. Shared-gauge estimates do not
constitute electrical calibration. No falling half-hour demand was observed,
but this does not reproduce the later1-2h Android regime or identify a culprit.

Europe/Paris was correct after return, but system time lagged the trusted host
by about82min with timesyncd active and NTPSynchronized=no. CLOCK_REALTIME was
corrected to within a second of the host without PMIC RTC writes. A private
trusted UTC/RTC anchor and conditional boot oneshot were installed, verified,
enabled and executed successfully. Seven pure model tests pass. A fresh boot
through the new service has not yet been physically tested. It adds no periodic
process or wake alarm. Generic images skip it until a trusted per-device anchor
is captured; same-phone rebuilds can supply M1_RTC_TIME_ANCHOR_FILE privately.

Sources: userspace/power/diagnostics/recovery-control and userspace/power/clock.
The image recipe includes the helper and conditional service; no heavy build,
image generation or flash was started. Longer recovery variants remain unvalidated.

## October 20: systematic peripheral audit ledger

A [common checklist](../validation/lmi-standby-peripheral-checklist-2026-10-20.md) now consolidates existing standby evidence and unverified peripheral states. The connected software inventory has 849 compatible DT nodes and 697 entries across 15 selected buses (607 bound). These are software entries, not physical chip counts or measured sleep power. A grouped reversible one-hour observation is pending; no residual-drain fix or new build is claimed.

## October 21: Android/Mobian return and host selector qualified

After full Android setup and root ADB inspection, native Windows ADB requested
Fastboot and temporarily booted the pinned adapted Mobian image. SSH confirms
root loop0p2 backed by dedicated sda35 (16 GiB), running Phosh/Phoc processes,
empty dpkg audit, charging and no RTC alarm. No partition was flashed during
this round trip. The per-device validation marker and private PC selector
configuration are now enabled for pinned RAM boots. The persistent boot
partition still holds the previously installed Mobian boot; the adapted boot
has not been installed persistently. The requested on-handset 15-second menu
with Mobian default remains unimplemented.

Mobian wall time was aligned to the host and Europe/Paris selected. The existing
offline RTC-anchor helper captured a trusted reference and its boot restoration
service is enabled. The anchor check differs by less than one second; this new
reference has not yet been validated through another boot. The hardware RTC
counter was not written. NTP is active but network synchronization is not
confirmed.

## October 21: dedicated handset-menu recipe prepared, not built

The new build/boot-menu directory contains pinned upstream sources, an isolated
operator-run Debian bookworm build, a temporary menu probe, guarded boot-v2
component extraction and seven host parsing tests. The untouched probe requests
Mobian after 15 seconds by restarting the existing boot partition; it must not
be installed persistently. Android chainloading, UEFI display/input and a real
handset dual-OS menu remain unvalidated. The source parser does not process our
v2 DTB field; explicit component/DTBO handoff is still required. No firmware was
compiled or booted during preparation. See [recipe](../../build/boot-menu/README.md).

## October 21: first handset-menu probe compiled

The operator's isolated EDK2 build completed. The 7059456-byte temporary probe
has SHA256 f39e2c65a434a90ae3d8a11cfa2b40e6113f6eee27eb6e73bd5b54cdcbd713a1;
the host independently re-read it and the exact patch manifest, then verified
the Windows transfer. No UEFI handset boot has occurred yet. This is still a
menu/countdown probe, not Android chainloading or a persistent dualboot menu.
The Windows operator helper has passed host-only plan mode. See the dedicated
[recipe and build result](../../build/boot-menu/README.md#first-operator-build-result).

## First handset probe and revision 2 correction

The operator temporarily booted the first probe. The menu is visible. Touch
does not select/activate entries, but Volume changes focus and Power confirms;
the operator returned to Mobian by selecting its entry and Boot. SSH confirms
the dedicated root, running Phosh and charging after that normal boot. This
also qualifies the old installed RPMh boot's discovery of the new root layout.

The automatic path failed: source review identifies that bootmenu_add explicitly
excludes BOOT_REBOOT from auto-selection. The probe uses BOOT_REBOOT for Mobian,
so no default selection exists and bootmenu_load never starts the timer. This
was an integration error in revision 1, not an observation of a failed RTC or a
failed reboot handler. The physical button path proves the latter can run.

Revision 2 permits default auto-selection for the named Mobian reboot entry
only. Fastboot/recovery are still excluded from automatic selection. It also
enumerates Mobian, Fastboot, Recovery explicitly, independent of confd child
order. Exact before/after source hashes and patch-idempotence checks pass. The
seven boot-component parser tests still pass. Revision 2 has NOT been compiled
or handset-tested yet; rerun the same operator build command. The existing
Windows launch helper remains pinned to revision 1 until a new artifact hash is
reviewed and transferred. Do not use it to launch a rebuilt image with a new
hash. Touch support and Android chainloading remain separate pending work.

## Revision 2 compiled, handset verification pending

The operator completed the corrected build. The image is 7063552 bytes, SHA256
10f69a7693038b01244a8095c68240554e5717684218c87574ba8c36f5520bcc.
All three patched source hashes match the lock, including bootmenu.c. Windows
transfer was verified as lmi-menu-smoke-v2-20261021.img. The Windows test helper
now pins this revision and keeps its result separate from revision 1.
Untouched countdown and explicit menu order remain pending handset verification.
The final requested order is Mobian, LineageOS, Fastboot, Recovery. This probe
still contains only Mobian, Fastboot, Recovery: LineageOS chainloading is pending,
not hidden or qualified by this build. Touch input is not yet operational.

## October 21: menu countdown accepted; LineageOS candidate prepared

The operator confirms revision 2 auto-boots after 15 seconds. Independent SSH
after return confirms dedicated sda35 backing, root loop0p2, running Phosh and
charging. This validates the temporary menu's automatic path. It does not
validate touch input or direct Android/Mobian chainloading.

The new [experimental LineageOS recipe](../../build/boot-menu/chainload/README.md)
adds the missing second entry and packages the two pinned images' exact
components plus the installed Android DTBO in a protected FV section. The
128 MiB firmware reservation and following RAM range are adjusted together;
the arbitrary-ramdisk approach was rejected before any build/boot. Actual-input
bundle creation (116559872 bytes), C bounds checks and source patch/restoration
checks pass. The candidate firmware has NOT been compiled or target-tested;
it is temporary-only and must not be flashed. The existing Mobian cold-reboot
default is retained while Android handoff is qualified.

## Experimental Lineage menu build completed

The operator's second attempt completed after the include-order correction.
The final boot image is 47302656 bytes, SHA256
2d4284b5fc26fb8e90c529eb714e5d9076b8b01331bc707d00758dd94335ef11.
The compressed FV occupies 46301152 bytes of its 128 MiB reservation. All 11
patched-source hashes match their build manifest; the verified asset bundle
SHA256 is f274b93fee79315b9f4cdf8e45d08a09a12f027a922e8dc7961ca8ed111f2892.
The Windows copy and host-only helper preflight also match. Neither the expanded
firmware nor LineageOS handoff has yet been booted on this handset. The Windows
helper is pinned to this image and contains no flash command. Use Volume/Power
to select LineageOS, then activate Boot. A focus change cancels the countdown.

## October 21: large Lineage candidate failed before menu; compact recipe ready

The expanded-FD candidate 2d4284b5... was temporarily booted and remained black
before any menu appeared. ADB/Fastboot/SSH were absent, and the operator had not
selected LineageOS. A long Power press returned to the unchanged installed
Mobian; root loop0p2, Phosh and normal battery status were confirmed over SSH.
pstore was empty. The precise firmware failure stage is unknown; this is not
an observed Android kernel/handoff failure. The old Windows launcher is retired
and rejects execution before phone contact.

The replacement bundles only the five Android components (61906944 bytes) and
limits FD to 32 MiB, fitting the upstream lmi reservation without changing its
memory map. Compact bounds tests, real-input packaging, exact source restoration
and unchanged-map checks pass. No compact firmware has yet been built or tested.
See [current candidate](../../build/boot-menu/chainload/COMPACT.md).

## Compact candidate compiled; temporary handset test pending

The compact build completed: 25993216 bytes, SHA256
a6b4e95476d8161ea89034915029d3fbc536e4f278ecb753e274ba800befe267.
The compressed volume uses 25070792 of 33554432 bytes. All ten modified-source
hashes match the manifest, and the upstream lmi memory map is independently
byte-identical. Windows transfer and host-only launcher preflight passed.
The new test-lineage-compact-windows.py pins this specific image; the older
failed candidate's launcher remains disabled. No compact handset boot has yet
occurred and no persistent boot change is made.

## Boot menu: pre-menu FFS3 defect reproduced and corrected (2026-10-21)

Both experimental LineageOS-bearing RAM boots stayed black before any menu;
the operator returned to installed Mobian with a long Power press. Their
launchers are retired. The original small menu's Volume/Power navigation and
15-second automatic Mobian return remain hardware validated. Android handoff
and persistent dualboot menu installation remain unvalidated.

The compact FD's 25024772-byte compressed FV uses a 32-byte FILE_HEADER2.
Pinned PrePi uses 24-byte headers, computes checksum 165 instead of zero and
misreads file size/body offset. Replaying the actual C functions against this
FD reproduces rejection; the correction finds the file and proper boundary.
Normal-file compatibility, malformed lengths, exact eleven-file restoration
and refusal of unreviewed edits pass. Full patched FwVol.c passes targeted
Clang 14 ARM64 syntax checking with the existing build flags and -Werror.
No corrected firmware build or phone test has been performed. Recipe and
validation evidence: build/boot-menu/chainload/COMPACT.md. No kernel rebuild,
flash or partition change is part of this correction.

## FFS3-corrected candidate compiled; temporary handset test pending

The operator build completed. Image: 25993216 bytes, SHA256
eea24170b1d63bb4028b94c66437db9a1add3a4b67a5616e88ca15b1547b2f6e.
All eleven source hashes match the manifest, including corrected PrePi; the lmi
memory map is unchanged. Old/patched C replay against the newly built FD again
reproduces the old rejection and corrected traversal/content boundary. Windows
image transfer and plan-only launcher preflight passed. The new launcher is
test-lineage-ffs3-windows.py; both earlier experimental launchers remain retired.
Handset menu display, Android handoff and persistent installation are not yet
validated. No phone command or flash was performed during these checks.

## Menu confirmed; LineageOS selection returns to UEFI setup

The operator explicitly confirmed the FFS3-corrected menu appears. Selecting
LineageOS then displays EDK2 setup (Device Manager / Boot Manager / Boot
Maintenance Manager), not Android. Installed Mobian has been restarted and
remains usable. No experimental firmware was flashed. Kernel execution is not
demonstrated and the exact returned error is not yet known.

A diagnostic-only recipe update records the last attempted launch stage and
shows the latest six warnings/errors from RAM for up to 120 seconds on a
returned failure. All three C units pass Clang 14 ARM64 -Werror syntax checks;
thirteen-file exact restoration and tamper rejection pass. No diagnostic build
or handset test has yet occurred. See chainload/HANDOFF-DIAGNOSTIC.md under
build/boot-menu. Next operator build uses the same --build --with-lineage command;
the manifest variant ends in prepi-ffs3-diag1. This is instrumentation, not a
claimed Android boot fix. No flash, kernel rebuild or partition change required.

## Diagnostic image compiled and qualified for temporary test

The operator compiled variant prepi-ffs3-diag1: 25995264 bytes, SHA256
287645d2b55060b15006037c6fa3a91180954af85cf4286ded2daae14b9803f0.
All thirteen source hashes match; the lmi memory map remains unchanged. The
PrePi replay passes on the new FD. Windows transfer and plan-only launcher
preflight passed. Use test-lineage-diagnostic-windows.py for this exact image.
No new phone contact, flash or persistent installation was performed. The
diagnostic error panel remains untested on the handset; Android handoff is
still unvalidated. The next observation is the stage/error after LineageOS
selection, not another blind boot attempt.

## LineageOS launch localized to board-only DTBO matching

The diagnostic handset image shows stage 08 apply DTBO and rejects lmi overlay
7 with "vote too few". It then returns to UEFI setup. Kernel execution has not
occurred. All twelve pinned Android overlays have board-id but omit msm-id;
the old matcher treats the missing SoC field as zero and rejects it against
the actual platform SoC. lmi board-id is (37, 0).

A minimal overlay-only correction inherits platform SoC fields only when
msm-id is absent and board-id is well formed. Board matching remains active;
explicit/malformed msm-id is not overridden. No guessed index or ignored
overlay error. Actual C voting against all twelve real board IDs passes eight
representative board-37 profiles, accepting only lmi after the correction.
Four-unit ARM64 syntax and fourteen-file exact restoration/tamper tests pass.
This dtbo1 correction is not yet built or hardware validated. See
build/boot-menu/chainload/DTBO-BOARD-ONLY.md. Same operator build command;
new variant ends in prepi-ffs3-dtbo1. No flash or kernel rebuild performed.

## Board-only DTBO correction compiled; handset test pending

The operator built dtbo1: 25997312 bytes, SHA256
969ee0c3d49083adfd17ea199575df55b211c66b5071d96fb24c8701fb82bed1.
Fourteen source hashes match, the lmi memory map is unchanged, and PrePi replay
passes on the rebuilt FD. Windows transfer and plan-only preflight passed.
test-lineage-dtbo-windows.py pins this image and now requires an explicit SSH
guard-completion marker before waiting for Fastboot; an absent USB link is no
longer mistaken for a possibly successful reboot. No phone command or flash was
performed in qualification. Actual DTBO application and Android handoff remain
pending; the diagnostic stage/error panel is retained.

## Android kernel and first-stage init confirmed; logical mount fix prepared

The dtbo1 test returned to Fastboot. Installed Mobian was recovered; private
archived console-ramoops shows the exact Lineage kernel running /init, then
a ten-second wait for physical system/vendor devices and InitFatalReboot with
bootloader target at about 12.3 seconds. This confirms Android kernel/first-stage
execution, not a completed Android boot. No experimental firmware was flashed.

All three pinned Android DTBs retain a physical ext4 vendor DT fstab; the pinned
ramdisk has the correct logical first-stage fstab, including erofs vendor.
Lineage prioritizes the DT table. The new Android-only stage-14 correction
removes that exact known legacy subtree in RAM, leaving the original ramdisk,
AVB policy, super metadata, GPT and installed boot unchanged. Unknown tables
are rejected. No command-line cleanup is included.

Actual C/libfdt tests on all three real DTBs plus the board-matched lmi overlay
pass, with every unrelated property unchanged. Wrong-OS and unexpected-path
guards, four-unit ARM64 syntax and fifteen-file exact restoration/tamper tests
pass. No fstab1 build or hardware test has yet occurred. See
build/boot-menu/chainload/ANDROID-FIRST-MOUNT.md. The operator command is unchanged;
new variant ends in prepi-ffs3-fstab1. Later Android startup issues may remain.

## Android logical-fstab image compiled; handset test pending

The operator built fstab1: 25993216 bytes, SHA256
eae891e3bbe03d2b15857a11319000da4eca81adac009d093126593bb548ad1f.
All fifteen source hashes match, the lmi memory map is unchanged and PrePi
replay passes on the rebuilt FD. Windows transfer and plan-only launcher
preflight passed. test-lineage-fstab-windows.py pins this exact image and
requires the SSH guard-completion marker before waiting for Fastboot.
No phone command or flash was performed during qualification. The removal of
the legacy DT table and progress past first-stage logical mounting remain
pending handset observation; Android userspace is not yet validated.

## Recovery user-init failure: direct stock-Android control prepared

fstab1 reaches recovery with init_user0_failed. The original Android failure
trace has been replaced by recovery activity; the exact data-initialization
failure is unknown. Mobian is restored. Read-only checks confirm separate
partitions; raw userdata can be encrypted, so its signature does not establish
corruption. Cache logs were captured with a temporary ro,noload mount, removed
afterwards. No wipe, flash or partition change was performed.

A Windows helper for the exact stock Lineage RAM boot passes plan-only image
verification. This will distinguish a menu-specific failure from normal Android
startup failure. See build/boot-menu/chainload/ANDROID-DATA-CONTROL.md. No new
build required. Execution and full Android startup remain pending. Security
context/key-management differences are hypotheses, not established causes.

## Stock Android succeeds; OS-version header control prepared

Original Lineage boots; operator confirmation and native Windows root ADB
independently establish boot_completed=1 and encrypted F2FS /data mounted.
Live DT and selected technical parameters are saved privately. The menu header
reports Android 11 / August 2022, versus stock Android 16 / September 2026.
A control copy aligns only this field; only offsets 44 and 47 differ, with
all remaining bytes identical. No compilation, partition change or key change.
Derived SHA256: 71e226f1a8adaf5d0574d1311d686143694404f49ab62df5d343c8a36c3c5196.
The Android-start Windows RAM launcher passes plan-only verification. Actual
outcome remains pending. Hardware-key version context and inherited AVB
metadata are hypotheses; no AVB bypass is proposed. Standard builder unchanged
until validation. See build/boot-menu/chainload/ANDROID-OS-VERSION-CONTROL.md.


## Compatibility-DT variant correction, 2026-10-22 (host only)

The successful temporary menu Android boot reports lmipro / CN / 3.9.0, whereas
the recorded direct stock Android command line supplies std / GLOBAL / 3.19.1.
The menu passes both sets. The pinned compatibility DT has the stale pro/CN
values before the actual bootloader arguments, explaining the Zoom Edition
identity. No system property or device identity was overwritten on the phone.

The candidate now removes only those first three known stale variant tokens
from the final in-memory DT bootargs, and only when a later value for the same
key exists. Unknown or multiple ambiguity is rejected before any buffer change.
Unrelated arguments (including AVB policy) remain byte-for-byte unchanged.
This correction applies only to the qualified android/mobian menu targets.
The source manifest now tracks seventeen edits for dual mode.

Actual C tests cover the real compatibility/stock argument combination, repeated
execution, unknown first value, empty value, excess duplicates and missing NUL.
Four affected ARM64 units pass syntax checks; source restoration and tamper
checks pass. The corrected fstab host checks retain the Mobian no-op. Hardware
model identification is still unvalidated for the new candidate.


## Board argument audit follow-up (host only)

The saved direct-stock/compatibility-DT audit finds nine differing duplicate
board argument keys, not just the three model-variant keys. The candidate now
also retains the later hardware-supplied camera configuration, network mode,
DTBO index, certificate model and device identifiers instead of the earlier
sample values in the pinned compatibility DT. No real identifiers are stored
in source or public notes. Device properties on the running handset are unchanged.

Only the nine explicitly reviewed keys are deduplicated, and only with exactly
two non-empty occurrences. The three initial model fields additionally retain
their known-template checks. Every other argument and its order remain unchanged,
including AVB policy. This is not a generic command-line rewrite. Host C tests
on the real saved compatibility/stock pair verify all nine later values and
the complete unchanged unrelated-token sequence; malformed/ambiguous inputs
are rejected. Hardware validation still requires the next temporary build.

## Incremental runtime activation — 25 October 2026

The IRQ-name-independent Phosh/GSD packages are installed and user-accepted for normal application use, drawer and power-button handling. Runtime process hashes and both opt-ins match the built artifacts; same temporary kernel boot and published j11 profile were retained, as was the accepted private-FBO Phoc renderer. The owned automatic rescue timer was cancelled after acceptance. Phosh package tests:36 OK; GSD:1 OK and9 SKIP.

The original fixed-IRQ mismatch is established; corrected natural gauge-resume behavior and battery benefit are still unvalidated. No full image or permanent boot was changed or promoted. See `userspace/power/irq-name-candidate/device-activation-20261025.json` and `docs/validation/lmi-irq-name-policy-2026-10-25.md`.

## Accepted closed-drawer previews — 25 October 2026

The incremental Phosh drawerpreview1 package is installed and operator-accepted: running previews are hidden on the closed home page and visible inside the open drawer; favorites remain at the bottom and gestures respond normally. All36 Phosh package tests passed. The actual running binary SHA256 is17f5cb077e08a1e93b13b6a828e69b225d7008e3c3db4faa03e26325b58ea159. Rescue rollback was cancelled after acceptance.

The same temporary kernel/published j11 profile, GSD IRQ-name policy and accepted Phoc private-FBO thumbnail renderer are retained. This is an incremental userspace milestone, not a new full image. Natural gauge-resume/energy validation remains pending. Evidence: userspace/phosh/closed-drawer-preview-candidate/device-acceptance-20261025.json.

## Natural gauge-resume validation —25 October 2026

Two detached msoc-delta resumes with the IRQ-name policy returned to suspend after14.862s and15.010s between D-Bus events; kernel suspend-exit to next deep-entry intervals were15.673s and15.792s. The preceding uncorrected-night median was1201.076s. No WakeUpScreen signal occurred during these two natural cycles and ScreenSaver.GetActive stayed true. This is not a direct panel-power measurement. Same boot/profile, clean capture closure and active Phosh/GSD with zero restarts were confirmed; the collector finished successfully.

The return-to-sleep defect is hardware-validated for these two cycles. A final USB-triggered resume is excluded. Two separate raw-counter brackets give25.201 and24.614 reported units per suspended second (awake callback margin included in the numerator); these are not calibrated current. Current charge_full2637000 differs from the historical2677000. Historical comparison and autonomy/sole-cause conclusions remain limited. Full-image pins have not yet been promoted to these incremental runtime packages.

Evidence: userspace/power/irq-name-candidate/natural-resume-validation-20261025.json. No additional test, reboot or policy change was launched on return.

## Next complete-image recipe updated —25 October 2026

Following the runtime validations, the complete-image recipe now selects the accepted Phosh drawerpreview1+irqnames1 pair, GSD esrquiet1+irqnames1 pair and existing private-FBO Phoc. Five exact package SHA256 guards prevent fallback to older variants; both Phosh and GSD are replaced in the nine-input manifest. The percentage display is an explicit profile default. Base non-complete package selection is retained.

Host validation passed:9 stable and7 complete staging tests, strict GSettings schema compilation, shell syntax and five actual package hashes. No new image/kernel/flash was performed. The temporary diagnostic boot/DT is not promoted. See build/profiles/lmi-current/COMPLETE-BUILD.md for the current selection; earlier image identities remain historical.


## Sustained quiet wakes and pending search improvements —25 October 2026

Five further natural gauge wakeups returned to suspend in about16seconds at
kernel boundaries, extending accepted coverage to seven cycles. The81.775minute
unplug included65.192minutes suspended and the normal initial idle wait. Displayed
capacity100->95% and raw progression24.676663reportedunits/suspendedsecond are
gauge observations, not calibrated current or projected autonomy. The old
~1201-second awake dwell did not recur. Capture finished cleanly; collector
inactive/success, same boot/profile, no alarm or recovery pending. See
docs/validation/lmi-quiet-wake-long-baseline-2026-10-25.md.

A separate drawer-search candidate is prepared but NOT built or installed:
Enter activates folder results and empty searches show an explicit hint.
An incorrect external signal callback was corrected and independently checked
using actual native GObject signal marshalling; this is not GTK/phone validation.
Default recipe preflight passes and preserves the accepted home/power/renderer
sources and rollback packages. Complete-image pins remain on the accepted
drawerpreview1 build. Recipe: userspace/phosh/drawer-search-candidate/README.md.


## Pending empty-search swipe-close candidate —25 October2026

The handset remains on accepted drawerpreview1 after the unaccepted search test
was rolled back. The reported empty screen was resolved by clearing retained
text on that older version; no new-version crash was established. The requested
UX change is now a separate revision2 candidate: clear a zero-result query only
after completed drawer closure, preserving result-bearing/cancelled searches.
The delayed GTK search signal gap has explicit raw-input/generation guards.

Recipe preflight, strict source/patch hashes and the15-case design model pass.
These are host checks, not GTK/tactile acceptance. The build input is drawersearch1
but the rescue remains installed drawerpreview1. No package built or installed,
and no complete-image pin changed. See
docs/validation/lmi-empty-search-drawer-close-candidate-2026-10-25.md and
userspace/phosh/drawer-empty-search-close-candidate/README.md.


## Host-only follow-up and pending UI build — 25 October 2026

The operator has built drawersearch1+draweremptysearch1 (36 package tests OK,
zero skipped); it is NOT installed. The handset remains on accepted
irqnames1+drawerpreview1 with the accepted Phoc/GSD. Complete-image pins stay
unchanged. The passive night is armed; no handset contact occurs while unplugged.

Offline recheck extends the existing, unintegrated ADC shadow-retry test to
32 cases per implementation. It is a shared source defect, already documented
on 7 October, with no demonstrated occurrence or battery-current causality.
See docs/validation/lmi-offline-gauge-recheck-2026-10-25.md.


## Battery research checkpoint — evening25October2026

The [current research checkpoint](BATTERY-RESEARCH-CURRENT.md) identifies accepted
quiet-wake behavior, the untouched passive night, pending UI acceptance and
known hypotheses that must not be rediscovered as new causes. A source review
of Wi-Fi STA power-save finds a conditional host-suspend path, not an active
phone-setting mismatch or a battery cause. No device operation followed.
