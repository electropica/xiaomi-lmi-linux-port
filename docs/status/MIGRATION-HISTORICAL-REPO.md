# Historical repository migration record (2026-09-30)

This document records a migration-time audit, not an active procedure or a
current filesystem dependency. The source and verified-copy paths reported in
the original migration note were local locations observed during that
migration; they are not asserted to exist now and are not current dependencies.
Those absolute paths are intentionally omitted here.

The reviewed material concerned an earlier lmi/postmarketOS porting period:
dated notes, diagnostic scripts, redacted logs, image manifests, kernel
configuration evidence, and older pmaports recipes. Its README described a
headless stage preceding the later GPU72 Mobian/Phosh validation. Historical
project provenance is summarized in [`p1-reconstruction-sources.md`](../provenance/p1-reconstruction-sources.md),
and the migration policy is documented in
[`migration-protocol-v1.md`](../architecture/decisions/migration-protocol-v1.md).

The audit classified the then-verified copy under an archive/legacy-repository
area because of its historical value. This classification does not establish
that any old absolute source or copy path remains present, and it does not
create an active dependency on those locations.

## Pre-copy audit

The targeted audit reported 177 regular files, 18 directories, no symbolic
links, and no internal `.git`. It found no known active dependency from the
principal inspected workspace scripts/configurations to `historical-repo`,
and no known dependency from its contents to GPU68, GPU69, GPU71, or GPU72.
In particular, no active GPU72 dependency was found by that targeted search.
This was not a workspace-wide proof that no reference exists.

The historical scripts referred mainly to an older WSL/user workspace rather
than the then-current migration workspace. The root workspace Git directory
was not inspected or changed as part of that classification.

## Copy verification

| Check | Source | Copy | Result |
| --- | ---: | ---: | --- |
| Regular files | 177 | 177 | Match |
| Directories | 18 | 18 | Match |
| Symbolic links | 0 | 0 | Match |
| Apparent size | 1,297,738 bytes | 1,297,738 bytes | Match |
| Disk usage (informative) | 1,781,760 bytes | 1,781,760 bytes | Match |
| Files with differing SHA-256 | 0 | 0 | Match |
| Missing files | 0 | 0 | Match |
| Extra files | 0 | 0 | Match |

The relative file inventories matched, and all 177 regular-file SHA-256
values matched at their respective relative paths. The original remained
present after verification. `VALIDATION : OK`.

This record remains historical. Any future archival relocation or retirement
must follow the current policy in
[`migration-protocol-v1.md`](../architecture/decisions/migration-protocol-v1.md).
