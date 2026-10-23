# Permanent dualboot installation preparation — October 23, 2026

Status: existing firmware built and host-qualified, handset validation PENDING.
No new firmware build is required to test the current candidate. This folder
prepares a reviewable installation; it has not installed or tested the handset.

Menu target: Mobian default after15s, LineageOS, Fastboot, Recovery. The candidate
uses direct RAM loading for both operating systems and preserves platform reset.

## Pinned files in Windows Downloads

- Menu `lmi-menu-outer-dual-extent-20261023.img`, 81051648 bytes,
  SHA256 be9841c76cbe34d0c72606c47877f99582aee224144744349a9e78d15cfd0a94.
- Dedicated-root rescue `mobian-lmi-dualboot-boot-20261021.img`, 54652928 bytes,
  SHA256 75bb65facbd4146d4a1e668039ef52433ef90c2b6bdb07f2c59980caf3191374.
- Existing native `Downloads/platform-tools/fastboot.exe`.

The old resetguard1 reference (SHA40cbcc...) uses a restart-only Mobian entry.
Do not install it over boot: it would not provide direct Mobian startup.

## Operator workflow

1. Finish MiniMax's battery observation and retrieve its files before any reboot.
2. Operator places the phone in Fastboot, cable connected. Run the existing
   `work/test-dual-extent-menu-windows.py --execute`: temporary RAM boot only.
3. Leave the15s default to Mobian. Once it starts, run this folder's
   `verify-mobian.py --execute`. It reads the marker lmi_menu=outer-v2, root
   block/loop backing and16GiB partition size through the existing SSH route.
   A visual return to Mobian without that marker does NOT qualify direct boot.
4. Record the operator-confirmed GUI/default outcome using
   `manage.py record-outcome --entry mobian-default --evidence "actual observation" --execute`.
   Reuse the same pinned temporary image to test LineageOS, Fastboot and Recovery,
   recording each actual result. A failure means fix/test again, never fabricate a PASS.
5. Only after all outcomes and runtime proof exist can the operator run
   `manage.py install --execute` from Fastboot. It rehashes both images, checks
   one device/product lmi and the exact boot/mobian sizes, then writes only boot.
   No automatic reboot or retry. Review the command before execution.
6. Operator reboots manually. Run `verify-mobian.py --phase installed --execute`
   to check direct root and the actual installed boot prefix SHA256. Only that
   establishes readback; Fastboot OKAY alone is a completed write, not readback.

## Rescue commands (operator-run Windows Fastboot)

With exactly the lmi phone in Fastboot and the verified rescue file:

```powershell
& "$env:USERPROFILE\Downloads\platform-tools\fastboot.exe" boot "$env:USERPROFILE\Downloads\mobian-lmi-dualboot-boot-20261021.img"
```

That boots the dedicated-root Mobian image in RAM. If restoring persistent boot
is required, the corresponding manual command writes that same rescue image to
boot. No userdata, super, recovery or partition-table change is involved.
The dualboot OS images remain on their existing partitions.

## Offline checks and scope

`manage.py` defaults to plan-only, hashing the local pinned files without device
contact. `test_manage.py` uses fake Fastboot output and simulated runtime records;
no handset call or flash. Private launch/runtime/operator evidence stays in ignored
private-state/. No remote publication. Do not modify MiniMax's active branch while
it is being used for battery work; this preparation is currently in Windows work/.
