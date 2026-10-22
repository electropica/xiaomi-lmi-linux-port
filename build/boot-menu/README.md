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

# lmi handset boot-menu candidate

Dedicated recipe for the requested on-phone Android/Mobian menu: Mobian by
default after 15 seconds, without a PC once qualified and installed.

**Current status: Android boot from the temporary menu is hardware-qualified.
A direct Mobian + Android candidate passes host checks but needs an operator
build and temporary hardware trials. Persistent installation remains unvalidated.
See [DUAL-DIRECT.md](chainload/DUAL-DIRECT.md).**

## First build: display, input and countdown

From WSL, with the existing mmdebstrap and unshare tools:

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build
```

The script creates a separate Debian bookworm amd64 rootfs at
`/home/linuxagent/lmi-boot-menu-build/rootfs`. Bookworm provides Python 3.11
with distutils and Clang 14; the WSL host currently has Python 3.14 / Clang 21,
which are not a suitable assumed baseline for these older sources. Dependencies
are installed inside that rootfs, not into the existing Phosh or kernel builds.
Debian packages are not snapshot-pinned; record build.log and the final manifest.
Only Git source revisions are locked. No bit-for-bit reproducibility claim.

Source fetching and compilation occur only when the operator runs the command.
The build never invokes ADB/Fastboot or generates an installer ZIP. It uses a
private mount namespace with /dev including devpts; mounts disappear on exit.
The recipe is bound read-only. A failed bootstrap is preserved for inspection,
not automatically deleted. There is one source tree and one output directory.

Expected output:

```
/home/linuxagent/lmi-boot-menu-build/output/boot-lmi.img
/home/linuxagent/lmi-boot-menu-build/output/artifact-manifest.json
/home/linuxagent/lmi-boot-menu-build/output/build.log
```

After successful build, review the manifest and copy the image to Windows
Downloads. The first handset operation must be **temporary fastboot boot**, from
Windows, after product/hash verification. Do not flash this probe: its Mobian
entry cold-reboots the currently installed boot partition. Installing the probe
there would create a reboot loop. This folder intentionally has no flash helper.

The first menu offers:

- Mobian (restart installed OS), selected by default after 15 seconds.
- Fastboot.
- Lineage recovery.

This validates the UEFI display/input/countdown path and the reset handoff, not
Android chainloading. Android is not presented as a working choice. Touch or
selection may cancel the upstream automatic countdown; test the untouched case
separately. An unexpected black screen is a failed probe, not a reason to flash.

The probe bypasses on-disk SimpleInit config loading and persistence, installs
only explicit menu entries, and skips OS probing. Existing configs therefore
cannot override Mobian default via boot.current. It retains the upstream lmi BSP
unchanged, including its alioth ButtonsDxe/ACPI references; these are an explicit
hardware qualification concern, not evidence that alioth and lmi are identical.

## Why a direct two-image configuration is not ready

Both exact qualified OS boot images use Android header v2. The pinned SimpleInit
aboot reader consumes kernel/ramdisk/second only and does not handle the v2 DTB
field. Passing boot.img to it is not equivalent to ABL/Fastboot booting that
image. The wrapper version of the UEFI image is a separate issue: upstream lmi
uses header v1. Display, buttons, DTB/DTBO choice and downstream handoff all need
actual target validation. Kexec is absent from the current Mobian kernel.

`extract-payloads.py` validates both pinned original image hashes and strictly
extracts their kernel, ramdisk, DTB and complete command line. It changes no boot
image or target storage. Use a NEW private output directory:

```bash
python3 build/boot-menu/extract-payloads.py \
  --mobian /path/to/mobian-lmi-dualboot-boot-20261021.img \
  --android /path/to/boot.img --output /path/to/private-components
```

The next candidate should carry both sets of components in a RAM-backed FAT
asset volume exposed to UEFI, rather than rely on Android userdata decryption or
repartition again. This is a design to implement, not an installed mechanism.
Image padding need not be copied, but actual payload totals, FAT overhead,
UEFI wrapper size and allocation limits must be checked against the 128 MiB boot
partition before any persistence proposal. No DTB/DTBO index is guessed here.

## Qualification gates

1. Build success and pinned artifact identity.
2. Temporary boot: readable menu, working selection, untouched 15-second timeout,
   default return to Mobian, independent Fastboot/recovery rescue.
3. Implement RAM asset registration and explicit kernel/initrd/DTB handoff;
   preserve command lines, qualify Android DTBO selection and downstream reset.
4. Temporarily boot both OSes repeatedly, verify dedicated Mobian root and full
   Android access, hardware functionality and unchanged rescue access.
5. Only then prepare the persistent image, default policy and guarded installation.

The existing PC RAM-boot selector remains the working switching method meanwhile.
This recipe does not alter the installed boot, recovery, ABL, XBL or GPT.

## Source provenance

- [EDK2-MSM](https://github.com/edk2-porting/edk2-msm/tree/e1952621f419f8db60ed28271264e1b5184c571d),
  including configs/devices/lmi.conf, Platform/Xiaomi/sm8250/lmi.dsc,
  lmi.fdf.inc and Silicon/platform.sh.inc.
- [Pinned SimpleInit](https://github.com/BigfootACA/simple-init/tree/29e062805776db5ab7a61d07ef040d43aed71161),
  especially src/main/uefimain.c, src/gui/interface/core/bootmenu.c,
  src/lib/aboot.c, src/linux-boot/aboot.c and src/confd/uefi.c.

All direct submodules are recorded in sources.lock.json, fetched at gitlinks,
never updated with --remote. Proprietary upstream EFI binaries stay in the local
ignored external build directory; do not add them or generated images to Git.

## First operator build result

The October 21 operator build completed using Debian Clang 14.0.6 / Python
3.11.2. boot-lmi.img is 7059456 bytes, SHA256
f39e2c65a434a90ae3d8a11cfa2b40e6113f6eee27eb6e73bd5b54cdcbd713a1.
The image and source-patch manifest were independently re-read. The compact
firmware volume fits its 7 MiB region; linker RWX warnings did not abort the
build. This is build evidence, not proof that the target firmware runs.

The exact image was transferred to Windows Downloads as
`lmi-menu-smoke-20261021.img` and hash-verified. `test-menu-windows.py` defaults
to a host-only plan; `--execute` qualifies the existing dedicated Mobian endpoint
and installed RPMh boot prefix, reboots to Fastboot, checks lmi/partition size
and requests only a temporary boot. It contains no flash command. Run it from
Windows, not inside WSL. The observed installed RPMh boot remains unchanged;
return through its normal cold-boot path has not yet been observed after migration.

During the first probe, leave the screen untouched to evaluate the countdown.
Then report whether the menu appeared and whether Mobian returned. If the
screen remains black, do not keep retrying or flash the probe: return to
Fastboot and temporarily boot the already qualified dedicated Mobian image.

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

## Next candidate: LineageOS

Revision 2 automatic return after 15 seconds is operator-confirmed and backed
by SSH dedicated-root checks. See [LineageOS candidate](chainload/README.md) for
the next explicit build command, implementation and pending hardware gates.
