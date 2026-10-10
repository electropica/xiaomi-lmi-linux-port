# Integrated current lmi image profile

Use `build/build-current-lmi.sh` for the current operator image. It selects
the existing Phosh builder and installs this profile **inside the image
before filesystem and sparse-image generation**. No post-flash patch sequence
is required for the components listed below. Heavy image builds remain
operator-run. The generic/historical builder remains available separately.

## Included components

- Current optional applications and the Photos, Text Editor, Calculator,
  Contacts and Recorder launchers; fonts and locale coverage from Phosh.
- Torch application and the bounded Chatty launcher with its private plugin
  view, desktop and D-Bus overrides. SMS/MMS service is not thereby validated.
- Stock Venus firmware references prepared after the read-only firmware mount,
  before Phosh. Metadata and split-segment lengths are checked before creating
  links. Existing differing destinations are refused. This enables codec open,
  not a claim of validated encode/decode streams or a camera-ready image.
- Previously validated ALSA/PipeWire speaker and microphone routes, generic
  TFA container, and Recorder format preferences.
- Previously validated patched UPower battery-status opt-in, CPU-idle
  opt-in for the existing kernel release, and battery-only suspend after
  900 seconds; no automatic suspend while connected to AC.
- Selected timezone and timesyncd, plus the existing time-seed clock floor
  initialized at build time and saved periodically and at orderly shutdown.
  This prevents regression below the saved epoch without writing the hardware
  RTC; it does not replace NTP or account for time spent powered off. Current Android
  system/vendor mount layout generated from paired external metadata reports.

These changes were validated separately on the previous phone installation.
Their integration in this fresh image is host-checked, not a replacement for
post-flash hardware validation. The current LineageOS vendor/runtime ABI
also requires post-boot verification. High idle consumption is **not fixed**
by the status-reporting patch; see `kernel/diagnostics/power/README.md`.

The experimental Snapshot camera bridge is not production-integrated here.
No obsolete custom camera frontend or Megapixels is installed. Avoid claiming
that the camera is ready solely because other applications are included.

## External inputs and one build entry point

Set `M1_CURRENT_LMI_PROFILE_INPUTS` to a private directory containing:

- `upower_1.90.9-1+lmi1_arm64.deb`
- `libupower-glib3_1.90.9-1+lmi1_arm64.deb`
- `gir1.2-upowerglib-1.0_1.90.9-1+lmi1_arm64.deb`
- `tfa98xx.cnt`, SHA256
  `07abfca151aaa296595fff35d53c2aa2999e7d16cdc373ade2fd5954ff90c9a9`
- `SHA256SUMS` containing exactly those four files and their recorded sums.

The package binaries are outputs of the existing UPower package recipe;
they are not committed. Preflight checks package name/version/architecture,
firmware identity and the private checksum manifest before rootfs work.
The runtime profile rechecks the inputs and installed package versions.
Recorder preferences are guarded by the tested `krecorder=25.04.0-2` version.
These version checks fail the build rather than silently applying an old
workaround to changed software.

Set `M1_ANDROID_SUPER_REPORTS_DIR`, `M1_SSH_PUBLIC_KEY_FILE` and
`M1_MOBIAN_PASSWORD` as for the preserved-M0 builder. `M1_TIMEZONE` defaults
to `Europe/Paris`; `M1_LOCALE` and `M1_XKB_LAYOUT` retain their existing controls.
Run the single entry point with the same three arguments:
`BASE_RAW M0_EXT4 OUTPUT_NAME`, as root in a private mount namespace.
The output name must be unused. The script does not delete previous images.

Reuse the already-built RPMh/reset-GPIO boot with SHA256
`a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50`.
This is a userdata image build; it does not build or flash a kernel.
Firmware, packages, personal files and recordings remain outside Git.

## Verification

`python3 build/profiles/lmi-current/test-stage.py INPUTS_DIRECTORY` tests
real input staging, missing inputs, corrupt firmware, incorrect manifests,
existing-output preservation and package-symlink rejection without building
an image. The image builder also audits Debian package state, compiles schemas,
checks the selected battery suspend action and retains its ext4/GPT/sparse
roundtrip checks. No services, camera or microphone are started by the profile.


## Old-kernel metadata-indexer guard

The profile masks the global user unit `localsearch-3.service`. On the current
4.19 kernel its extractor cannot enable Landlock, and PIDFD child-watch errors
were observed with 28609 unreaped children. Stopping the indexer restored user
thread creation on the handset. No indexing database or personal file is
removed. Background metadata/full-text indexing is unavailable while masked;
ordinary file browsing is retained. This guard is not an autonomy-fix claim.
The recipe change has shell validation, but no new image build or reboot test.


### Suspend-only NPU bandwidth policy (2026-10-10)

The profile stages the helper, sleep hook and independent ExecStopPost recovery
from [userspace/power](../../../userspace/power/README.md#suspend-only-npu-bandwidth-policy-2026-10-10),
and enables its opt-in marker. Exact kernel/build guards keep this scoped to
the reviewed RPMh/reset-GPIO boot. Generic builds are unaffected. Production
hook passed an attended sleep cycle at 49.593 mA from the gauge, with original
policy restored. Automatic multi-cycle/night-long validation remains pending.
No new image or kernel build was run.
