# Standby follow-up — 19 October 2026

## Daytime reporting and natural resumes

The completed same-boot observation contains 42 natural gauge resumes followed
by PrepareForSleep in 15.209–15.442 seconds (median 15.385). No unplugged
WakeUpScreen request was recorded; the expected request occurred at USB return.
These software events do not directly measure physical panel power.

Displayed capacity differs from real_capacity/MSOC by zero or one percentage
point, median zero, throughout the usable unplugged rows. Learned capacity stays
2710 mAh. This argues against an extra Phosh-only display error in this record;
MSOC remains a model estimate, not independent current or capacity calibration.

## UFS lane-clock mechanism

The [RP5 experiment patch](https://github.com/mihaivladan/rp5-ufs-kernel-test/blob/main/ufs-lane-clocks.patch)
changes bulk-all-clock lane helpers to individual lane-clock operations.
Retrieved patch SHA256:
67340039b880e85485875d896fc2e9e517e9a808beba996f1e8b151853397fd5.

The retained downstream drivers/scsi/ufs/ufs-qcom.c already controls individual
RX/TX lane clocks, guards repeated enable/disable with is_lane_clks_enabled,
and disables lane clocks during suspend when the link is not active. The
specific bulk-all-clock mechanism is absent; this comparison justifies no new
patch/build. It does not prove every UFS runtime clock or rail is off.

## FG calibration: open question, no proposed write

The retained qpnp-fg-gen4.c exposes CALIBRATE through a cached calib_level,
initially -EINVAL at probe. Only its property setter invokes
fg_gen4_set_calibrate_level: write a request to SDAM1 register 0xB0BC, trigger
PBS, check completion, cache the level. The common Xiaomi DT sets
qcom,force-calib-level=130, but parsing this property does not invoke the setter.
A bounded selected charger-source search found no other kernel caller; Android
proprietary userspace and all indirect call paths have not been audited.

The [Qualcomm binding](https://android.googlesource.com/kernel/msm/+/refs/heads/android-msm-coral-4.14-android13/Documentation/devicetree/bindings/power/supply/qcom/qpnp-fg-gen4.txt)
describes the optional forced level and PBS reference.
[Commit 7588e9f](https://android.googlesource.com/kernel/msm/+/7588e9fca199b9db23797a3c28f8a9e6dade59f4)
corrects the SDAM mailbox from register 127 to 124; our retained setter already
uses the corrected address. The API's presence does not show that Android uses
it, that calibration is missing, or that it affects physical standby demand.
A cached -EINVAL would mean no successful setter invocation in that driver
instance, not necessarily uncalibrated PMIC hardware.

The parallel-current worker separately derives FG_SMB_MEAS_EN from input
presence/charge_done; its callback controls SMB_MEASURE_EN_BIT. The selected
kernel-journal check found no FG failures during the observation. With debug
logging off, this is not a readback of the bit in suspend.

A read-only follow-up is prepared for the next confirmed replug: cached
calibrate, DT PBS/forced-level properties, existing measurement-vote status.
Equivalent full-Android evidence is needed before interpreting a difference.
Plugged readback cannot establish unplugged register state. No calibration,
PBS trigger, profile reset, charge-protection change, hardware write, build or
new battery test was run. The operator may unplug; no collector is active.

## Read-only handset follow-up completed

On the same Mobian boot after the operator confirmed USB return, the cached
calibrate property reads -22. The live DT contains force-calib-level 130 and a
PBS phandle. This confirms no successful calibration-setter invocation in this
driver instance; it does not prove missing or inaccurate hardware calibration.

The FG_SMB_MEAS_EN vote is zero with no effective client. There is no power
supply named parallel: only batt_verify, battery, bms, bq2597x-standalone, dc,
main, pc_port and usb. The retained fg-util.c helper looks up exactly parallel,
so that worker's availability condition is false in this observed topology.
A single targeted read of BATT_INFO_FG_CNV_CHAR_CFG at 0x41b7 returned 0x02:
SMB_MEASURE_EN_BIT(bit2) is clear. The regmap reader address/count selectors
were restored and verified; no hardware data register was written. This is a
plugged/awake snapshot, not direct evidence from inside suspension.

A bounded read of 17 selected battery/thermal vendor binaries (~10 MB) and 98 init
and thermal configuration files (~273 KB) found no direct calibration invocation.
The health service's sole matching text, "Calibration required", is also the
standard [AOSP BatteryMonitor health-enum label](https://android.googlesource.com/platform/system/core/+/android16-qpr2-release/healthd/BatteryMonitor.cpp),
not evidence of calibration execution. Its selected health interface shared
library contains no matching reference. This is bounded negative evidence;
computed paths, dynamically loaded components and other vendor binaries are
not exhaustively excluded. No proprietary binary is included in this repository.

No calibration experiment is justified from these findings. The possible
longer recovery comparison has been deferred at the operator's request because
two hours is too long. Repeating the existing half-hour control would not test
the previously observed full-Android change after one hour. No new battery test,
reboot, build, flash or power-policy change is pending.

## Separating awake and suspended accounting

Offline re-accounting of the October 19 record isolates 42 adjacent
PrepareForSleep/resume pairs with USB-zero discharging endpoints and stable
capacity scales. They cover 34,947.255 seconds, of which 34,921.467 were actually
suspended (99.926%). Software accounting gives 47.86 mA, shadow 47.27 mA and
nominal-scaled raw 86.08 mA. The awake groups account for 52.965 mAh of qualified
software-counter decreases, versus 464.559 mAh in suspend brackets. Their sum
matches the previously qualified whole-session decreases for each counter.
A software-counter increase is excluded by the same qualification rules.

Thus removing the initial awake wait and inter-suspend awake gaps does not
remove the residual counter-estimated demand. This is still model-based charge
accounting, not a calibrated electrical current measurement. Endpoint updates
and gauge corrections prevent exact attribution of short awake gaps.

## A real Android calibration caller identified, execution unproven

An expanded static review inspected constant/dynamic-string sections in 296
vendor executables (32.4 MB, no execution). It found a relevant caller inside
hvdcp_opti, whose private binary SHA256 is
 eca52d713010f7768a28fe0123382495cae7303c1351e4f5e59c7834adf60f09.
The binary and disassembly remain private and are not included in Git.

ELF relative relocations and the setter's disassembly identify property 29 in a
24-byte property table: name calibrate, domain 2. The domain table maps 2 to
/sys/class/power_supply/bms/. At call 0x2dde4, index 29 is passed to the generic
setter at 0x3d0cc. The alternate IIO name is in_index_calibrate_level_input.
This is stronger than the earlier string-only search: the identified static
path can address the BMS calibration setter.

Its CP initialization is conditional. It probes charge_pump_master/model_name,
checks for SMB1390 and parallel-output mode, and also reads the Android
persist.vendor.cp.calib_force/calib_disable/calib_level properties. Failure to
read the model in the ordinary non-forced branch bypasses the calibration
write. Current Mobian exposes bq2597x-standalone, with no charge_pump_master,
parallel or /dev/qg. Alternative IIO dispatch and Android's active persistent
properties are not qualified by this inspection.

The current vendor defaults set persist.vendor.hvdcp_opti.disallowed=1; the
binary consults this in HVDCP strategy paths. This does not prove the entire
daemon is disabled or that its CP path never executes. Preserved full-Android
battery statistics do contain a process accounting entry for hvdcp_opti, which
establishes prior process activity, not calibration execution or its outcome.
No matching calibration-forcing default was found in the selected property files.

Only a small private SOH state file was found in the daemon's persist folder;
its contents were preserved without alteration. Its historical model values
must not be reported as a current physical battery-health percentage. Current
DT has multi-profile-load disabled, and the selected live profile is j11sun.
There is no demonstrated omitted age-profile switch in this readback.

No calibration, daemon startup, charge setting, hardware data register, build,
flash or new battery test was performed. The two-hour control remains declined;
no substitute repeated half-hour trial is pending. This caller is a bounded
Android-initialization comparison lead, not a confirmed fix.


### Calibration model-name gate qualified

Further static ELF table analysis identifies property 92 (model_name, domain 6)
as having no IIO fallback pointer. Resolver 0x3cd10 returns -EINVAL when the
charge_pump_master/model_name sysfs path is absent and this pointer is NULL;
the string getter propagates failure and CP initialization branches away at
0x2dd94, before the calibration setter. IIO support for other properties does
not rescue this particular lookup. A nonempty Android calibration-force
property can bypass it, and its runtime value remains unknown.

A bounded follow-up searched 44 preserved full-Android text/JSON records
(1,290,511 bytes): no calibration-force property or calibration-execution log
was found. The records confirm BQ2597x wake-lock and hvdcp_opti process activity,
not a successful calibration. Missing fields in these historical captures
prevent a negative execution claim. No new phone test or calibration write
is justified by this result alone.
