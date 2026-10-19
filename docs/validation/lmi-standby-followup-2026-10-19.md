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
