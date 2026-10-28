## Snapshot 51 deployed, and the third kernel facility identified — October 28, 2026

The Flatpak deployment of the Snapshot 51 candidate, which failed on the
downstream 4.19 kernel because it did not provide `STATX_MNT_ID`, now
succeeds on the kernel of the permanent boot: the measured `statx` mask is
`0x17ff` with a mount identifier present, the retained objects were reused,
and `org.gnome.Snapshot 51.0` is installed for the session account.

The candidate reaches its own start and stops on the next facility. The
document portal of the session cannot mount its export directory because
`/dev/fuse` does not exist: the kernel carries `CONFIG_FUSE_FS=m`, but the
module is not shipped, so the device node is never created. The candidate
therefore stops at startup with `Can't get document portal`.

The camera side of the upgrade stays compatible with the producer of this
branch: Snapshot 51.0 still captures the camera with GStreamer `camerabin`,
which the session already carries, and the camera is still enumerated through
the PipeWire device provider, which is what the producer publishes. The
launcher now knows both versions: it drives the candidate when it is
installed and when the FUSE device exists, and the native application
otherwise, with the tuning preload that belongs to it.

The convergence is the point: the rear camera of the Linux 7 line and the
newer application of the camera need **one kernel build**. The sensor patch
and the camera configuration bind the rear sensor, and `CONFIG_FUSE_FS=y`
creates the FUSE device that lets the document portal mount. Both are
expressed in the same configuration fragment, and the recipe
`kernel/experimental/linux7/tools/build-community-camera-kernel.sh` builds
them together; its preparation step is validated on the community tree. See
the [validation record](../validation/lmi-snapshot51-linux7-preconditions-2026-10-28.md)
and the [recipe record](../validation/lmi-linux7-camera-kernel-recipe-2026-10-28.md).

## Snapshot 51 preconditions on the Linux 7 boot — October 28, 2026

The deployment blocker of the Snapshot 51 candidate is gone on the kernel of
the permanent boot. The 2026-10-26 assessment recorded that the Flatpak
deployment failed because the kernel of that moment did not provide
`STATX_MNT_ID`, which the runtime guard requires. Measured on the running
Linux 7.2.12 kernel, the `statx` mask is `0x17ff` with a mount identifier
present on every path, including the user directory the deployment writes to.
No security check is relaxed and no identifier is invented: this kernel really
provides the facility. The `flathub` remote and 1.7 GB of runtime objects are
still on the handset, so a retry does not download the world again.

The camera side of the upgrade stays compatible with the producer of this
branch: Snapshot 51.0 still captures the camera with GStreamer `camerabin`,
which the session already carries, and the camera is still enumerated through
the PipeWire device provider, which is what the producer publishes. Three
adaptations remain: the launcher has to know which application it drives, the
Flatpak desktop entry would otherwise open the application without the
launcher and therefore without the camera, and the preloaded tuning library
hooks the C internals of Snapshot 48 while Snapshot 51 is a Rust rewrite.
Nothing was deployed on the handset. See the
[validation record](../validation/lmi-snapshot51-linux7-preconditions-2026-10-28.md).

## Camera launcher in V4L2 mode on the Linux 7 line — October 28, 2026

The camera launcher now has a second source. When the OEM capture engine is
missing, it starts the V4L2 producer and waits for it to report a real frame
before opening the camera application, so a node that never frames gives the
explicit reason instead of a black viewfinder. The producer follows the
foreground lease of the launcher, so the camera is powered only while the
application is in the foreground. The OEM path is unchanged, and the notice of
the previous record is shown as before when there is no producer.

Measured on the handset with the current kernel, which has no bound sensor:
the producer probes the fourteen video nodes in under a second and exits with
status 3, the launcher reports the outcome, the notice names it, and no
child process, no producer and no privileged service are left behind. The
success path is not qualified yet, because it needs a kernel that carries the
sensor patch. See the [validation record](../validation/lmi-linux7-camera-launcher-v4l2-2026-10-28.md).

## Rear camera sensor binding prepared on the Linux 7 port — October 28, 2026

The rear sensor of the lmi board never binds on the permanent Linux 7.2.12
boot, and the reason is now identified: the `ov13b10` driver of this kernel
carries only an ACPI match table, with no `of_device_id`, so a sensor
described in the device tree can never be matched. The driver is built in and
registers, the i2c client exists with the right compatible string, and no
probe happens at all. The board device tree is already complete for the
driver, so the change is a kernel patch that restores the OF match table and
not a device tree change.

The patch, the camera configuration fragment and a host check are prepared and
the check passes: the patch applies to the pinned tree and to the community
tree that produced the handset kernel, the patched driver compiles, and the
camera configuration resolves every symbol of the chain. A V4L2 to PipeWire
producer is prepared for the userspace side, since the Linux 7 line has no OEM
preview service to feed the camera application. Nothing has been flashed: the
binding is proven at the source level only, and the camera application keeps
reporting the missing engine until a kernel carrying the patch is installed.
See the [validation record](../validation/lmi-linux7-camera-sensor-binding-2026-10-28.md).

## Camera application on the permanent Linux 7 boot — October 27, 2026

The camera application of the permanent Linux 7.2.12 boot no longer dies on
start. The launcher reports that the OEM capture engine is only qualified on
the Mobian 4.19 kernel and points at the fallback boot entry that the
installed `system5` menu keeps next to the Linux 7 entry. The privileged
publisher refuses with a legible reason, and the launcher and publisher are
deployed on the running system with backups.

No image is produced on the Linux 7 entry. The vendor partition holds no
camera blobs, the kernel has the CAMSS ISP but no Xiaomi camera techpack, and
the rear sensor is not bound, so the application has no frame source and says
so instead of failing silently. The rear preview recorded in the journal on
October 26 belongs to the 4.19 entry, which remains the only system with a
validated rear camera. See the [engine gate record](../validation/lmi-camera-app-linux7-engine-gate-2026-10-27.md).

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

## Historical Linux 7 community RAM references — October 27, 2026

Three RAM-only community boots are hardware-qualified on that line: two as
display and USB milestones, the latest as a bounded Mobian userspace session.
Those historical trials were diagnostic boots, not installable systems: the sessions were bounded in
time, could not retain settings, and established no GPU acceleration, autonomous boot,
suspend or battery result. They are retained as historical reference artifacts.
The later permanent system5 boot is described above.

The qualified 7.2.12 Phosh desktop session, the current base of that line:

- Menu image `43dccd8f5e8543ed5bae17bcdd7129a24fafde8534ba4874efec66176fc41cd6`,
  71,909,376 bytes.
- Outer bundle `39fc67b4c3c6b036730419489e4c4f7cd2b3bcbd6dd5876cbf3521c2eff3a3d8`,
  45,912,145 bytes.
- Kernel Image `703819e444e378d0de4a79523a7faed2066ada9d514dcabb249a96e1f11938d3`
  and DTB `306315e8288ea13c4dc10c017eda3c75aefe4a3a189c906c6567ed6b75b602db`,
  both unchanged from the display and touch base.
- Diagnostic initramfs
  `d3ec261b72b2a8c81485d5e01292d5a792fdaeef49147527e54990f6c2d9729a`.
- Graphics log 26,648 bytes, SHA256
  `5e29281a6ec773d676680144c8aa2ceaa82fe4a5bb787c84192341f6f31ed50a`.

The qualified 7.2.12 community display and touch base it continues:

- Menu image `bdd18157d0e9f3e9a83e53c2d10d5f1ee3e2d187947f23937dbb21b187bc36ed`,
  71,907,328 bytes.
- Outer bundle `2385a16dbc475111fd33a81b13146235dceab7342454ace735cbac3bd14ded24`,
  45,908,049 bytes.
- Kernel Image `703819e444e378d0de4a79523a7faed2066ada9d514dcabb249a96e1f11938d3`,
  46,991,368 bytes, extent 48,758,784, version `7.2.12-lmi-community-port1`.
- DTB `306315e8288ea13c4dc10c017eda3c75aefe4a3a189c906c6567ed6b75b602db`
  (128,544 bytes) and initramfs
  `feaac77aec44734d5ba4bd7ebb659f83f2bbc7fab6191472164a0554adb0eb19`.
- Journal capture 128,947 bytes, SHA256
  `2b6cb737ce7a8ad17a38ed862ffec77cb603af4ded059ce677bdf7aab6da8826`.
- Bounded evdev capture 230,248 bytes, SHA256
  `f69fccea869532d7e01f73c081148e94ed5e9bf32432b043ba0808a1461399fd`.

The earlier display-only 7.2.12 community port, kept for comparison:

- Menu image `99dcf5f303c6d412a3bb2e5cacc55a165a1262d605e5fc59fb34918177d7df9e`,
  71,909,376 bytes.
- Outer bundle `5cf5a7a1d23535cd716af519dfcd963caf59c628aceb445c48e8d9221818605b`,
  45,912,145 bytes.
- Kernel Image `0a41c82fcd1faf482c32d4d78d023ce293a39ce8357b9ff5eb0ceb6dd5644531`,
  46,991,368 bytes, extent 48,758,784, version `7.2.12-lmi-community-port1`.
- DTB `bff7bbf5ad525e5fa23a6afdf6c7660bfa3ad580c67319185ecd18b0aeba4150`
  (128,472 bytes) and the same initramfs, on tree revision
  `cc9de5d4b5ab6459f5774946aa3195ad51236fa8`.
- Journal capture 129,425 bytes, SHA256
  `ba5f473d989d602234e77201b24c26cc9425e1a92cd05242657e98ebfec2d604`.

The earlier 7.1 community reference, kept for comparison:

- Menu image `d96f21a0b80f129bc73b09d6b9eaa4d4ac9e99352f681a9a0a4aff53c8de6f11`,
  72,943,616 bytes.
- Outer bundle `14c940ee4d69b5f5a6b32d778991e859b85cc5fe45dcd3834fb23df184ecd54b`,
  46,948,433 bytes.
- Kernel Image `e40ecc5fecb149be8ad69afb8cf009d6ffab502bce8e91512bafc3ee6ccae3ad`,
  49,190,920 bytes, extent 50,987,008, version `7.1.0-lmi-ccc-ram1`, from
  community revision `3a8409fb1020b5952310072713ce97edea5e65d7`.
- DTB `cf83edb68632917677dcd91e4268024f6f369599d6d53043cd7e71677cde0109`
  (128,468 bytes) and the same initramfs.
- Journal capture 129,701 bytes, SHA256
  `ae822d8ebdcab772f3e263020aee0f8b4fbe434bcfcfe862727899994a2f9bfe`.

All three menus were booted temporarily with `fastboot boot` only. Nothing was
flashed to a partition, and the installed Mobian/Lineage system is unchanged.
See [the Phosh desktop record](../validation/lmi-linux7-phosh-desktop-2026-10-27.md),
[the combined display and touch record](../validation/lmi-linux7-community-display-touch-2026-10-27.md),
[the 7.2.12 display record](../validation/lmi-linux7-community-port-display-2026-10-27.md)
and [the 7.1 record](../validation/lmi-linux7-community-display-2026-10-27.md).

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

## October 24: fuel-gauge profile lookup depends on board-tree order

## Thumbnail source localization, October 24

Raw thumbnail pixels are already striped before Phosh paints them. Standalone GPU controls reproduce corruption in the shared GBM target while the internal target gives twelve exact cases including orientation. The private-target Phoc package is now device-accepted: clear upright Horloges/Fichiers previews plus responsive overview, app activation and horizontal favorite drag. Its running binary is verified and the complete-image Phoc pin updated. GLES2, the same temporary kernel and the published battery profile are preserved; no full image was rebuilt. See [evidence and limits](../validation/lmi-thumbnail-private-target-2026-10-24.md).

## October 24 follow-up: quiet battery comparison remains pending

The temporary old-kernel/intended-profile boot completed a normal deep-sleep diagnostic (295.868715303 seconds), awakened only by USB. The prior 14-second RTC-interrupted counter window is not a valid long-suspend comparison; the RTC diagnostic recorded no battery counter endpoints. No battery fix or calibrated current is established. See [window and RTC follow-up](../validation/lmi-fg-dt-order-window-2026-10-24.md).

Installed Phoc +thumblinear1 still shows striped app cards. The thumbnail-only row-readback candidate was built, activated, visually rejected and rolled back; see [actual outcome](../../userspace/phosh/thumbnail-row-readback-candidate/README.md). A temporary pixman diagnostic was unusably slow and pixel-inconclusive; GLES2 is restored and its runtime override is removed. The same temporary kernel/profile were preserved. No kernel/full image build or pin promotion. The next passive measurement remains planned for tonight.

The qualified menu startup reference remains unchanged. Offline replay of its exact Mobian DTB shows that the old FG name lookup reaches the vendor container rather than the intended SOC profile container. A separate order-only diagnostic image (7425c00b...) has now temporarily started Mobian on the original October7 kernel and published the intended j11sun/design4700000 profile. UI acceptance and battery observation remain pending; no battery-current cause is established. The candidate is not permanently installed, its output paths are isolated, and the qualified reference image remains unchanged. See [the evidence and limits](../validation/lmi-fg-profile-dt-order-2026-10-24.md).

## Current permanent dualboot reference — October 23, 2026

## October 23: locked power menu package update

The installed Phosh/common pair is now homedrag8. Its 36 package tests,
locked power-menu confirmation and operator-requested restart are validated.
The next complete build selects this pair; the existing installed rootfs and
boot/menu artifacts are unchanged. See
[the validation record](../validation/lmi-locked-power-menu-2026-10-23.md).


The permanent four-entry menu has passed temporary Mobian/LineageOS/Fastboot/
Recovery trials; persistent Mobian startup and boot-prefix readback are verified.
The qualified artifact identities and retention rules are recorded in
docs/maintenance/ARTIFACT-RETENTION.md. The current menu-only recipe is
build/boot-menu/external-mobian/build-external.py; the pinned operator installer
is build/boot-menu/permanent/manage.py. Older chronological entries below
describe superseded experiments and are not the current installation procedure.

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

# Current validated build and userspace state

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


## October 21: dual-boot build candidate prepared, not installed

The operator requested a fresh complete image rather than a live-system backup.
The [dual-boot candidate](../../build/dualboot/README.md) reuses the current RPMh
kernel and DTB, with a narrowly changed initramfs discovery function restricted
to a proposed dedicated 16 GiB `mobian` partition. The full-image entry point
retains the qualified homedrag7/Phoc/GSD/application layers. Fourteen host tests,
fifteen existing staging tests and installer dependency staging pass.

No full image or kernel build, repartition, format, flash, reboot or Android
installation was performed for this preparation. The existing Mobian remains
the installed reference. The GPT proposal is text-only and requires fresh
recovery qualification before migration. The Windows OS-selection controller
is mocked-test-qualified only and locked until both actual OS boots/accesses
are validated. Initial selection uses a connected PC/Fastboot, not an on-phone
boot menu. There is no demonstrated battery saving from this design.


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


## Next complete-image preparation — 2026-10-18

The operator requested native favorite drag ordering and application shortcuts
placed in the unused home area. A [native candidate](../../userspace/phosh/home-drag-candidate/README.md)
is prepared against the retained quiet-gauge v3 source, with pinned inputs.
Order/placement logic tests, syntax-only checks of both modified C translation
units using the retained ARM build environment, and strict schema validation
passed. The operator-run package build is the next gate; no native drag feature
is installed or hardware-qualified. The existing resource-only dock stays active.

The next full image must also address the missing camera. Package inspection
confirms the usual checklist applications are installed, but `gnome-snapshot`
and its diagnostic rear-camera bridge are absent. The retained camera path
requires backend/lifecycle integration, not merely adding the package or icon.
The previous private accepted-trial sources/binaries were located; no new
acquisition or recording was started. The combined recipe is now prepared; compilation and post-flash qualification remain pending.

## Post-flash home navigation adaptation — 2026-10-18

The handset now uses a scoped resource-only favorites-home/application-drawer
overlay. The operator validated opening the drawer and launching/closing a
favorite. Favorites were then bottom-aligned and the chevron moved below them
at the operator's request; final placement was verified by a native Phosh screenshot.
All applications are enabled and the adaptive-only button is natively hidden.
The active Phosh environment retains its quiet-gauge opt-in.

The installed UI adaptation is persistent and its trial rollback timer stopped.
Sources/defaults are staged by the next-image profile, but the flashed r1
image predates them. No kernel/package build, new flash or post-UI battery
qualification was performed. See the [application checklist](../validation/lmi-app-checklist-2026-10-03.md).

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

## October 18 build interruption

The first current-image attempt stopped before image generation. Its fresh M0
rootfs had no `mobian` account, while optional Chatty integration required that
account before the builder created it. No raw or sparse image was produced.
Account creation/group setup now precedes optional app integration; the app
staging check also rejects the wrong order. The next full build remains
operator-run. This correction does not change the phone or kernel.

## Current image rebuild preparation — 2026-10-18

The operator restored the retained October 9 userdata and the existing RPMh
boot after LineageOS October 7 (no OTA). The retained v3 Phosh/GSD pair and
production opt-ins were reinstalled; both live service environments were
verified without debug. The suspend-only NPU hook was restored with original
awake bandwidth policy. The operator confirmed normal interface interaction.
No new battery result follows from this restoration.

The current-image profile now reuses the complete shared Chatty installer,
retaining its daemon autostart mask and desktop activation guard instead of
partially overwriting them. Nine profile staging/rejection tests pass. The
original paired Android reports match the hashes retained with the October 9
image. The next userdata build remains operator-run; it has not yet been
built, flashed or hardware-qualified. The existing RPMh kernel is reused.


## Source recovery boundary — 2026-10-14

The [cumulative quiet-gauge v3 source patches](../../userspace/power/quiet-gauge-v3/README.md)
now recover both qualified source files directly from pinned Debian baselines.
Twelve source preparation/rejection checks passed, and output hashes match the
retained ARM build trees. Image-profile v3 package pins are unchanged. No new
image/package build, handset deployment or battery-saving result is claimed.

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


This document distinguishes the validated Mobian userdata family from the
separate D-v43/OpenRC reconstruction and from temporary diagnostic boots.
Generated images are not stored in Git.

## Historical installed userspace — 2026-10-11

The handset runs Mobian again after the Android comparison. Its installed
Phosh0.46.0-3+deb13u1+lmigaugewake2 and GSD48.1-1+lmiquietgauge1 packages now
retain screen blanking during the two observed gauge-only wakes and release
the Phosh delay inhibitor before resuspension. Persistent service opt-ins
are enabled without debug environments. The same installed kernel and NPU
suspend policy were retained; no new boot was built or flashed for this fix.

This is a qualified installed-userspace change, not a new golden image or
bit-for-bit image reconstruction. The artifact identities below are historical
validation records. The current image recipe now stages these exact packages and service opt-ins
with nine host preflight/rejection checks. No new image has been built or
tested for this integration; sustained autonomy remains unqualified; see the [power record](../../kernel/diagnostics/power/README.md).

## Golden-family hardware validation

The `archi-validation-02` Debian 13/Mobian userdata was booted on Xiaomi
`lmi` with the D-repro D-v43 boot. Phosh was visible and usable; touch/unlock,
DSI-1, and GLES2 → Zink → Vulkan Turnip → KGSL → Adreno 650 were validated.
GNOME Console and Calculator were exercised. The original D-repro boot
(`D-repro-01-kernel-Dv43-qca6390-v2-complete-fcsource-boot.img`, SHA-256
`0b6c7d88b3068ae4e3d106fd4b15a1a79bf00c3e576be7b3fcd8ab62faed73ad`) is
the durable boot identity for the golden and `daily-base` validations. The
boot image embedded in userdata is a distinct artifact.

## Golden userdata: `archi-validation-02`

The external raw and Android-sparse images were verified as a matching pair:

| Form | Size | SHA-256 |
| --- | ---: | --- |
| Raw `archi-validation-02.img` | 4,551,868,416 bytes | `329e2124f97032a2f4b15167bbd9bbbd9395bb422f2794a2117ee610a2368f27` |
| Sparse `archi-validation-02.img.android-sparse.img` | 2,960,036,280 bytes | `84182b57edb7be8e49c29e0f0b472e9b6a54f7efa645ef99664dc0e004759f78` |

The sparse image was flashed as userdata and booted with the D-repro boot.
The text lock records its packages, persistent customizations, GPU72 runtime
and boot/userspace contract at
[`build/locks/userspace/`](../../build/locks/userspace/README.md).
The golden is not in Git. A bit-for-bit rebuild from all historical sources
is not demonstrated.

## Derived profile: `daily-base`

`daily-base` was derived from the golden userdata without rebuilding the
kernel. It adds the validated time-seed floor and a per-user XDG override
that disables only automatic Chatty-daemon startup; Chatty remains installed
and manually launchable.

| Form | Size | SHA-256 |
| --- | ---: | --- |
| Raw `archi-validation-02-derived-daily-base-20260927.img` | 4,551,868,416 bytes | `5cc226cd96c324b68d74e33eec461a091e7f5dd69b80e0529c2d0267cfa3cad5` |
| Sparse `archi-validation-02-derived-daily-base-20260927.img.android-sparse.img` | 2,960,466,444 bytes | `172a4f950252e810f408bf4d5caf5075c699020e6a2198999f7f0b30c7f19928` |

The raw/sparse round trip and hardware boot were validated. The images remain
external. See
[`daily-base` validation](../validation/archi-validation-02-daily-base-validation-2026-09-27.md).

## Experimental profile: `daily-base-audio-fw-test`

This separate experimental derivative adds the proprietary TFA9874 container
to the kernel's active firmware lookup path. It was tested with a distinct
reset-GPIO diagnostic boot loaded temporarily using `fastboot boot`; that
boot was not installed durably. The firmware binary, userdata and diagnostic
boot remain external and must never be added to Git.

The WCD938x/TFA9874 path now supports clear speaker music through direct
S32_LE ALSA and an installed opt-in PipeWire route (2026-10-03). A complete
UCM2 profile and headset/earpiece validation remain pending; microphone
capture and KRecorder saving were subsequently tested on 2026-10-04; see
[`archi-validation-02` audio progress](../validation/archi-validation-02-audio-progress-2026-09-29.md).

## Earlier build: `archi-validation-01` (superseded as current pointer)

The prior Android-sparse build remains a historical artifact identity, not
the current golden:

| Artifact | Size | SHA-256 |
| --- | ---: | --- |
| Work ext4 | 4,294,967,296 bytes | `60de98660991379cb1d463ebadc7de43b73242d68f73502308e3891d2350844d` |
| Raw userdata | 4,551,868,416 bytes | `559d6c44f2aa2223f91fd8af1db7a838b8183d7a223ceb80f7bdd13a9b6e31e4` |
| Android sparse userdata | 2,834,813,356 bytes | `f61c19a09881c9a7ac165cc5e36ab08f146d65acddae2de18a6bb555c10663b3` |

Its two `e2fsck` validation passes completed cleanly. It is superseded as the
current userspace reference by `archi-validation-02` and its validated
`daily-base` derivative.

## Build entry points

Repository orchestrator:

    build/build-mobian-image.sh

Current Phosh/userspace builder:

    userspace/phosh/scripts/build-m1-phosh.sh

Optional application installer:

    userspace/apps/scripts/install.sh

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
- gnome-calendar
- gnome-maps
- geary
- amberol
- krecorder
- koko

## GPU source state

The active GPU72 runtime is stored under:

    userspace/gpu/files/gpu72/

Its canonical source provenance is documented in:

    userspace/gpu/files/gpu72/SOURCE-PROVENANCE.md

The validated source reconstruction is upstream Mesa 25.0.7 plus the canonical
GPU72 patch.

## Important separation of concerns

The current M0/base-rootfs chain, current Phosh/userspace chain and kernel
build are separate.

The separate Mobian device workflow is not a replacement for the current
`userspace/phosh/scripts/build-m1-phosh.sh` image-production chain.

## Known deferred work

The following remain separate deferred items:

- full UCM2 routing, headset/earpiece and durable audio-boot deployment
- camera configuration and a usable downstream capture pipeline

The historical M0 Weston display validation and the later D-v43/OpenRC Weston
failures are different environments and must not be conflated.

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
Allumer and Éteindre buttons were operator-confirmed. Camera capture was
blocked at this milestone; later rear-camera diagnostic progress is recorded
in the [camera record](../../userspace/camera/README.md). These are live-phone
customizations, not newly locked golden images.
See the [validation record](../validation/lmi-battery-audio-torch-2026-10-03.md).

## Next-build multilingual baseline — prepared 2026-10-03

The M1 recipe now includes core/CJK/emoji Noto fonts and all Debian locales
without requiring optional apps. Initial interface locale and XKB layout are
build parameters. Korean-interface/Turkish-document rendering is an intended
validation scenario, not yet an image/hardware result. No new image was built
and the battery-test phone was not changed. See the Phosh recipe README for
remaining input-method, runtime language selection and translation limits.

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

## Runtime audio checkpoint — 2026-10-04

The inspected phone runtime exposed no ALSA card. The earlier speaker result
remains specific to the temporary diagnostic boot. Its installed opt-in
PipeWire adapter now tolerates a missing card, allowing the server to start;
Dummy Output is not physical audio. Diagnostic-boot speaker and microphone
retesting is pending. See the [application checklist](../validation/lmi-app-checklist-2026-10-03.md).

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
The subsequent approximate powered-off comparison returned at the same 88%
reported charge. Charging and boot/Fastboot intervals were not quantified, so
this does not establish zero off-state drain or physical battery health. No
autonomy fix is established.
See the power diagnostic record for return-measurement and kernel-identity limits.

The next-build optional application recipe no longer installs the abandoned
Megapixels package. Snapshot is still a separately tested diagnostic application,
not a production camera replacement in this recipe. No image was rebuilt and
no live-phone package was changed by this recipe correction.

M1 now stages the Recorder launch wrapper required by the optional-app installer.
A host-only dependency-closure check first reproduced the missing-file failure,
then passed all seven staged app inputs after the correction. No image or live
phone was changed. The checker is under `userspace/apps/scripts/`.


### Persistent diagnostic baseline installed — 2026-10-07

The operator selected the existing reviewed RPMh observer image for persistent
boot installation, avoiding another build/version. Its 54,652,928-byte artifact
hash is `a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50`.
The operator flashed only `boot` and rebooted successfully. Post-reboot
verification confirms that its image-size prefix matches the selected RPMh
image, the running banner is dated 2026-10-07 05:27:54 UTC, and IKCONFIG SHA-256
is `c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78`.
All 47 RPMh observer attributes are present; USB charging and CPU idle work.
The gauge recognizes `j11sun_4700mah`, with design 4,700 mAh and learned full
2,822 mAh. This is not a new autonomy validation. Display/touch confirmation
remains an operator check. The original D-repro remains the rollback image. The newly prepared guarded FG observer and lookup/retry fixes are
excluded from this chosen image and must not be reported as active. See the
[power protocol](../../kernel/diagnostics/power/README.md#reuse-of-the-existing-reviewed-kernel--2026-10-07).


### Persistent-kernel overnight result — 2026-10-08

The first return after the night reported 69% versus the previous plugged-in
100% baseline. Running and installed RPMh kernel identity remained confirmed,
with no intervening restart supported by boot-time progression. The journal
records 96.808% deep suspend between the first and last overnight suspend
markers, with 61 `msoc-delta` and one `msoc-high` wake reports. Approximate
counter-derived consumption is 94.089 mA over 8.666782 hours between readings;
charging at both ends and the unknown exact unplug time prevent treating this
as a controlled current measurement. No autonomy fix is established. See the
[power record](../../kernel/diagnostics/power/README.md#overnight-return-on-the-persistent-rpmh-baseline--2026-10-08).


### Test handset temporarily switched to LineageOS — 2026-10-08

The operator installed official LineageOS 23.2-20261007-NIGHTLY-lmi, Android 16,
for an idle-drain comparison. The ZIP SHA-256 is
`c182c6f8ed1ccb1821be38e764e189f3d58f65dd9bea8aa21f1381c791395a29`;
the matching recovery SHA-256 is
`211cdc50ae40a9ecbcc35fa91ee81a54fcb02af7b49b77e8623a357f9984f7b3`.
Both downloaded files were verified. The operator explicitly chose installation
without a snapshot of the current Mobian runtime. The installer replaces boot,
Android dynamic partitions, dtbo and vbmeta images; the earlier permanently
installed RPMh image is no longer the running test-handset kernel. Existing
Mobian artifacts and Git history remain available, but exact runtime restoration
has not been established. No new Mobian image was built.

The first short Android idle comparison suggests lower drain but is preliminary.
See the [single power decision summary](../../kernel/diagnostics/power/README.md#current-decision-summary--2026-10-09)
for grouped results and the distinction between charging return samples and
pre-charge battery-history events. The longer Android interval is complete: 29 min 41 s on battery, displayed
83% unchanged before charge, about 98.5% system suspend and 5.35 mAh summed
gauge decreases reported by Android. An upward gauge correction prevents a
reliable net endpoint-current estimate. This supports lower apparent Android
idle drain, not a physical battery-health verdict. Radios are restored and the
one-shot reminder is paused. Detailed logs remain private.


### LineageOS overnight comparison completed — 2026-10-09

The same-boot, radios-off overnight interval lasted 8 h 37 min, with displayed
charge falling from 100% to 91% before reconnect. Pre-charge history gives
283 mAh net loss (about 32.8 mA); Android's sum-of-decreases statistic gives
289 mAh (about 33.5 mA). Upward gauge corrections, cooling and baseline timing
limits remain explicit in the [single power decision record](../../kernel/diagnostics/power/README.md#completed-android-overnight-result--2026-10-09).
About 99.54% system-suspend occupancy and lower apparent drain than historical
Mobian trials are supported, without a physical battery-health verdict or an
identified autonomy fix. The finite collector completed, its private data was
retrieved, and original radios were restored. The handset remains on LineageOS;
no Mobian build, restoration or new kernel was performed.

The hourly review refines this overnight result: approximately 71% of net
counter loss occurs in the first two hours, with about 12.4 mA net gauge
accounting over the remaining 6 h 37 min. This is not uniform physical idle
current. See the [counter interpretation and limits](../../kernel/diagnostics/power/README.md#overnight-discharge-is-not-uniform).
The subsequent operator-requested comparison completed after 13 h 29 min.
No periodic diagnostic logger was used.

### LineageOS daytime comparison completed — 2026-10-09

The same-boot, radios-off interval lasted 13 h 29 min, with displayed level
100% to 94% before charging. Net rounded gauge loss is 150 mAh (~11.1 mA);
Android counts 188 mAh decreases (~13.9 mA), with positive corrections retained.
System-suspend accounting is about 99.62%. Original radio settings were
restored and verified. This reinforces lower apparent Android idle drain,
without a physical cell-health verdict or a demonstrated Mobian fix. See the
[single power decision record](../../kernel/diagnostics/power/README.md#completed-android-daytime-result--2026-10-09).
The handset remains on LineageOS; no Mobian restoration or new build occurred.

### Return-to-Mobian mount prerequisite — 2026-10-09

LineageOS changed the dynamic vendor partition offset and uses EROFS. The
retained Mobian kernel already supports EROFS, but the historical fixed vendor
offset is incompatible with the inspected current layout. A guarded,
[text-only candidate preparer](../../userspace/wifi/diagnostics/README.md)
and nine synthetic tests are now available. A private candidate passes shell
syntax validation; no candidate was installed and no image was built.
Runtime vendor/APEX compatibility and actual Mobian startup remain pending.
This storage compatibility gate is separate from the battery investigation.
Existing sparse userdata and RPMh boot were located; returning to that older
userdata would not restore the latest live application fixes automatically.
The running handset remains on LineageOS until the operator chooses a reviewed
return procedure. No partition write or new kernel is part of this preparation.

### Current-recipe return build prepared — 2026-10-09

The operator selected rebuilding userspace from current sources rather than
reusing the September audio sparse image. The preserved M0 raw's prefix and
M0 DISPLAY ext4 filesystem identity were verified locally. The
[read-only M0-input wrapper](../../userspace/phosh/README.md#operator-run-build-from-the-preserved-m0-filesystem)
feeds the current Phosh recipe without needing an old extracted working tree.
Paired current Android reports are an explicit input for generated mount
parameters; no historical source or lock is silently replaced. Static shell
checks and nine metadata guards pass. No actual build, flash or runtime
validation has occurred. Reuse the existing RPMh kernel; selected external
power/audio/camera runtime layers remain separate from the generic build.

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
