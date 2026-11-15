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

The image configures `CHASSIS=handset` in `/etc/machine-info` and verifies it. GSD disables its desktop automatic-suspend warning for handset chassis; on 15 November the handset had an unset chassis and GSD warnings coincided with repeated display wakeups. The handset setting was restored and a battery test is pending; this correlation is not yet an end-to-end validation.
