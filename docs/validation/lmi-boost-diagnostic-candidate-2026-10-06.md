# Unvalidated boost diagnostic candidate ? 2026-10-06

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
