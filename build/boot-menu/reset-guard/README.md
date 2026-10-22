# Preserve the platform reset service — isolated candidate

Status: host-replayed candidate only. Not integrated into the firmware recipe,
not built into an image, not installed, and not validated on the handset.

## Operator result

On 22 October 2026 the operator tested the older menu where LineageOS starts:
Mobian starts, LineageOS starts, and both Fastboot and Recovery selections
return to Mobian. The text no longer fills the screen. This does not qualify
the newer 64-MiB dual-direct candidate. The exact tested artifact has not been
read back; an operator reference to an installed menu is not evidence of a
particular boot-partition hash.

## Source findings

The pinned EDK2-MSM revision is e1952621f419f8db60ed28271264e1b5184c571d;
its EDK2 core is e7aac7fc137e247edad22f7ee53b9a1fba227397.

- `SimpleInit/src/boot/boot.c` constructs `cfg->key` as `base.extra`.
  `reboot_uefi.c` reads `arg` below that key. The menu's `extra.arg`
  configuration is therefore correctly addressed.
- `SimpleInit/src/lib/reboot.c` maps `bootloader` and `recovery` to a
  `RESET_PARAM` structure with reason 2 and 1, respectively. Both use
  `EfiResetCold` with this payload.
- `Platform/Qualcomm/sm8250/Apriori.fdf.inc` places the Qualcomm reset driver
  before `ResetSystemRuntimeDxe`. Private offline inspection of the locked
  Qualcomm driver finds `RESET_PARAM` handling material and installation of
  a runtime reset function; no proprietary binary is included here.
- The generic driver's `InitializeResetSystem` contains only an assertion
  about an existing reset architectural protocol, then unconditionally writes
  `gRT->ResetSystem`. The menu recipe builds RELEASE, so the assertion does
  not provide a runtime guard.
- The generic `ResetSystemLib` mapping in `QcomCommonDsc.inc` selects
  `ArmSmcPsciResetSystemLib`. Its cold-reset path discards `ResetData` and
  performs the normal PSCI system reset.

This is a concrete conflicting-service path consistent with both failed
selections. Runtime dispatch/driver initialization on the tested handset
has not been captured, so it remains a hardware hypothesis rather than a
proven end-to-end cause. Keeping the platform driver also does not establish
that every Qualcomm reboot reason is correctly interpreted on this device.

## Candidate and validation

`patch-reset.py` accepts only the exact reviewed source hash, produces a new
C file with exclusive creation, and refuses an in-place cache edit. It adds
a real `LocateProtocol` guard before any runtime-table write:

- Existing reset architectural protocol: preserve the service and return
  `EFI_ALREADY_STARTED`, including its valid NULL protocol interface.
- No existing protocol: retain the generic installation path.
- Other lookup error: return the error without replacing the service.

The host test extracts the **actual complete initializer** from the pinned
source and the patched source, compiles both with mocked UEFI services, and
checks the original RELEASE overwrite plus all three corrected paths. It also
checks rejection of an altered source. It does not simulate the firmware
dispatcher, Qualcomm driver or reboot hardware.

```sh
python3 -B build/boot-menu/reset-guard/test-reset.py \
  /home/linuxagent/lmi-boot-menu-build/source/edk2-msm
```

Result: original overwrite reproduced; platform preservation, missing-service
fallback, error propagation and altered-input rejection pass.

Before a manual image build, integrate this guard into the **identified
Android-working baseline**, include the changed EDK2 source in the build
manifest, and validate target compilation. Do not silently combine it with
the unresolved 64-MiB handoff changes. A temporary handset trial should check
both OS entries and both reboot destinations before any persistent installation.

The text sizing complaint is separate. The previously accepted native-font
rendering avoids the custom zoom stutter; this reset candidate does not
modify the renderer, font or console mode.
