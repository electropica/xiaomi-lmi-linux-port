# lmi dual-boot migration gate

The operator selected a fresh installation without preserving today's Mobian
files/settings. These sources prepare a constrained GPT migration, not a
general partition manager. Device write operations remain operator-run from
native Windows, matching the repository workflow.

Read-only recovery qualification on October 21 confirms root ADB, product lmi,
no block-backed mounted filesystems, 4096-byte sectors and a 254669750272-byte
LU0 disk. Primary/backup header CRCs and both partition arrays agree with the
earlier qualified layout. The secondary array starts at last-header-minus-four,
not minus-two; two reserved sectors remain unchanged. The parser refuses other
geometry instead of guessing. Nine transformation tests pass using the retained
read-only metadata, including damaged CRCs, stale geometry, disk-ID mismatch,
table-copy mismatch, exact changed-byte scope and secondary-first write order.

The proposal keeps entries 1–33 byte-identical, changes only userdata entry 34's
end from 62175226 to 57980671, and creates entry 35 `mobian` at LBAs
57980672–62174975 (16 GiB). Protective MBR, partition starts, other GUIDs,
attributes, disk identity and reserved gaps remain unchanged. Existing userdata
filesystems no longer fit their shortened block device and MUST NOT be mounted;
the next installation step must recreate Android data as already agreed.

`migrate.py` defaults to a fresh read-only capture/plan. `--apply` additionally
requires `--discard-current-installation`, performs fresh recovery/root/device/
unmounted/geometry/CRC/layout checks, rereads all metadata immediately before
writing, then writes and byte-verifies each secondary array/header followed by
the primary array/header. Temporary payloads are pushed only to recovery RAM
and checked by SHA-256. No filesystem format or image flash is performed by it.
Original metadata and every completed write are kept privately on the PC for
verification and error recovery; this is not a full Mobian userdata backup.

After any partial failure: stop, preserve the private record, and do not format,
flash or retry blindly. A successful GPT write still requires restarting the
recovery and verifying the new kernel block-device sizes before formatting or
flashing. The sparse Mobian image must target `mobian`, never `userdata`.
Both OS boots and automated selection remain unvalidated.

Workstation defaults use the existing Windows Downloads platform-tools and
Documents/ChatGPT/Mobian/work for private state. `--work-dir` can override the
private state directory. Do not commit that directory or captured disk metadata.
