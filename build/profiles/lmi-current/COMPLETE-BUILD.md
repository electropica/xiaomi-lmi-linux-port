# Complete operator image — 2026-10-18

`build/build-complete-lmi.sh BASE_RAW M0_EXT4 OUTPUT_NAME` is the combined
operator-run entry point. Run as root in a private mount namespace, with the
same external base, preserved M0, paired Android partition reports, SSH public
key and interactively supplied Mobian password as the current image recipe.
It performs no phone operation, flash or kernel build.

Additional external inputs:

- `M1_CURRENT_LMI_PROFILE_INPUTS`: the verified stable eight-file package and
  firmware input manifest used by the previous image.
- `M1_CAMERA_ANDROID_LIBCXX`: the matching external Android system libc++.so
  needed to link the OEM QTI bridge; never add this library to Git.
- Existing ARM build root `/home/linuxagent/phosh-gauge-wake-build/rootfs`
  containing quiet-gauge v3 sources, build dependencies and generated Wayland
  protocol sources; the native drag candidate checks its source identities.
- Android NDK r27d (default retained toolchain path, optionally
  `M1_ANDROID_TOOLCHAIN`).

The command builds Phosh/common
`0.46.0-3+deb13u1+lmigaugewake3+homedrag1`, compiles the Snapshot rear-camera
bundle, creates a separate private eight-input manifest, then runs the full
userspace/image builder. Package dependencies are installed noninteractively.
It retains normal optional applications and their scoped fixes, audio,
Recorder, torch, Chatty guards, fonts/locales, quiet-gauge v3 GSD/Phosh,
UPower, CPU-idle, suspend-only NPU policy, clock floor and current Android
mount layout. The already installed RPMh kernel is reused.

The candidate owns its matching UI/schema: bottom favorites, chevron below,
separate all-app drawer, favorite drag ordering and sixteen persistent home
slots. The previous resource-only UI overlay is deliberately omitted, since
it lacks the widgets bound by the new C implementation. Global horizontal
minimization is not added.

Snapshot (`gnome-snapshot=48.0.1-1`) is installed together with the experimental
rear-only bridge and scoped rendering/audio tuning. Opening its desktop icon
starts the adapter; the root sensor service requires a recent foreground lease
from that launcher. Background/exit revokes the lease and stops the backend.
The service is not enabled at boot. No obsolete custom camera frontend,
Megapixels, test recording, private desktop database or personal media is added.
The bridge is specific to the preserved Android runtime and exact existing
kernel. It uses the accepted fixed-30 sensor request, NEON conversion and
40 ms native producer polling; these do not establish 720p/30 video output.

## Validation boundary

Source preparation, zero-fuzz patch application, ARM syntax checks, strict
schema checks and host order/placement tests passed. Stable-profile tests and
complete-profile staging tests verify exact package selection and rejection
of corrupted/missing bundles, wrong binary architecture and manifest paths.
Test fixtures are metadata only and are never used in the real image.

The first complete-build attempt stopped in the Phosh unit tests before
package generation. Its null app-info regression is fixed; all 36 Phosh tests
now pass after incremental recompilation/relinking. Restart the same operator
command. The complete package/image build is **not yet finished**. Native touchscreen drag
behavior and the newly combined Snapshot foreground/exit lifecycle require
post-flash tests. Prior camera trials establish a useful rear preview, not
front-camera, zoom/flash controls, reliable recording or improved autonomy.
The current working installation remains unchanged until the operator flashes
the completed image. Build success must include filesystem checks, sparse
roundtrip and the final `COMPLETE_IMAGE_WITH_NATIVE_HOME_AND_SNAPSHOT` marker.

Existing image output paths are refused. Finished package/bundle artifacts
can be reused after identity checks; partial camera preparation is reused only after matching every prepared
source/runtime asset against fresh preparation. Altered assets are refused. No cleanup or deletion is performed automatically.

The retained ARM chroot receives private proc/devpts mounts and a PTY probe
before camera compilation. Apt dependency installation is noninteractive with
PTY logging disabled. Native Phosh packages completed on the second operator
attempt and will be reused; the camera dependency step was interrupted and
has not yet produced a completed image.

## Operator build completed

The subsequent operator run finished successfully on 2026-10-18 with
`COMPLETE_IMAGE_WITH_NATIVE_HOME_AND_SNAPSHOT`. The 3,660,046,632-byte sparse
image has SHA-256
`67413598eab1cf646e9f8c22606aa29d33a52d8e9d37a933c2571e8cc97d7a85`.
Filesystem checks, raw/sparse comparison and offline package/profile inspection
passed. Post-flash touchscreen and camera lifecycle tests remain pending.
Earlier failure/recovery paragraphs above record preparation history.

## Next native drag repair

The built/flashed image above contains homedrag1. Its physical drag test
failed because the drawer remained visible. The recipe now selects homedrag2,
which automatically exposes the actual home drop cells. Host tests pass;
operator package build and physical retest remain pending. This does not
change the recorded identity of the already built image. A subsequent complete
image must use a new unused output name.


### Current next-build selection — 2026-10-18

The next complete recipe selects Phosh/common homedrag4 and Phoc
0.46.0-1+lmishelldnd1 together. Phoc DnD and the preceding homedrag3 removal,
compact labels, lateral preview/reorder and app-edge/drawer behavior are
operator-confirmed on the handset. Homedrag4 adds drawer-to-dock insertion up
to five favorites; its package and physical five-icon validation remain pending.
The input manifest now includes the Phoc package (nine total inputs); staging
rejects its absence. Stable non-complete image behavior remains unchanged.
The already-built complete image still contains homedrag1; it is not rewritten
by these recipe changes. No new image build is necessary to test the new pair.


The subsequent next-build selection is homedrag5 plus the same Phoc candidate.
Homedrag4 added the fifth favorite but exposed
right-edge clipping and intermittent shortcut-removal delay. The homedrag5
source follow-up removes cell theme padding and raises deferred removal to
normal main-loop priority. Its compiled geometry/busy-loop tests pass; package
and physical checks are pending. No existing image has been overwritten.


The latest next-build selection is homedrag6 with the same Phoc package.
Homedrag5's five-icon fit is physically confirmed. Homedrag6 changes cross-
surface copies into transfers between favorites and home, while drawer drags
continue to copy; grouped source/destination checks are tested. Its operator
package build and physical transfer checks remain pending.


Homedrag6 is now operator-built (36/36 package tests), installed and validated
for favorites → home → favorites transfer without retained source shortcuts.
The full-image recipe already includes that pair and Phoc lmishelldnd1; no
new image was generated by this package validation. See CURRENT-BUILD for
package hashes, remaining qualification boundaries and prior image identity.


The current next-build selection is homedrag8 plus the same Phoc package.
It adds a native Restart power-menu action; its source compiles, but the pair
build and physical menu/confirmation checks are pending. No restart was issued
while preparing it. The installed handset is still homedrag6.
