# lmi Linux7 experimental checkpoint

This branch isolates the7.2.12 bring-up from the working downstream4.19 system.
The operator temporarily booted a RAM observer and recovered its live USB log.
TLMM GPIO exclusions28-31/40-43 were required to cross the earlier binding
stall in this trial. See the [hardware record](../../../docs/validation/lmi-linux7-menu-host-check-2026-10-26.md).

## Accepted and unqualified layers

- Accepted: kernel entry, eight CPUs, observer /init, HS USB RNDIS, journal retrieval.
- Not qualified: display, touch, rootfs boot, GPU, camera, radios or battery life.
- CPUfreq still defers: its EPSS-L3 provider was modular, while this initramfs
  carries no modules. configs/cpufreq-next.fragment is host-Kconfig checked only.
- initramfs/init is the tested observer source. It stays in RAM, serves a bounded
  journal on USB TCP9000 and offers no remote shell. It is not a graphical OS.

The tested source inputs and diagnostic patch are retained here with their
identities. No generated Image, DTB, initramfs, proprietary firmware, keys or
raw handset logs are committed. The DTS reproduces the tested semantic inputs;
a host recompile from this path matches every deployed DT property. Byte-identical
DTB serialization is not required or claimed.

## Reconstruction boundary

This is a source checkpoint, not yet a portable one-command image builder.
The staged menu recipe still depends on the qualified local four-entry menu
inputs and isolated compiler rootfs. Do not delete those ignored build inputs
on the strength of this checkpoint alone. Refactor and lock the full menu and
kernel recipes here before declaring cleanup/reconstruction independence.
Heavy builds remain operator-run. No persistent installer is changed.

Keep working4.19 recoverable. Do not replace its kernel or boot the existing
Mobian rootfs with7.x before qualifying storage, modules, firmware, display and
input. The older branch name developpement is retained for now; no remote
branch or default-branch rename is performed by this checkpoint.
