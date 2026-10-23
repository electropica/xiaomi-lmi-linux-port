# Project artifact retention

Julien's policy, October 23, 2026: keep only useful working material on the
computer; the external D: archive contains only useful material that is
neither reproducible nor already available in Git.

## One current version

Keep one qualified menu image, one compatible rescue boot and one latest
installable Mobian system image. A kernel input required by a recipe is an
input, not an extra daily build. Retain its exact hash and provenance.
After a replacement passes actual handset validation, remove superseded
generated images and their unpacked working files. A temporary candidate is
allowed during an active comparison and is removed when the comparison ends.

The current qualified menu is be9841c76cbe34d0c72606c47877f99582aee224144744349a9e78d15cfd0a94,
81,051,648 bytes. Its compatible dedicated-root rescue is
75bb65facbd4146d4a1e668039ef52433ef90c2b6bdb07f2c59980caf3191374,
54,652,928 bytes. The latest full sparse system image is
f803fae6954c4d5e13cfa77815640a895d3d051d8a56db7813c75edce2bd3f8e,
3,660,075,304 bytes. No claim of bit-for-bit rebuild equivalence is implied.

## Git and external inputs

Git stores useful source changes, recipes, locks, patches and sanitized
validation results. Push only the authorized developpement branch; do not
modify main. Never publish credentials, raw private captures or vendor binary
inputs. Verify upstream revisions and local changes before deleting clones.

The external archive stores one copy of useful irreplaceable inputs, raw
measurements, private source changes and required private signing material.
Public toolchains, clean public clones, regenerated packages, build chroots,
generated OS images and obsolete build variants do not belong in that archive.
An item is not automatically reproducible merely because it is large or old.
Validate retrieval or preserve useful unique differences before deletion.

## Working directory discipline

Use the canonical checkout and only the isolated checkouts needed by active
work. Do not create a new top-level home directory for every experiment.
Put future scratch work beneath a single ignored build-cache root, with a
manifest naming its owner, recipe, purpose and removal condition. Existing
hard-coded paths must be migrated and checked before moving directories.
Do not leave symlinks that hide a broken dependency.

## Cleanup and backup checks

Before deletion, record the exact targets, resolve them under the authorized
scope, reject symlink/mount traversal and check for active builds. Keep a
small deletion receipt rather than a second full backup of generated files.
Before deleting a unique source, verify its replacement by hash. Preserve
file modes, symbolic links and extended attributes when archiving Linux-only
material; copying an extracted rootfs to NTFS is not a faithful Linux backup.

Do not delete active kernel sources or uncommitted modifications during
another analyst's work. Build compilation remains operator-run. Cleaning
files inside WSL does not automatically reduce the Windows VHDX file; report
filesystem cleanup separately from VHDX compaction.
