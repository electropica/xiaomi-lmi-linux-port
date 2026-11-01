# lmi Linux 7 PM8150B charger input current — host-checked candidate, November 1, 2026

## What this candidate is

The charger of this board runs entirely on the ROM defaults: no charger driver is bound
(`CONFIG_CHARGER_QCOM_SMB5` is absent from the configuration of the running kernel), so the PM8150B
charger block keeps the values the ROM programmed.

The measured consequence is the input current limit:

| Register | Value on 2026-10-30 | Meaning |
|---|---|---|
| `0x1370` USBIN_CURRENT_LIMIT_CFG | 10 | 500 mA ceiling |
| `0x1106` ICL_MAX_STATUS | 10 | 500 mA ceiling, read back |
| `0x1108` AICL_ICL_STATUS | 10 | 500 mA effective input limit |
| `0x110a` AICL_STATUS | 65 | AICL done, `SOFT_ILIMIT` set: the input voltage collapses at that limit |
| `0x1365` USBIN_LOAD_CFG | 0xb5 | `ICL_OVERRIDE_AFTER_APSD` set: the D+/D- detection imposes the limit |
| `0x1308` APSD_RESULT_STATUS | 0x01 | the detection sees SDP, because a Type-C source has no D+/D- signature |
| `0x1506` TYPE_C_SNK_STATUS | 0x04 | the source advertises Rp 1.5 A on CC |
| `0x110b` POWER_PATH_STATUS | 149 | a valid input, the system is fed through USBIN, the input is not suspended |

The USB-C connector of the board declares a 5000 mV / 3000 mA source PDO and the port TCPM
negotiated 5 V / 3 A. The system load of the running handset is above 500 mA, so the battery supplies
the difference: that is the "99 % then 96 % with the cable plugged in" capture of 2026-11-01, and it
is the same mechanism as the camera anomaly of the wall charger session of 2026-10-30.

The termination itself is normal: `0x1006` bits[2:0] = 5 (TERMINATE) with the float register
`0x1070` = 0x50, that is 3.6 V + 80 * 10 mV = 4.40 V, and the charge did terminate at 4.419 V on
2026-10-28. The automatic re-charge did resume on that date, when the battery went back below the
VBAT threshold of the ROM.

## What the candidate does

`patches/0005-lmi-pm8150b-charger-input-current.patch` corrects the community driver
`drivers/power/supply/qcom_pm8150b_charger.c`, which cannot be enabled as it is on this tree:

- the float voltage formula uses the 7.5 mV step of another PMIC, and would command 4.90 V for this
  cell (CAF 4.19 `smb5_pm8150b_params.fv`: 3.6 V base, 10 mV step, 4.79 V maximum). The register is
  not written any more; the ROM value of 4.40 V is kept;
- the driver asks for an interrupt named `usbin-plugin` while the board names it `usb-plugin`, so the
  probe would fail;
- the init sequence writes the Type-C block (0x1544 and neighbours), which the `qcom,pm8150b-typec`
  driver of this board owns, and the Type-C attach and detach detection of the port depends on it;
- the input current limit is selected from the D+/D- detection, which sees SDP and would keep the
  500 mA limit; the candidate follows the capability the source advertises on CC, capped at the
  3000 mA of the connector;
- the re-charge threshold is switched to SOC based, but the community fuel gauge never publishes its
  SOC to the charger; the candidate keeps the threshold driven by the battery voltage;
- `SUSPEND_ON_COLLAPSE_USBIN` is not written: a collapse of the input must not suspend the USB link,
  which is the only way to reach the handset.

`configs/charger-smb5.fragment` enables `CONFIG_CHARGER_QCOM_SMB5=y`. The driver then publishes the
`pm8150b-charger` power supply, which the fuel gauge driver of this board already looks up by name,
so the reported status becomes the charger state instead of a guess based on the sign of the current.

## What is host-checked

`tools/check-charger-patch.sh` applies the patch to the community tree that produced the running
handset kernel (the tree that carries the Type-C detach fix of commit 1553aee, with the camera,
GNSS, audio and MHI work), resolves the configuration with `merge_config.sh` and `olddefconfig`, and
checks the properties of the corrected driver. It does not compile and it does not flash. Result:
`CHARGER_CANDIDATE_HOST_CHECK_OK`.

`tools/build-community-charger-kernel.sh` is the operator recipe: it takes the same tree, applies
the patch, merges the fragment and builds the kernel and its device tree. `--prepare-only` stops
after the configuration merge, which is the part that was run here.

`tools/pm8150b-charger-targeted-read.py` is the read-only probe of the charger registers. It resolves
the regmap from the live device tree and verifies the PM8150B signature (the charger register 0x1006
and the fuel gauge register 0x4009 have to be in the same regmap) before reading anything; it never
scans the regmaps of the machine to guess which one is the right device, which is the defect of the
older MSOC trajectory script. `tools/test-pm8150b-targeted-read.py` checks that behaviour offline.

## What is not qualified

- Nothing was compiled and nothing was flashed. The build and the handset trial are the operator's
  steps.
- The limit the kernel applies is the Rp of the source, 1.5 A on the 2026-10-30 capture. The 3 A of
  the PD contract is negotiated by the userspace TCPM and is not exposed to the kernel.
- The float voltage stays at the ROM value of 4.40 V. The `voltage-max-design-microvolt = 4460000`
  of the board device tree is the design maximum of the cell, not necessarily the charge voltage
  retained by the vendor. `work/minimax-lmi-charge-termination-20261101/patches/0002-qcom-pm8150b-charger-float-voltage-scale.patch`
  corrects the scale and would program 4.46 V; it conflicts with this candidate on that hunk and has
  to be arbitrated explicitly. Until the float moves, the gauge tops out below 0xff, so a visible
  100 % stays out of reach and the MSOC display candidate stays dormant.
- The VBAT re-charge threshold of the ROM (0x107e / 0x107f) was never read; the probe measures it.
- The cell charge current is not programmed: the device tree declares no
  `constant-charge-current-max-microamp`.

See also `work/battery-review-20261101/RAPPORT-CHARGE-STOP-20261101.md` and
`work/battery-review-20261101/msoc-candidate-review.md`.
