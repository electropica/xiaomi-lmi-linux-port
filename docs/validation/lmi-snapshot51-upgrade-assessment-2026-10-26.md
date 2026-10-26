# Snapshot51 and complete-system upgrade assessment — 2026-10-26

## Current handset

Debian13/Trixie, native Snapshot48.0.1-1, GTK4.18.6, libadwaita1.7.6,
custom Phosh0.46/Phoc0.46/GSD48 with accepted lmi patches, downstream kernel4.19.
No packages are held. Native Snapshot candidate in configured apt indexes is
still48.0.1. A simulated full-upgrade proposes19 existing-package updates,
no additions/removals, and no change to the selected custom shell packages.
Those19 updates have NOT been applied. No repository suite was changed.

## Snapshot51 route investigated

Official GNOME/Flathub sources confirm51.0, available for ARM64. The official
source archive SHA2563e64fa4cd1a742ae34b6f6d8e6d9614a2d3eab88a1b0071c11ab53617eb214c2
was checked. It requires GTK>=4.18, libadwaita>=1.8.alpha and glycin2; a native
replacement is not satisfied by installed libadwaita1.7.6. Flathub packages it
with org.gnome.Platform/aarch64/51.

Flatpak1.16.6 and libostree2025.2 were installed (only two additional packages,
no existing-package upgrade/removal); dpkg audit clean. Exact ownership of
/home/mobian/.local and .local/share was repaired root->mobian because it blocked
user installation; no recursive ownership or file-content change. The official
Flathub user remote was added. Native Snapshot/launcher remain unchanged.

Snapshot51 itself is NOT installed. Its install job downloaded runtime data but
failed deploying it with "statx didn't return all required fields". The job is
inactive/failed, not running. Downloaded objects are retained for a possible
validated retry; no unbounded downloader remains.

## Confirmed compatibility gap

Read-only libc statx probes on /, /proc and the user Flatpak directory request
TYPE|INO|MNT_ID; calls return0, but masks are0xfff/0x7ff/0xfff, with MNT_ID absent.
The upstream libglnx path-chasing guard explicitly requires TYPE, INO and either
MNT_ID or MNT_ID_UNIQUE and emits this exact error otherwise. This establishes a
real missing kernel facility relevant to the failure; it is not a full audit of
all additional Flatpak/runtime compatibility requirements.

Do not invent mount identifiers, disable sandbox/security checks or downgrade
security-sensitive packages merely to bypass this error. A properly verified
kernel feature backport is a possible future solution, not prepared/compiled/
installed here and not a guarantee that every later runtime requirement passes.

## Whole-system upgrade

Mobian's official FAQ distinguishes Trixie/stable, Forky/testing and
staging/unstable. A migration to testing is possible but cannot be treated as an
ordinary app update on this custom port. Newer package versions can supersede
local shell/power patches; current apt's choice of those versions on Trixie does
not protect them against a newer branch. A controlled candidate image with
ported patches and qualification is preferable to an unreviewed live suite swap.
No Forky resolution, image recipe migration or full upgrade has been executed.

## Sources

- https://welcome.gnome.org/app/Snapshot/
- https://raw.githubusercontent.com/flathub/org.gnome.Snapshot/master/org.gnome.Snapshot.json
- https://download.gnome.org/sources/snapshot/51/snapshot-51.0.tar.xz
- https://wiki.debian.org/Mobian/FAQ
- https://browse.dgit.debian.org/flatpak.git/tree/glnx-chase.c?h=debian%2F1.17.3-2&id=916b70619c44cd7736b2d4f9d2e8ae0ee5ddab28
- https://kernel.googlesource.com/pub/scm/docs/man-pages/man-pages/+/master/man/man2/statx.2

Private detailed receipts: snapshot51-*-20261026-private.json and
mobian-system-upgrade-audit-20261026-private.json. No credentials or raw images
belong in the versioned record.
