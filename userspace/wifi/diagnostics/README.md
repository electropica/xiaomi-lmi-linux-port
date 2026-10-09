# Android super mount-script preparation

`prepare-android-super-mounts.py` creates a private candidate from paired
read-only `lpdump` text and JSON reports and the locked historical
`../scripts/lmi-android-wifi-mounts` reference. It only writes a new output
directory containing a script and layout manifest. It does not contact a
phone, create mappings, mount filesystems, flash partitions or build images.
Captured reports and generated candidates remain outside Git.

The inspected LineageOS 23.2 October 7 layout moves the vendor start from
1,146,093,568 to 1,147,142,144 bytes within super and changes its logical size
to 820,428,800 bytes. Its filesystem is EROFS, already enabled in the retained
Mobian kernel. The historical fixed-offset script must not be treated as
compatible with that new vendor layout. This is a return-to-Mobian prerequisite,
not evidence explaining battery drain.

The generator accepts metadata version 10.0, one `super` block device and one
zero-based linear extent per partition. It cross-checks text and JSON sizes,
readonly attributes, filesystem sizes, bounds, overlap and partition identity.
It rejects other layouts instead of inferring a loop offset. The exact
reference SHA-256 is locked. Only the system/vendor mount-call parameters
change; the canonical script and historical image lock remain untouched.

WSL/Linux — offline preparation only:

```sh
python3 userspace/wifi/diagnostics/prepare-android-super-mounts.py \
  --lpdump-text /private/path/lpdump.txt \
  --lpdump-json /private/path/lpdump.json \
  --reference-script userspace/wifi/scripts/lmi-android-wifi-mounts \
  --output-directory /private/path/new-candidate
```

Re-read metadata after any Android update. Do not install a candidate merely
because generation succeeds: verify the retained userdata/boot identities,
review the generated two-line change and preserve a return path first.
Actual Mobian boot, vendor tools, Android linker/APEX compatibility and service
startup remain unvalidated with the new layout. A vendor-tool permission
denial from ordinary Android shell does not establish its absence.

No automatic image-builder integration or phone installation is provided.
The source contains no proprietary filesystem bytes. Synthetic guard tests
run without phone access or captured device fixtures:

WSL/Linux — host validation:

```sh
python3 userspace/wifi/diagnostics/test-prepare-android-super-mounts.py
```
