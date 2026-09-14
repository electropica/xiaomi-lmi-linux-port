# Sensitive local SSH test material

STATUS: SENSITIVE — RETAIN IN PLACE — DO NOT COMMIT

Directory: `/home/linuxagent/pmos-d-repro-01/ssh-key-test`

## Inventory and audit boundary

The targeted audit found 28 regular files, 15 directories, four internal
symbolic links, and no internal `.git`. Three variants of `authorized_keys`
each contain one public SSH key; the three files have the same SHA-256. No
private-key marker was found in the targeted audit. That absence is not a
guarantee that every possible secret format was excluded.

`shadow-before` and `shadow-after` are identical. Each contains one unlocked
authentication-hash field associated with the historical account `lmi`
(UID 20694, GID 0). This document intentionally does not record that hash,
any SSH key, a key comment, or any shadow-file contents. A targeted search for
the `lmi:` entry inside `ssh-key-test` found it only in those two shadow
copies. The `lmi` account is absent from the active GPU72 rootfs file
`/home/linuxagent/pmos-d-repro-01/Mobian-M0/rootfs-final-gpu72/etc/passwd`.

No role for `ssh-key-test` in the active GPU72 chain was established. No
incoming reference was found in the principal active scripts and
configurations inspected; the search was targeted, not exhaustive.

## Access and disposition

The directory has been secured to mode `0700`; `shadow-before` and
`shadow-after` have been secured to mode `0600`. The current owner is
`linuxagent:linuxagent`.

Keep the directory at its current path. Do not copy it as-is to
`archive/legacy-repos`. Neither `ssh-key-test` nor its sensitive files may
ever be added to the canonical Git repository. Any decision to redact,
delete, or place this material in a restricted local archive requires a
separate, explicitly reviewed phase. This status note authorizes none of
those operations.
