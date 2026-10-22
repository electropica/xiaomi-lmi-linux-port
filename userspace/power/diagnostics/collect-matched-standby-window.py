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
unplugged suspend cannot be observed over it. The collector therefore runs
on the phone, is started before the cable is removed and stopped after it is
reconnected, and writes one small JSON file.

What it reads. The gauge counters, the USB attach state and the UFS
suspend-policy attributes. All read-only.

Revision 2, after the independent review of 2026-10-22. The previous
revision was not usable and its numbers must not be quoted:

  * clocks() read /proc/uptime and treated its two fields as CLOCK_BOOTTIME
    and CLOCK_MONOTONIC. The second field of /proc/uptime is the aggregate
    CPU idle time, not CLOCK_MONOTONIC. Every suspended-time value and every
    suspend detection derived from it was therefore invalid. The clocks are
    now read with time.clock_gettime(CLOCK_BOOTTIME) and
    time.clock_gettime(CLOCK_MONOTONIC), and the collector refuses to run
    when either clock is unavailable.
  * The wall-clock deadline is now taken on CLOCK_BOOTTIME, which keeps
    counting across a suspend. No RTC wake alarm is armed: a userspace
    deadline cannot be enforced while the processor is down, so the bound is
    applied at the next resume and the elapsed time includes the suspended
    time.
  * Suspend events are kept as a bounded sequence instead of only the first
    one, so a window can be reported event by event.
  * The counter is treated as a gauge reading, not as an instantaneous
    measurement of a suspended interval, and the discontinuity observed
    around a USB unplug is preserved rather than explained away.
  * --poll and --max-seconds reject non-positive and non-finite values, and
    the sampling overhead of a polling collector is documented.

It only reads. It writes its own output file and nothing else. It changes no
policy, no service, no register and no setting, and it has no restoration
step because it has no effect to restore.

Usage, on the phone, as the mobile user:

    python3 collect-matched-standby-window.py --execute --out /tmp/standby-window.json

Start it, unplug, let the phone suspend and wake on its own, replug, then
stop it. The collector reports the gauge numbers, the suspended intervals and
the events it saw. It only reads.
"""

import argparse
import json
import math
import os
import sys
import time

GAUGE = "/sys/class/power_supply/battery"
UFS = "/sys/bus/platform/devices/1d84000.ufshc"
REG_SUMMARY = "/sys/kernel/debug/regulator/regulator_summary"

MAX_EVENTS = 512


class ClockUnavailable(RuntimeError):
    """The platform does not expose the clocks this measurement needs."""


def clocks():
    """Return (boottime, monotonic) in seconds.

    CLOCK_BOOTTIME keeps counting across a suspend, CLOCK_MONOTONIC stops,
    so their difference is the time the processor spent down. /proc/uptime
    cannot be used for this: its second field is the aggregate CPU idle
    time, which is a different quantity entirely.
    """
    if not hasattr(time, "clock_gettime"):
        raise ClockUnavailable("time.clock_gettime is not available")
    for name in ("CLOCK_BOOTTIME", "CLOCK_MONOTONIC"):
        if not hasattr(time, name):
            raise ClockUnavailable("time.%s is not available" % name)
    return (time.clock_gettime(time.CLOCK_BOOTTIME),
            time.clock_gettime(time.CLOCK_MONOTONIC))


def suspended_total(sample):
    """Approximate seconds the processor has been down since boot.

    This is the difference between the two clocks of one reading. The
    monotonic clock is slewed by the timekeeping layer and the boot clock
    is not, so the difference drifts slowly and can even be slightly
    negative on a host that never suspended. It is therefore never used on
    its own: a suspend is the change of this value between two readings,
    which cancels the drift.
    """
    return sample["boottime"] - sample["monotonic"]


def suspend_gap(previous, current, threshold):
    """Seconds the processor was down between two samples, 0 if it stayed up.

    A gap is the growth of the suspended total between two readings. It is
    bounded by the poll interval: a suspend shorter than the interval is
    merged into the awake time and cannot be told apart from it.
    """
    gap = suspended_total(current) - suspended_total(previous)
    if gap < threshold:
        return 0.0
    return gap


def classify(previous, current, threshold):
    """Return the event between two samples, or None if nothing happened."""
    gap = suspend_gap(previous, current, threshold)
    if gap <= 0.0:
        return None
    return {
        "type": "suspend_gap",
        "wall_utc_start": previous["wall_utc"],
        "wall_utc_end": current["wall_utc"],
        "boottime_start": previous["boottime"],
        "boottime_end": current["boottime"],
        "monotonic_start": previous["monotonic"],
        "monotonic_end": current["monotonic"],
        "suspended_seconds": round(gap, 3),
        "awake_seconds_between_reads": round(
            current["monotonic"] - previous["monotonic"], 3),
        "counter_before": previous.get("charge_counter"),
        "counter_after": current.get("charge_counter"),
        "usb_attached_start": previous.get("usb_attached"),
        "usb_attached_end": current.get("usb_attached"),
    }


class Window(object):
    """The observed state of one standby window.

    Events are kept as a sequence so that a window with several suspends is
    reported event by event, instead of only the first suspend being kept.
    """

    def __init__(self, threshold=1.0, max_events=MAX_EVENTS):
        self.threshold = threshold
        self.max_events = max_events
        self.events = []
        self.events_truncated = False
        self.first = None
        self.last = None

    def observe(self, sample):
        if self.first is None:
            self.first = sample
            self.last = sample
            return None
        previous = self.last
        self.last = sample
        event = classify(previous, sample, self.threshold)
        if event is None:
            if previous.get("usb_attached") != sample.get("usb_attached"):
                event = {
                    "type": "usb_transition",
                    "wall_utc_start": previous["wall_utc"],
                    "wall_utc_end": sample["wall_utc"],
                    "usb_attached_start": previous.get("usb_attached"),
                    "usb_attached_end": sample.get("usb_attached"),
                    "counter_before": previous.get("charge_counter"),
                    "counter_after": sample.get("charge_counter"),
                }
            else:
                return None
        if len(self.events) >= self.max_events:
            self.events_truncated = True
            return None
        self.events.append(event)
        return event

    def suspend_events(self):
        return [e for e in self.events if e["type"] == "suspend_gap"]

    def suspended_seconds(self):
        return sum(e["suspended_seconds"] for e in self.suspend_events())


def read(path):
    try:
        with open(path, "r", errors="replace") as fh:
            return fh.read().strip()
    except OSError as exc:
        return "ERR:%d" % (exc.errno or 0)


def usb_state():
    """Best effort USB state.

    On this platform the USB gadget appears as a network link, not only as a
    `power_supply/usb` node, so both are probed. The unplug is detected on
    either: the power-supply `online` flag falling to 0, or the USB network
    interface losing its carrier. The loopback interface always reports
    carrier=1 and must not be counted.
    """
    online = []
    usb_online = None
    for d in sorted(os.listdir("/sys/class/power_supply")):
        p = os.path.join("/sys/class/power_supply", d, "online")
        if os.path.exists(p):
            value = read(p)
            online.append("%s=%s" % (d, value))
            if d == "usb":
                usb_online = value
    links = []
    try:
        for name in sorted(os.listdir("/sys/class/net")):
            if not name.startswith("usb"):
                continue
            carrier = read(os.path.join("/sys/class/net", name, "carrier"))
            if carrier == "1":
                links.append(name)
    except OSError:
        pass
    return {"usb_power_supply": online, "usb_online": usb_online,
            "usb_links_up": links}


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
                 "charge_full_design", "status", "temp", "voltage_now",
                 "current_now"):
        out[name] = read(os.path.join(GAUGE, name))
    usb = usb_state()
    out["usb_power_supply"] = usb["usb_power_supply"]
    out["usb_online"] = usb["usb_online"]
    out["usb_links_up"] = usb["usb_links_up"]
    out["usb_attached"] = (usb["usb_online"] == "1") or bool(usb["usb_links_up"])
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
    out["ufs_max_bus_w"] = read(os.path.join(UFS, "max_bus_w"))
    out["regulator_summary_present"] = os.path.exists(REG_SUMMARY)
    return out


def positive_finite(text):
    """argparse type: a strictly positive, finite number."""
    try:
        value = float(text)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("not a number: %r" % (text,))
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("must be finite: %r" % (text,))
    if value <= 0:
        raise argparse.ArgumentTypeError("must be strictly positive: %r" % (text,))
    return value


def deadline_reached(boottime, deadline):
    """True when the wall-clock deadline, taken on CLOCK_BOOTTIME, is past.

    CLOCK_BOOTTIME keeps counting while the processor is down, so the
    deadline bounds the real elapsed time of the window and not only the
    time the collector was running. A userspace deadline cannot be enforced
    while the processor is down: the check happens at the next resume, and
    no RTC wake alarm is armed to make it happen sooner.
    """
    return boottime >= deadline


def build_result(window, started, ended, deadline, args):
    """Assemble the JSON result from the observed window."""
    events = window.events
    suspends = window.suspend_events()
    attached = [e for e in events if e["type"] == "usb_transition"]
    unplug = None
    replug = None
    for e in attached:
        if e["usb_attached_start"] and not e["usb_attached_end"]:
            unplug = e
        elif not e["usb_attached_start"] and e["usb_attached_end"]:
            replug = e
    elapsed = None
    if window.first and window.last:
        elapsed = window.last["boottime"] - window.first["boottime"]
    suspended = window.suspended_seconds()
    fraction = None
    if elapsed:
        fraction = suspended / elapsed

    result = {
        "collector": "collect-matched-standby-window",
        "version": 2,
        "started_utc": started["wall_utc"],
        "ended_utc": ended["wall_utc"],
        "wall_seconds_observed": round(elapsed, 3) if elapsed else None,
        "deadline_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                      time.gmtime(deadline)),
        "poll_seconds": args.poll,
        "suspend_threshold_seconds": args.threshold,
        "events": events,
        "events_truncated": window.events_truncated,
        "suspend_events": suspends,
        "suspend_event_count": len(suspends),
        "suspended_seconds_total": round(suspended, 3),
        "suspended_fraction_of_window": (
            round(fraction, 6) if fraction is not None else None),
        "unplug_event": unplug,
        "replug_event": replug,
        "before": started,
        "after": ended,
        "clock": {
            "source": "time.clock_gettime(CLOCK_BOOTTIME) and "
                      "time.clock_gettime(CLOCK_MONOTONIC)",
            "suspended_total_definition": "CLOCK_BOOTTIME minus "
                                          "CLOCK_MONOTONIC, per sample",
            "detection": "A suspend is the growth of that difference "
                         "between two readings, compared with "
                         "--threshold. The difference is never used on its "
                         "own, because the monotonic clock is slewed by the "
                         "timekeeping layer and the boot clock is not, so "
                         "the two drift apart slowly.",
            "note": "The previous revision read /proc/uptime, whose second "
                    "field is aggregate CPU idle time and not CLOCK_MONOTONIC. "
                    "Its suspended times and suspend detections were invalid "
                    "and are not comparable with this file.",
        },
        "counter": {
            "read_before_unplug": unplug["counter_before"] if unplug else None,
            "read_after_unplug": unplug["counter_after"] if unplug else None,
            "read_at_replug": replug["counter_after"] if replug else None,
            "jump_across_unplug_uah": (
                _int_or_none(unplug["counter_after"]) -
                _int_or_none(unplug["counter_before"]))
            if unplug and _int_or_none(unplug["counter_after"]) is not None
            and _int_or_none(unplug["counter_before"]) is not None else None,
            "note": "The counter is a gauge value, not an instantaneous "
                    "measurement of the suspended interval. The readings "
                    "bracket awake time around every event, and this "
                    "platform shows a discontinuity in the counter around a "
                    "USB unplug. The Android reference excludes an "
                    "equivalent jump before computing its quotient; the same "
                    "treatment is required here, and the raw readings are "
                    "preserved above so it can be applied.",
        },
        "estimators": {
            "sleep_window_net": "For each suspend event, the counter delta "
                                 "between the two bracketing reads over the "
                                 "suspended seconds of that event. The two "
                                 "reads are taken while the processor is up, "
                                 "so the delta also contains the awake time "
                                 "around the event and any counter "
                                 "discontinuity. It is an event-by-event "
                                 "estimate, not a calibrated sleep current.",
            "window_net": "The counter delta between the unplug reading and "
                          "the replug reading over the whole unplugged "
                          "interval, with the jump across the unplug "
                          "reported separately. The interval contains awake "
                          "time as well as suspended time.",
            "not_computed_here": "No current in mA is computed by the "
                                 "collector. The scale of this gauge counter "
                                 "relative to the design capacity is not "
                                 "established, so a quotient in mA would "
                                 "carry an unresolved factor.",
        },
        "method": "The Android reference needs three points: the counter at "
                  "the unplug, the counter after the sleep and the suspended "
                  "interval, so that the counter discontinuity at the unplug "
                  "can be excluded exactly as the reference does. This "
                  "collector records every sample, every suspend event and "
                  "every USB transition, and preserves the readings so the "
                  "same exclusion can be applied offline.",
        "limits": "Gauge counters, not a calibrated current. The counter "
                  "path, the capacity scale and the unplug discontinuity "
                  "handling must be applied exactly as in the Android "
                  "reference before any comparison; a single run does not "
                  "establish an average. A polling collector wakes the "
                  "processor every --poll seconds, and a suspend shorter "
                  "than that interval cannot be told apart from awake time. "
                  "No RTC wake alarm is added, so a window that needs a "
                  "wake source to end may overrun its deadline. Regulator "
                  "and UFS values are configuration and bookkeeping, not "
                  "electrical state.",
    }
    return result


def _int_or_none(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def write_result(path, result):
    with open(path, "w") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--execute", action="store_true",
                    help="actually collect; without it the plan is printed only")
    ap.add_argument("--out", default="/tmp/standby-window.json")
    ap.add_argument("--poll", type=positive_finite, default=5.0,
                    help="seconds between two samples, strictly positive")
    ap.add_argument("--max-seconds", type=positive_finite, default=7200.0,
                    help="wall-clock bound taken on CLOCK_BOOTTIME")
    ap.add_argument("--threshold", type=positive_finite, default=1.0,
                    help="minimum suspended gap, in seconds, to report an "
                         "event")
    args = ap.parse_args()

    if not args.execute:
        print("PLAN (nothing is read, nothing is written)")
        print("  on the phone, as the mobile user:")
        print("    python3 %s --execute --out %s"
              % (os.path.basename(__file__), args.out))
        print("  then: start it, unplug, let the phone suspend and wake by")
        print("  itself, replug, stop it. The collector reports the matched")
        print("  gauge numbers and the suspended intervals. It only reads.")
        return 0

    try:
        boottime, monotonic = clocks()
    except ClockUnavailable as exc:
        print("REFUSED: %s" % exc, file=sys.stderr)
        print("The suspended-time measurement needs CLOCK_BOOTTIME and "
              "CLOCK_MONOTONIC. Refusing to collect.", file=sys.stderr)
        return 2

    deadline = boottime + args.max_seconds
    started = sample("before")
    print("before:", json.dumps(started, sort_keys=True), flush=True)

    window = Window(threshold=args.threshold)
    window.observe(started)
    result = None
    while not deadline_reached(clocks()[0], deadline):
        time.sleep(args.poll)
        now = sample("poll")
        event = window.observe(now)
        if event is not None:
            print("%s: %s" % (event["type"], json.dumps(event, sort_keys=True)),
                  flush=True)
            # Write after every event so a window that is interrupted still
            # leaves the readings it had collected on the device.
            ended = now
            result = build_result(window, started, ended, deadline, args)
            write_result(args.out, result)
        if event is not None and event["type"] == "usb_transition":
            if event["usb_attached_end"]:
                print("replug observed", flush=True)
                break
    ended = sample("after")
    result = build_result(window, started, ended, deadline, args)
    write_result(args.out, result)
    print("written:", args.out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
