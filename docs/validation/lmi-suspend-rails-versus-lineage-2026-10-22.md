# What stays on while the processor is down: the Mobian rails against LineageOS

## What is compared here, and what is not

Two things are compared, from the evidence already kept, both offline:

* the **suspend path** of each platform, that is the rails each platform
  disables while it goes down, taken from the trace analysis already
  recorded in `minimax-rpmh-audit-20261022/regulator-inventory.json`;
* the **always requested rails** of Mobian and their consumers, from the
  point-in-time regulator summary kept in
  `evidence/captures/regulator-mobian-20261022T165333.txt`.

Two things are **not** available and are not replaced by an assumption:

* there is **no point-in-time regulator summary for LineageOS** in the
  kept packet. `lineage-power-trace-20261022-private/snapshot.txt` holds
  only the error of the missing tracing instance, so the Android
  always-on set is unknown;
* no rail current is measured anywhere. Every `current` column of the
  Mobian summary reads 0 mA, the regulator framework does not report
  currents on this platform.

## The suspend path, Mobian against LineageOS

From the inventory's comparison, for the one Mobian trial whose trace is
complete (`wide-regulator-observer-20261012-private`, the other Mobian
trials have no complete trace and no usable window):

| | rails disabled in the suspend path |
|---|---|
| Mobian | display_panel_vci, pm8150_l14, pm8150_l17, pm8150_l9, pm8150_s3_level, pm8150_s3_mmcx_sup_level, pm8150a_s3_level, pm8150a_s3_mmcx_sup_level, pm8150a_s4_level, refgen, ufs_phy_gdsc |
| LineageOS | gpu_cx_gdsc, pm8150_l17, pm8150_l9, pm8150_s3_level, pm8150_s3_mmcx_sup_level, pm8150a_s3_level, pm8150a_s3_mmcx_sup_level, pm8150a_s4_level, ufs_phy_gdsc |

Only in Mobian: `display_panel_vci`, `pm8150_l14`, `refgen`. Only in
LineageOS: **`gpu_cx_gdsc`**, the GPU core rail.

Read carefully, the software difference points the other way on two of
the three: Mobian disables the two panel rails and the reference clock
generator in the suspend path, and LineageOS does not. The one rail that
LineageOS disables and Mobian does not is the GPU core rail.

The caveat of the inventory applies without reservation: a state
transition observed around the suspend is a **software** transition, it
is not proof of an electrical state during the powered-down interval.

## The Mobian always-on rails

From the point-in-time summary, the rails whose only consumer is
`deviceless`, that is requested from the device tree or the bootloader
and never released: `vdd_boost_vreg`, `pm8150_s5` and `pm8150_s6` (the
WLAN rails), `pm8150_l2` (the USB-PD rail), `pm8150_l5`, `pm8150_l5_ao`
and `pm8150_l12_ao` (the CPU `limits-dcvs` rails), `pm8150_l9`,
`pm8150_l12`, `pm8150_l14` and `display_panel_vci` (the panel rails),
`pm8150_l17`, `pm8150a_l1` (the touch controller), `pm8150a_s8`,
`pm8150a_bob` (the camera rails), `pm8009_s2`, `pcie_0_gdsc`,
`usb30_prim_gdsc`, `hsphy@88e3000` (the USB HS PHY) and
`regulator-dummy`.

`vdd_boost_vreg` is the one the project has followed since 12 October:
use=1, open=1, a single `deviceless` consumer.

**The important observation is the opposite of a lead.** A `deviceless`
consumer means the request comes from the device tree or from the
bootloader, and the device tree is the same on the two platforms: the
Mobian and the LineageOS images run the same `live.dtb` and the same
menu dtbo, which are kept in the private area. An always-on rail that
comes from the shared device tree is very likely always-on on
LineageOS too, and an always-on rail on both platforms cannot by itself
explain a difference between them.

That removes the most obvious candidate, `vdd_boost_vreg`, as an
explanation of the difference: it is a rail both platforms hold.

## What remains, and what is still missing

The candidate that survives the comparison is the GPU core rail:
LineageOS disables `gpu_cx_gdsc` in its suspend path and Mobian does
not. That is a software difference in the suspend path, and it is a
candidate, not a cause: nothing here says how much current that rail
costs, and the regulator framework reports no currents.

Three things are missing, and none of them can be replaced by an
argument:

1. the **point-in-time regulator summary of LineageOS in the unplugged
   state**, so that the two always-on sets can be compared rail by rail
   in the state that matters;
2. the **Mobian regulator summary in the unplugged state**, that is
   which rails are still requested once the cable is out, which the
   point-in-time capture cannot answer because it was taken with the
   cable connected;
3. any **electrical measurement of a rail** during a suspend. The
   framework does not provide one here.

## The one discriminating verification proposed

**Read the regulator summary in the unplugged state on both platforms,
and compare the rail sets.** It is a read-only command, it changes
nothing, it disables nothing, and it is the only step that separates
"a rail that both platforms hold" from "a rail only Mobian holds". On
Mobian it is one `cat /sys/kernel/debug/regulator/regulator_summary`
during a short unplug; on LineageOS the same.

It is proposed, not scheduled. No new unplug is arranged for now, and
nothing is disabled. The night run in progress gives the counter and
the duty cycle over a full night, which is the other half of the
question, but it does not touch the rails.

## Limits

* The Mobian summary is a point-in-time snapshot taken 110 s after a
  boot with the cable connected. It describes the rails that are
  requested, not the rails that carry current.
* The suspend-path lists come from two different dates and two different
  builds: the Mobian trial is from 12 October, the LineageOS trace is
  from 2026-10-07.
* The 12 October Mobian observer artefacts record no kernel release
  string, so they are not certified to be the current build.
* No electrical measurement exists, so nothing here is a current
  measurement and nothing here designates a responsible party.
