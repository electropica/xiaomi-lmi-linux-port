#!/usr/bin/env python3
"""Read-only local collector for one matched standby window on Mobian.

Why this exists. The whole standby comparison still rests on two different
accounting methods: a Mobian estimate against a LineageOS estimate. The
LineageOS reference (docs/validation/LINEAGE-POWER-TRACE-20261022.md) yields
13.84 mA net and 15.72 mA summed downward after excluding the counter
discontinuity at unplug. The Mobian side never produced a number by that
method. A matched Mobian number would turn the comparison into one method on
two platforms.

Why it has to run locally. The SSH route needs the cable connected, so an
unplugged suspend cannot be observed over it. The collector therefore runs on
the phone, is started before the cable is removed and stopped after it is
reconnected, and writes one small JSON file.

It only reads. It writes its own output file and nothing else. It changes no
policy, no service, no register and no setting, and it has no restoration
step because it has no effect to restore.

Usage, on the phone, as the mobile user:

    python3 collect-matched-standby-window.py --execute --out /tmp/standby-window.json

Start it, unplug, let the phone suspend and wake on its own, replug, then
stop it. The collector detects the suspend from the divergence between
CLOCK_BOOTTIME and CLOCK_MONOTONIC, which is the same signal the project
already uses in its observer, and samples the gauge on both sides of it.
"""

import argparse
import json
import os
import time

GAUGE = "/sys/class/power_supply/battery"
UFS = "/sys/bus/platform/devices/1d84000.ufshc"
REG_SUMMARY = "/sys/kernel/debug/regulator/regulator_summary"


def read(path):
    try:
        with open(path, "r", errors="replace") as fh:
            return fh.read().strip()
    except OSError as exc:
        return "ERR:%d" % (exc.errno or 0)


def clocks():
    """CLOCK_BOOTTIME keeps running across a suspend, CLOCK_MONOTONIC does not.
    The difference is the suspended time."""
    with open("/proc/uptime", "r") as fh:
        parts = fh.read().split()
    return float(parts[0]), float(parts[1])


def sample(label):
    boottime, monotonic = clocks()
    out = {
        "label": label,
        "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "boottime": boottime,
        "monotonic": monotonic,
        "suspended_accumulated": boottime - monotonic,
    }
    for name in ("capacity", "charge_counter", "charge_full",
                 "charge_full_design", "charge_now", "status", "temp",
                 "voltage_now", "current_now", "usb_online"):
        out[name] = read(os.path.join(GAUGE, name))
    out["ufshc_runtime_status"] = read(os.path.join(UFS, "power", "runtime_status"))
    for attr in ("clkgate_enable", "clkgate_delay_ms", "rpm_lvl", "spm_lvl",
                 "auto_hibern8", "rpm_target_link_state",
                 "rpm_target_dev_state", "spm_target_link_state",
                 "spm_target_dev_state"):
        out["ufs_" + attr] = read(os.path.join(UFS, attr))
    out["ufs_psa_state"] = read(os.path.join(UFS, "attributes", "psa_state"))
    out["ufs_current_power_mode"] = read(
        os.path.join(UFS, "attributes", "current_power_mode"))
    out["ufs_power_mode"] = read(os.path.join(UFS, "qcom", "power_mode"))
    out["ufs_max_bus_bw"] = read(os.path.join(UFS, "max_bus_bw"))
    out["regulator_summary_present"] = os.path.exists(REG_SUMMARY)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--execute", action="store_true",
                    help="actually collect; without it the plan is printed only")
    ap.add_argument("--out", default="/tmp/standby-window.json")
    ap.add_argument("--poll", type=float, default=5.0)
    ap.add_argument("--max-seconds", type=float, default=7200.0)
    args = ap.parse_args()

    if not args.execute:
        print("PLAN (nothing is read, nothing is written)")
        print("  on the phone, as the mobile user:")
        print("    python3 %s --execute --out %s"
              % (os.path.basename(__file__), args.out))
        print("  then: start it, unplug, let the phone suspend and wake by")
        print("  itself, replug, stop it. The collector reports the matched")
        print("  gauge numbers and the suspended interval. It only reads.")
        return 0

    started = sample("before")
    print("before:", json.dumps(started, sort_keys=True), flush=True)

    deadline = time.monotonic() + args.max_seconds
    seen_suspend = False
    at_unplug = None
    previous = started
    while time.monotonic() < deadline:
        time.sleep(args.poll)
        now = sample("poll")
        # the counter jumps exactly at the unplug; keep that sample so the
        # Android reference method can exclude the discontinuity
        if (at_unplug is None
                and previous.get("usb_online") == "1"
                and now.get("usb_online") == "0"):
            at_unplug = now
            print("unplug observed", flush=True)
        delta = now["suspended_accumulated"] - started["suspended_accumulated"]
        if delta >= max(args.poll, 1.0):
            # the monotonic clock lost time: a suspend happened
            seen_suspend = True
            started = now
            print("suspend detected, delta=%.3f" % delta, flush=True)
            break
        previous = now
    after = sample("after")

    result = {
        "collector": "collect-matched-standby-window",
        "version": 1,
        "started_utc": started["wall_utc"],
        "ended_utc": after["wall_utc"],
        "suspend_detected": seen_suspend,
        "at_unplug": at_unplug,
        "suspended_seconds_estimate": round(
            after["suspended_accumulated"] - started["suspended_accumulated"], 3),
        "before": started,
        "after": after,
        "method": "The Android reference needs three points: the counter at "
                  "the unplug, the counter after the sleep and the suspended "
                  "interval, so that the counter discontinuity at the unplug "
                  "can be excluded exactly as the reference does. The "
                  "'at_unplug' sample is the one observed by the poll that "
                  "sees usb_online fall from 1 to 0; it is null if the "
                  "unplug was not observed.",
        "limits": "Gauge counters, not a calibrated current. The counter path, "
                  "the capacity scale and the unplug discontinuity handling "
                  "must be applied exactly as in the Android reference before "
                  "any comparison; a single run does not establish an average."
                  "Regulator and UFS values are configuration and bookkeeping, "
                  "not electrical state.",
    }
    with open(args.out, "w") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
    print("written:", args.out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
