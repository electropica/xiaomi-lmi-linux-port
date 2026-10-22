
## 2026-10-21: Android boots from the temporary menu

The operator confirmed a successful LineageOS start after selecting it in the
temporary menu. Native Windows ADB independently reported sys.boot_completed=1,
file-based encryption, and metadata encryption enabled. Tested image: 25993216
bytes, SHA256 71e226f1a8adaf5d0574d1311d686143694404f49ab62df5d343c8a36c3c5196.

Only header offsets 44 and 47 differ from the previous fstab1 image: the OS
version field now matches pinned Android 16 / September 2026. A successful stock
Android boot occurred between the failed and successful menu trials, so the
exact internal vold/keymaster cause remains unproven. No keys or encryption
policy were changed; no flash, wipe or partition change occurred in this trial.

The recipe now applies this header alignment automatically to Lineage menu
outputs and records the OS-version context in its artifact manifest. Host checks
reproduce the tested image from the previous output; shell/Python syntax pass.
No new firmware compilation was run. The existing WSL cached output still has
the old header; the tested derived image is distinct.

The menu remains temporary and MUST NOT be flashed. Mobian currently restarts
the installed boot image; it needs direct chainloading before a persistent menu
can safely replace that image. Touch input remains unqualified; buttons work.

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


## Compatibility-DT variant correction, 2026-10-22 (host only)

The successful temporary menu Android boot reports lmipro / CN / 3.9.0, whereas
the recorded direct stock Android command line supplies std / GLOBAL / 3.19.1.
The menu passes both sets. The pinned compatibility DT has the stale pro/CN
values before the actual bootloader arguments, explaining the Zoom Edition
identity. No system property or device identity was overwritten on the phone.

The candidate now removes only those first three known stale variant tokens
from the final in-memory DT bootargs, and only when a later value for the same
key exists. Unknown or multiple ambiguity is rejected before any buffer change.
Unrelated arguments (including AVB policy) remain byte-for-byte unchanged.
This correction applies only to the qualified android/mobian menu targets.
The source manifest now tracks seventeen edits for dual mode.

Actual C tests cover the real compatibility/stock argument combination, repeated
execution, unknown first value, empty value, excess duplicates and missing NUL.
Four affected ARM64 units pass syntax checks; source restoration and tamper
checks pass. The corrected fstab host checks retain the Mobian no-op. Hardware
model identification is still unvalidated for the new candidate.
