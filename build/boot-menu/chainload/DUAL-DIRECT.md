
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

# Experimental direct Mobian and Android menu

Android-only menu boot is hardware-qualified with the aligned Android OS header.
This new dual candidate is HOST-VALIDATED ONLY. It has not been compiled or
booted. Do not flash it or reuse an older candidate's Windows launcher.

## Change

`--with-dual` embeds both pinned boot component sets. Mobian now uses BOOT_LINUX,
not BOOT_REBOOT. The menu order remains Mobian, LineageOS, Fastboot, Recovery,
with Mobian selected after fifteen seconds. No disk configuration is imported.

The RAM bundle has nine components (116559872 bytes before FV compression).
Each OS uses its own unchanged kernel, initrd, DTB and command line. Android alone
receives the installed, board-matched DTBO and guarded removal of its obsolete
physical-partition DT fstab. Mobian's DT is not changed by that correction and
receives no Android overlay. Its pinned command line retains the installed
dedicated-partition boot/root UUIDs. No rootfs or kernel rebuild is needed.

The firmware reservation grows from 32 to 64 MiB at the same base 0xCE000000.
The immediately adjacent ordinary RAM region now starts at 0xD2000000 instead
of 0xD0000000 and shrinks by exactly 32 MiB, preserving its original end address.
No other map regions change. FDF and BootShim FD sizes match. This map change is
new and requires hardware qualification; host consistency does not prove boot.
The previously corrected PrePi large-file support is retained.

The outer boot header retains the pinned Android OS-version context required
by the successful Android trial. Every generated candidate records its hashes;
neither output nor manifest asserts hardware validation.

## Host validation, 2026-10-22

- Actual pinned inputs produce all nine components within the bundle budget.
- Actual C parser accepts all nine rows; invalid row count, duplicate names,
  malformed offsets, truncated input and oversized last-row length are rejected.
- Seventeen source edits apply and restore exactly. An altered reviewed file
  prevents all restoration, without partial writes.
- Firmware/RAM boundaries are contiguous and conserve the original region end.
- Four affected ARM64 C units pass syntax checking with generated build flags.
- C/libfdt tests on all three real Android DTBs with the lmi-matched overlay
  confirm the Android-only change, Mobian no-op and unknown-OS/path rejection.
- Shell and embedded Python syntax pass. No firmware compilation or phone
  boot was performed by the agent for this candidate.

## Operator build

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build --with-dual
```

Reuses the existing isolated compiler rootfs and pinned private inputs. Output:
`/home/linuxagent/lmi-boot-menu-build/output/boot-lmi-dual-test.img`,
`dual-artifact-manifest.json`, and `boot-os-version-manifest.json`.
Expected marker: `DUAL_DIRECT_RAM_HANDOFF_BUILD_COMPLETE_NOT_FOR_FLASHING`.
No ADB, Fastboot, formatting, partition operation or automatic installation.

After compilation, verify the actual FD layout, artifact hashes and manifest,
then prepare a hash-pinned Windows RAM launcher. Qualify Mobian first, including
its dedicated root filesystem, interface and return path, then Android. Keep
the installed Mobian boot as the fallback throughout these temporary trials.
Persistent installation requires a separate reviewed step after both pass.


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
