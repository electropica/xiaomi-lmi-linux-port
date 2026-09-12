# Historical repository workspace copy

STATUS: COPIED AND VERIFIED — ORIGINAL RETAINED

## Paths and classification

- Source: `/home/linuxagent/pmos-d-repro-01/historical-repo`
- Verified copy: `/home/linuxagent/pmos-d-repro-01/archive/legacy-repos/historical-repo`

The copy is classified under `archive/legacy-repos` because it preserves an
earlier lmi/postmarketOS porting period: dated notes, diagnostic scripts,
redacted logs, image manifests, kernel configuration evidence, and older
pmaports recipes. It has high historical value and must be preserved in full.
Its README describes a headless stage preceding the currently validated
GPU72 Mobian/Phosh state.

## Pre-copy audit

The targeted audit found 177 regular files, 18 directories, no symbolic
links, and no internal `.git`. It found no known active dependency from the
principal inspected workspace scripts/configurations to `historical-repo`,
and no known dependency from its contents to GPU68, GPU69, GPU71, or GPU72.
In particular, no active GPU72 dependency was found by that targeted search.
This was not a workspace-wide proof that no reference exists.

The historical scripts refer mainly to an older `/home/microstar` and WSL
`/mnt/c/Users/microstar/Documents/lmi_linx` environment, not the current
`/home/linuxagent/pmos-d-repro-01` workspace paths. The root workspace Git
directory was not inspected or changed as part of this classification.

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

The verified copy does **not** authorize deletion of the source or make the
new location the sole historical reference. Any later removal, retirement,
or redirection of the old path requires a distinct phase and explicit
decision under `docs/decisions/migration-protocol-v1.md`.
