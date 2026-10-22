# Collector revision 4: the discharge endpoint is qualified, the snapshot is one-shot

## Why

The independent revision 3 review of 2026-10-22 confirmed the fixes of
revision 3 and found two defects in it, plus one small source defect. It
also said not to deploy until the endpoint handling is qualified. This
note records what was changed, what the tests show, and what is still
missing.

## Defect 1: a failed read was read as an offline source

Revision 3 computed:

```python
out["usb_power_attached"] = (usb["usb_online"] == "1")
out["detached"] = not out["usb_power_attached"]
```

An online flag that reads "1" means the source is present, "0" means it
is not, and anything else is unknown: a missing node, a denied read, a
read that failed. Revision 3 read every unknown as "not 1", that is as
absent, and then qualified a discharge endpoint on that absence.

The counterexample the review gives is exact: with the online flag
reading `ERR:13` and the gauge reporting `Charging`, revision 3 produced
a detached sample and kept that charging counter as a discharge endpoint.
The other power sources were recorded but never checked, so a phone
charging from the DC input would still have qualified.

Revision 4 qualifies the endpoint explicitly, and it needs three
independent things, because the measurement is made over a USB cable:

* the USB power path must be **validated offline**, that is its raw
  online flag must read exactly "0";
* every other power source that exposes an online flag must be **known**
  and **not online**; on this device that is `dc` and `pc_port`;
* the gauge must report **Discharging**, because a Charging or Full
  reading means the counter can move back up towards `charge_full`.

Any unknown or failed reading disqualifies the sample. The evidence is
kept either way, with the reason it was rejected, and the reasons are
counted in the result. A reported offline USB node is still not
independent proof of a physically unplugged phone, and the result says
so.

The reading is tri-state now: `usb_power_attached` is `True`, `False` or
`None` for unknown. The boolean `usb_attached` stays what it was, a
proxy built from the power state and the carrier of the USB links.

The samples that qualify are the only ones kept as endpoints. The
pre-replug disconnected samples are therefore the endpoints, and a
reading taken after the reconnection, which is a charging-side reading,
is not one.

## Defect 2: the optional snapshot was not one-shot

With `--ufs-hardware-snapshot`, revision 3 called `ufs_hardware_snapshot()`
at the start **and again after every event**. Each of those two reads
runtime-resumes the UFS device and sends a UPIU attribute query, so the
option reintroduced exactly the perturbation it exists to isolate. The
snapshot is now taken at most once per run and reused.

The default mode never made those queries, so this defect is not proof
that a default run was perturbed.

## The small defect: the attribute name

The collector read `max_bus_w`. The driver creates `max_bus_bw`
(`ufs-qcom-mobian-a5b3099017ae.c`, a stored vote exposed read-only), so
the old name always returned an error. Checked on the device:
`/sys/bus/platform/devices/1d84000.ufshc/max_bus_bw` reads 0 and
`max_bus_w` does not exist. The correct name is used now.

## The tests

The offline suite now holds **38 tests**. The endpoint tests are driven
from **simulated raw readings**, not from a preconstructed boolean: the
test replaces the read helper and the list of power supplies that expose
an online flag, so the real classification runs on raw strings, including
the error strings the read helper produces.

| collector | result |
|---|---|
| revision 4 | **38 tests, 0 failures** |
| revision 3 (`ab1ab69`) | 38 tests, **12 failures** |
| revision 2 (`2eb21f3`) | 38 tests, **12 failures** |

The twelve failures against the previous revisions are the new tests:
the counterexample of the review (`usb_online` reading `ERR:13` with the
gauge reporting `Charging`), the charging reading, the full reading,
another source online, another source unknown, the missing USB node, the
validated offline reading, the endpoint bookkeeping, the transport and
power separation, the snapshot read count, and the attribute name. The
snapshot test fails on revision 3 with the message "the snapshot was read
2 times", which is the defect itself.

The other suite, `test-ufs-policy-reader.py`, still passes with 10 tests.
No phone is contacted by any of it.

## What was not touched

No interrupt is disabled, no gauge processing is suppressed, the charge
protections are unchanged, the normal sleep delay is unchanged, and the
Phosh and GSD thresholds are unchanged. The `50000` threshold is 50 ms,
not 50 s, and it was not modified. Nothing was built, installed or
deployed.

## Limits

* Revision 4 has not run on a handset. Nothing about the physical
  standby draw follows from it.
* The qualification is deliberately conservative: a reading that cannot
  be qualified is kept as evidence with its reason and is not offered as
  an endpoint. A lost endpoint is a missing measurement, a wrongly
  qualified one is a wrong measurement.
* The set of power sources is whatever exposes an online flag on the
  device; on this one it is `usb`, `dc` and `pc_port`.
* The USB offline signal is the best this protocol has, and it is not
  independent proof of a physical unplug.
* The window remains a gauge reading, with no calibrated current and no
  established scale against the design capacity.

## Next

Deploy revision 4 and run the second window, with a fixed
operator-visible maximum duration, and keep the pre-replug disconnected
samples as the endpoints.
