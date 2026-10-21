# LineageOS selection returns to UEFI setup

## Observed handset result

The FFS3-corrected candidate (SHA256
eea24170b1d63bb4028b94c66437db9a1add3a4b67a5616e88ca15b1547b2f6e)
displays our Mobian / LineageOS / Fastboot / Recovery menu. The operator
explicitly confirmed that choosing LineageOS subsequently displays EDK2's
Device Manager / Boot Manager / Boot Maintenance Manager setup screen.
This is distinct from the earlier pre-menu black screens. The operator has
restarted into installed Mobian. No experimental firmware has been flashed.

Android kernel execution has not been demonstrated. An exact failing function
cannot be inferred from the setup screen alone. The pinned generic ARM launcher
also contains a historical Qualcomm Android FIXME; that comment is a limitation
to investigate, not proof of this specific failure.

## Source review

The configuration constructor returns a configuration even without disk paths;
the adapter can inject kernel/DTB/initrd/DTBO FROM_POINTER components afterwards.
ARM64 is initialized in linux_boot_init. The random-seed installer returns zero
even when RNG services are unavailable. None of these observations identifies
the actual hardware failure. DTBO matching, component loading, FV asset lookup
and ARM handoff validation still require an observed error.

boot() prints logs and clears the screen after ten seconds. The new diagnostic
records each attempted preparation step and, if run_boot_linux returns through
its failure cleanup, shows that step plus the latest six warnings/errors from
the existing RAM log. The error screen lasts at most 120 seconds, or until a
key is received. The panel is invoked before cleanup and before boot() clears
the console. FV lookup and component/CRC failures now have explicit messages.
No EFI variable, partition, file, boot address, overlay selection or kernel
argument is changed by the instrumentation.

Stages cover configuration, boot-object creation, verified RAM bundle, loading,
random seed, decompression, DTB selection, DTBO application, FDT generation,
component movement, initrd installation, FDT update, final checks and execution.
If no diagnostic screen appears, do not assume that this failure path ran.
Likewise a stage number denotes an attempted operation, not its success.

## Validation and next operator step

The three affected C translation units pass Clang 14 ARM64 syntax checking with
the generated build flags and -Werror. Thirteen-file patch/restore and tamper
rejection pass on a temporary source fixture. Actual build sources remain
unchanged during these checks. This is host qualification only; the diagnostic
has not yet been built or displayed on the handset.

Run the existing operator command:

```bash
sudo bash /home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/build.sh --build --with-lineage
```

The new artifact manifest variant ends in `prepi-ffs3-diag1`. After compilation,
qualify the new image and prepare a fresh Windows temporary launcher. Select
LineageOS using Volume/Power. Photograph the diagnostic panel if it appears;
the next change must follow its observed error. No experimental image is ready
for persistent installation.

## Diagnostic image compiled and qualified for temporary test

The operator compiled variant prepi-ffs3-diag1: 25995264 bytes, SHA256
287645d2b55060b15006037c6fa3a91180954af85cf4286ded2daae14b9803f0.
All thirteen source hashes match; the lmi memory map remains unchanged. The
PrePi replay passes on the new FD. Windows transfer and plan-only launcher
preflight passed. Use test-lineage-diagnostic-windows.py for this exact image.
No new phone contact, flash or persistent installation was performed. The
diagnostic error panel remains untested on the handset; Android handoff is
still unvalidated. The next observation is the stage/error after LineageOS
selection, not another blind boot attempt.
