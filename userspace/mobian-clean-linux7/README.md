# Experimental clean Mobian rootfs for lmi

Work in progress, not an installable or hardware-validated image. The recipe
is documented for review while an operator-run build is in progress. It is
not a replacement for the installed system or its recovery images.

The recipe installs the project's custom packages, stages hardware assets,
and includes the staging-directory and file-mode fixes found during the
first build attempts. Phoc's DSI-1 output is configured at scale 3. The
operator builds on a case-sensitive Linux filesystem, not `/mnt/c`.

The custom Debian packages, GPU stack, firmware, user data, credentials and
backups are intentionally absent. The recipe cannot run from this public
tree alone; private inputs must be supplied and verified separately. Package
holds and pinned versions need a security update strategy. Post-boot account
provisioning, selective user-data restoration and full device verification
remain open. The sparse verifier has negative synthetic tests only. No flash
or partition replacement is authorized by this recipe.

The November 4 operator run successfully produced an experimental rootfs.
For WSL, build on the Linux filesystem: `/mnt/c` may conflate case-distinct
filenames. Debos runtime staging uses `/var/lib/lmi-image-staging`, whose
parent is created first, and executable scripts retain their modes. The image
verifier uses a read-only loop rather than copying a 16 GiB filesystem to
WSL's small `/tmp` tmpfs. Rootfs and raw image checks passed off device; the
new rootfs has not yet been qualified through a real boot.

## Suspend refusal fix and USB guard

The clean Linux 7 recipe requires the `+sleeprefusal1` GSD runtime and common packages. Stage the two matching Debian packages alongside the other custom packages and regenerate the staging `SHA256SUMS` before building. The image installer and verifier reject older GSD versions. The package payloads are external build inputs and must not be committed to Git.

The image includes and enables `lmi-usb-pc-guard`; its overlay matches the guard observed on the handset on 15 November (SHA-256 `5b1e50e75f6692ac8e2d3d9b291ab310d09a7d1dfd9b3bb8d7ec29d576495a9f`). It blocks system suspend while the maintenance USB connection is detected; verify inhibitor release and automatic suspend on battery in a supervised test. The GSD refusal callback was observed, but the full retry sequence after a refusal remains unvalidated.

The historical quiet-gauge wake filters are not enabled by this change. The current kernel does not expose the expected `last_resume_reason` interface and the relevant opt-ins were absent in the observed processes. Their package names alone do not establish active wake filtering. Do not suppress unrelated input or calls as a substitute.

The image configures `CHASSIS=handset` in `/etc/machine-info` and verifies it. GSD disables its desktop automatic-suspend warning for handset chassis; on 15 November the handset had an unset chassis and GSD warnings coincided with repeated display wakeups. After restoring handset chassis, a battery test on 15 November showed no recurring GSD warning or DSI modeset before successful automatic s2idle after about five minutes. The test does not establish that every unsolicited screen wake is fixed: the installed logger reported the screen on at two sampled moments before suspend, and its exact source-to-binary identity was not independently established.

The GeoClue BSS reseed helper counts its two-second sleeps in seconds and has a 300-second systemd startup limit. On 15 November the previous helper exceeded its 180-second limit because each 90-second loop could actually wait 180 seconds. The corrected helper completed successfully in about 91 seconds with no empty-BSS error observed; this validates the timeout path, not GPS reception or geolocation accuracy.

## November 16 recipe changes

The custom package staging directory now requires the three matching `+drawerlayout1` packages (`phosh`, `phosh-common`, and `libphosh-0.45-0`), in addition to phoc, both GSD packages, and both libcamera packages: eight packages in total. Stage the matching locally verified `.deb` files and regenerate `SHA256SUMS`; they are not included in this repository.

Before building, prepare `recipe/overlays/lmi-battery-debs/` with the three packages produced by `userspace/apps/battery-packaging/build-debs.sh` and a `SHA256SUMS` covering them. The image installs battery-logger 0.1.1, battery-viewer 0.1.10 and battery-sleep-boundaries 0.1.0 and enables the logger. The optional sleep hook records only suspend boundaries, not continuous measurements while suspended.

Run `sh tools/preflight-packages.sh CUSTOM_DIR BATTERY_DIR` before a build. It verifies package counts, every manifest entry and checksum, package names, versions and architectures. Version equality does not establish binary identity or functional equivalence; in particular, two logger 0.1.1 packages were observed with different payload hashes. The preflight does not validate proprietary firmware, GPU inputs, package repository availability or the finished image.

The recipe sets the French keyboard as the system default and enables the manual keyboard-hide button. Existing user preferences override the default. `tools/test-keyboard-recipe.sh` checks unit installation and script syntax, but the updated full image recipe has not yet been built or boot-tested.

On 16 November the sound card was absent because the `3370000.codec` VA macro probe timed out at boot; manually requesting one new probe restored the card and the user confirmed audio after restarting PipeWire. The recipe includes a one-shot retry after ADSP startup, only if that codec is still unbound. Its no-op path was checked on the running phone; recovery at the next boot has not been tested.
