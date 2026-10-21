# Successful stock Android: OS-header control

The operator confirms original Lineage boots. Native Windows ADB independently
confirms boot_completed=1 and encrypted F2FS /data mounted. The live Android DT
and selected technical parameters are saved privately. The menu path still
reaches recovery with init_user0_failed; stock Android is the working control.

Stock Android-v2 header OS version: 536871337, Android 16 / September 2026.
Menu v1 header OS version: 369099112, Android 11 / August 2022.
Hardware-backed version binding can make this relevant to key use, but its
role in this failure remains a hypothesis. Inherited AVB metadata also differs
and remains a separate candidate, unchanged in this test.

match-android-os-version.py copies only header bytes 44..47 from the exact pinned
Android boot into a qualified fstab1 copy. Only offsets 44 and 47 actually
change; every other byte and the image length remain identical. No compilation,
kernel, ramdisk, DT, signature policy, partition or key-material changes.
The standard builder is unchanged until this isolated control is validated.

Derived image SHA256:
71e226f1a8adaf5d0574d1311d686143694404f49ab62df5d343c8a36c3c5196

test-lineage-osversion-windows.py starts from the working Android with root ADB
already enabled. It checks lmi, Android boot completion, installed Mobian boot
prefix and Mobian partition size, then performs only a Fastboot RAM boot.
Plan-only verification passed. Actual Android outcome remains pending.
No flash, erase or format; do not accept any data-wipe prompt if recovery returns.

Reference: https://source.android.com/docs/security/features/keystore/version-binding
