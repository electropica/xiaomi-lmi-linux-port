# Recovery reason init_user0_failed: direct stock-Android control

fstab1 reaches recovery after Android selection. The operator returned to
Mobian. Recovery logs/pmsg show --prompt_and_wipe_data with
--reason=init_user0_failed. The original Android failure trace has been
replaced by recovery activity; the exact vold/user-initialization error is
not yet captured. No wipe, flash or partition change was performed.

Read-only inspection confirms Mobian root /dev/loop0p2 is backed by /dev/sda35,
Android userdata is /dev/sda34 and metadata is /dev/sda18. Metadata has an ext4
signature. Raw userdata lacks a plain ext4/F2FS signature, which is compatible
with encryption and does not prove corruption. The temporary cache log mount
was ext4 ro,noload and was removed after capture. Private logs stay off Git.

Run the exact original Lineage boot directly via Fastboot RAM boot with the
same partitions and userdata. This distinguishes a menu/handoff-specific
failure from one affecting normal Android startup. No build is required.
test-lineage-direct-control-windows.py verifies the pinned original image,
Android-v2 header/size, Mobian root/installed boot, lmi product and partition
sizes, and requires the SSH preflight-completion marker. Only fastboot boot
is issued: no flash, erase or format. Plan-only verification passed; operator
execution and startup outcome remain pending. The persistent boot stays Mobian.

If Android reaches its lock/home screen, capture read-only Android logs and
compare boot/security context before another menu change. If recovery returns,
preserve its reason and investigate that baseline. Do not accept a wipe prompt.
Key-management context differences are hypotheses, not demonstrated causes.

## Stock Android succeeds; OS-version header control prepared

Original Lineage boots; operator confirmation and native Windows root ADB
independently establish boot_completed=1 and encrypted F2FS /data mounted.
Live DT and selected technical parameters are saved privately. The menu header
reports Android 11 / August 2022, versus stock Android 16 / September 2026.
A control copy aligns only this field; only offsets 44 and 47 differ, with
all remaining bytes identical. No compilation, partition change or key change.
Derived SHA256: 71e226f1a8adaf5d0574d1311d686143694404f49ab62df5d343c8a36c3c5196.
The Android-start Windows RAM launcher passes plan-only verification. Actual
outcome remains pending. Hardware-key version context and inherited AVB
metadata are hypotheses; no AVB bypass is proposed. Standard builder unchanged
until validation. See build/boot-menu/chainload/ANDROID-OS-VERSION-CONTROL.md.
