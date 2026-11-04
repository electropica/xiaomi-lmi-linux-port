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
