# Opt-in Lineage recovery power control

This is an attended diagnostic for lmi, not an installation or battery repair.
The 18 October 2026 second trial completed180.094s of suspend and restored the
recovery settings. See kernel/diagnostics/power/README.md for results and limits.
No firmware, partitions or user-data files are written by this protocol.

## Read-only preflight

Run preflight.py on Windows with --adb pointing to native adb.exe and --output
pointing to a NEW private JSON file. It requires exactly one authorized device,
root, lmi identity and a running recovery process. No reboot or flash is invoked.
Android scripts use shell -T with explicit shell quoting, not script stdin.
Keep output private. ADB transport and recovery access may need operator action.

## Measurement (operator opt-in required)

Review measure-r2.sh before transferring it to temporary /dev storage using
native Windows ADB. Check that /dev is tmpfs, no other trial is active, the RTC
alarm is unused, and the three NPU clients initially use performance/min0.
The script requires USB online, deep selected and a running recovery. Its fixed
/dev/lmi-recovery-power-control-r2 output must not already exist; preserve any
previous evidence rather than overwriting it. Validate with sh -n first.

Launch detached with nohup/setsid, standard input /dev/null and a separate launch
log. Verify a live process and WAITING_FOR_UNPLUG before requesting the physical
unplug. Waiting is bounded to600s. After unplug and20s stabilization, the script
requires Discharging and USB offline, temporarily enables low-power idle and
sets the three NPU clients to powersave/zero. It requests mem with an RTC wake.

Recovery health monitoring is preserved. Early wakes cause another suspension
until the180s BOOTTIME deadline, with a twelve-wake guard. Each wake is logged.
The original NPU governors and sleep_disabled value are restored, and only its
owned alarm is cleared. The EXIT/signal trap provides normal error cleanup;
forced process killing or a kernel failure cannot be made safe by a shell trap.
The RTC wake and an attended operator remain necessary. No automatic reboot,
flash, firmware loading, calibration or protection change is part of the test.

## Retrieval and interpretation

After physical USB return, fetch.py --adb PATH retrieves the private log and
checks restoration against the qualified recovery baseline. It uses analyze.py
to sum actual suspend intervals, excludes a duplicated final sample, and rejects
charging endpoints, early returns, incomplete runs and insufficient suspension.
It never starts a measurement. Existing output files are refused.

Counter rates are correlated gauge-derived estimates. Raw and learned counters
have different capacity scales; do not compare their unscaled rates as currents.
A short100%SOC test and charge-filter transients do not reproduce long Android
idle trials. Recovery kernel/baseDTB identity does not prove runtime overlay or
full-Android initialization equivalence. Return normally to the installed OS
after retrieval and verify its kernel, policies and interface separately.


## Extended variant

measure-r3.sh / arm-r3.py / fetch-r3.py add1800,3600,7200s choices and per-wake
accounting. Only1800s has hardware validation. Longer variants are host-only
validated. Read EXTENDED-PLAN.md and retain its elapsed-time limits.
