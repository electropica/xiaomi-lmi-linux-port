# Unvalidated boost diagnostic candidate - 2026-10-06

This is a source-only experimental candidate, not a battery fix or an
approved deployment recipe. It was not applied to the reference source,
built, booted or installed.

The exact a5b3099017ae581aae8bf597b2f9c8c765026af1 source declares
vdd_boost_vreg always-on at PM8150B GPIO 5. A targeted search of the QCOM
DTS/DTSI files found this declaration but no phandle consumer. Live sysfs
reports it enabled with one user. The separate vdd_hap_boost regulator uses
the same GPIO and is disabled with zero users. Shared GPIO handling is
supported by the regulator core; this is not proof of a GPIO conflict.

The [candidate patch](../../kernel/patches/diagnostics/lmi-boost-release-always-on-unvalidated.patch)
replaces always-on with boot-on in that node only. The normal regulator core
could then release the unclaimed enable vote during late unused-regulator
cleanup, while preserving enablement during initial boot. No direct GPIO
write, driver unbind, charge/gauge change or thermal-policy change is involved.
A dry-run applies cleanly to the exact source above. DT compilation and
hardware behavior have not been validated.

Before a hardware trial, establish the board function of this boost and
exclude undeclared essential consumers. Lack of a DT phandle is not proof
that its external load is optional. This prerequisite from the earlier
[peripheral review](lmi-battery-audio-torch-2026-10-03.md) remains open.
The patch must remain outside the production patch list until then.

If that prerequisite is resolved, the diagnostic must use a separate
temporary boot, retain the known boot for recovery, compare charge-counter
loss across matched deep-suspend intervals, and verify USB, charging,
display, touch, speaker, microphone, torch and haptics. Only a measured
reduction with retained functionality would support a production change.

This follow-up found no new runtime power fault: CPU idle remains enabled,
and charging-time GPU/USB/UFS runtime status cannot establish their state
in unplugged deep suspend. Previous tests already ruled out persistent
USB rails and GPU CX/GX rails in their observed unplugged intervals.


## Phone OEM-style DTBO comparison - read-only, 2026-10-06

A bounded read of the phone's dtbo partition found an Android DTBO table with
12 entries and declared size 5,514,578 bytes. Every parsed entry declares
vdd_boost_vreg always-on on PM8150B GPIO 5. Each also declares vdd_hap_boost
on the same controller/pin, with a vdd-supply reference from qcom,haptics.
No direct *-supply consumer of vdd_boost_vreg was found inside these overlays.
Entry 0 additionally declares an AW8697 haptic device. The GPIO controller
phandles were resolved rather than assuming that integer 5 alone identified
an identical pin. Local-fixup bookkeeping nodes were excluded from consumers.

Thus the always-on declaration is also present in the on-phone OEM-style
artifact, rather than being established as a Linux-port-only addition. The
shared GPIO is associated with a declared haptic supply; this does not prove
that haptics is its sole physical load or that it is safe to release the vote.
Overlay references do not exhaust dependencies in the base DT or firmware.
The active overlay index and original MIUI release identity were not established.
No artifact was flashed, saved to Git or modified. The diagnostic patch remains
source-only and its essential-load prerequisite is not waived.

For reproducible identification, entry 0 SHA-256 is
524d131cb916a73bb5a44aa44c18faae89af14a51cfc9ae6145c3b16a131f571;
entry 11 is ebef7c8ecdc14fe096e69d2c6d570edae681c48462c74e715e0fc8a9734022a6.
The read-only inspector is under userspace/power/diagnostics/ and requires an
explicit --input argument. It bounds table entries and blob lengths and emits
only selected regulator relationships; it does not write partitions or GPIOs.

Related read-only checks found pci_msm keep_resources_on=0 and all three
ASPM capability inversion parameters zero. PCI config reads showed ASPM L1
enabled (link-control mask 2) at both root port and endpoint, with all four
L1SS enable bits set (mask 15). These charging-time configuration bits show
that low-power features are enabled, not proof of residence in those states
while unplugged. No PCI register, link policy or Wi-Fi state was changed.
