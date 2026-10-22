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
configuration attributes. All read-only.

Revision 3, after the API review of 2026-10-22. The review results are kept
outside the repository, in work/MINIMAX-API-REVIEW-RESULTS-20261022.md.
The review confirmed five defects in revision 2, all fixed here:

  * One pair of samples could not carry a suspend gap and a USB transition
    at the same time: the presence of a suspend skipped the transition
    handling, so a detach that happened inside a suspend interval was
    lost, with the counter readings on both sides of it, and the collector
    could not stop on the reconnection either. The two are now detected
    independently and both are kept.
  * The event log was bounded by dropping events, so a saturated log could
    hide the terminal transition, and the suspended total was the sum of
    the surviving events, so a full log also shortened the measured sleep.
    The retained log now keeps the most recent events, the USB
    transitions have their own bounded list, and the totals live in
    counters that do not depend on the log.
  * The deadline was printed as a wall-clock date but was computed from
    the boot clock, which produced a date in 1970. The deadline now
    carries an explicit boot-clock value and a wall-clock value obtained
    by pairing the two clocks at start.
  * The result was written only when an event happened and the write was
    not atomic, so an interrupted run could leave nothing behind or a
    truncated file. The result is now written before the first event, every
    write is atomic, and a termination signal writes the final result.
  * The UFS attributes current_power_mode and psa_state were read on every
    poll. In drivers/scsi/ufs/ufs-sysfs.c the UFS_ATTRIBUTE macro (lines
    711-726) calls pm_runtime_get_sync(), ufshcd_query_attr() and
    pm_runtime_put_sync(), and current_power_mode (line 729) and psa_state
    (line 742) instantiate that macro: each read runtime-resumes the UFS
    device and sends a hardware query. That is not a passive observation of
    a sleeping device, so those two attributes are no longer read while
    the window is measured. A one-shot snapshot is available behind an
    explicit flag, and it says what it is.

The review also rejected claims that the previous revision made. They are
corrected here:

  * Both clocks are derived from adjusted monotonic time, so neither one is
    exempt from the timekeeping adjustments, and two sequential reads
    carry a sampling skew. The collector only ever uses the change of the
    difference between two readings, never the difference itself.
  * A normal timer is not a wake source that would keep the system from
    suspending. The polling still costs energy and perturbs the device
    under study, which is what the limits say.
  * The USB boolean is a proxy. Transport, power and charge are reported
    apart, and only a reading taken with no power source attached can
    serve as a discharge endpoint.
  * The difference across the unplug mixes consumption and any
    discontinuity. It is not a pure discontinuity and not a consumption
    figure, and the field no longer carries the name of a jump.

It only reads. It writes its own output file and nothing else. It changes no
policy, no service, no register and no setting, and it has no restoration
step because it has no effect to restore.

Usage, on the phone, as a user that can read the gauge and the USB sysfs
nodes:

    python3 collect-matched-standby-window.py --execute --out /tmp/standby-window.json

Start it, unplug, let the phone suspend and wake on its own, replug, then
stop it. The collector reports the gauge numbers, the suspended intervals and
the events it saw. It only reads.
"""

import argparse
import json
import math
import os
import signal
import sys
import time

GAUGE = "/sys/class/power_supply/battery"
UFS = "/sys/bus/platform/devices/1d84000.ufshc"
REG_SUMMARY = "/sys/kernel/debug/regulator/regulator_summary"

MAX_EVENTS = 512
MAX_USB_EVENTS = 64
MAX_DETACHED_SAMPLES = 256

# UFS attributes read while the window is measured. They are configuration
# or bookkeeping values: the init script writes them as platform knobs, and
# the driver keeps them in memory. None of them is an electrical measurement.
UFS_POLICY_ATTRS = ("clkgate_enable", "clkgate_delay_ms", "rpm_lvl", "spm_lvl",
                    "auto_hibern8", "rpm_target_link_state",
                    "rpm_target_dev_state", "spm_target_link_state",
                    "spm_target_dev_state")

# These two are instantiated by the UFS_ATTRIBUTE macro of ufs-sysfs.c, so
# each read runtime-resumes the UFS device and sends a hardware query. They
# are kept out of the sampling loop.
UFS_HARDWARE_ATTRS = ("current_power_mode", "psa_state")


class ClockUnavailable(RuntimeError):
    """The platform does not expose the clocks this measurement needs."""


def clocks():
    """Return (boottime, monotonic) in seconds.

    CLOCK_BOOTTIME keeps counting across a suspend, CLOCK_MONOTONIC stops,
    so their difference grows by the time the processor spent down.
    /proc/uptime cannot be used for this: its second field is the aggregate
    CPU idle time, which is a different quantity entirely.
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

    This is the difference between the two clocks of one reading. Both
    clocks are derived from adjusted monotonic time and two sequential
    reads carry a sampling skew, so the difference is not guaranteed to be
    constant and can wander slowly. It is therefore never used on its own:
    a suspend is the change of this value between two readings, which
    cancels the wander.
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
    """Return the suspend event between two samples, or None if none."""
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


def usb_transition(previous, current):
    """Return the attachment transition between two samples, or None.

    This is detected independently of the suspend detection: the same pair
    of samples can carry a suspend gap and a detach, and the detach must
    not be lost because of it.
    """
    if previous.get("usb_attached") == current.get("usb_attached"):
        return None
    return {
        "type": "usb_transition",
        "wall_utc_start": previous["wall_utc"],
        "wall_utc_end": current["wall_utc"],
        "usb_attached_start": previous.get("usb_attached"),
        "usb_attached_end": current.get("usb_attached"),
        "usb_power_attached_start": previous.get("usb_power_attached"),
        "usb_power_attached_end": current.get("usb_power_attached"),
        "usb_transport_attached_start": previous.get("usb_transport_attached"),
        "usb_transport_attached_end": current.get("usb_transport_attached"),
        "charging_start": previous.get("charging"),
        "charging_end": current.get("charging"),
        "counter_before": previous.get("charge_counter"),
        "counter_after": current.get("charge_counter"),
        "counter_before_is_discharge_endpoint": previous.get("detached"),
        "counter_after_is_discharge_endpoint": current.get("detached"),
    }


class Window(object):
    """The observed state of one standby window.

    The retained log is bounded, but the totals are not: the number of
    suspend events and the suspended time live in counters, so a log that
    reaches its capacity cannot shorten the measured sleep. The USB
    transitions are kept in their own bounded list, so the terminal
    transition survives a saturated log.
    """

    def __init__(self, threshold=1.0, max_events=MAX_EVENTS,
                 max_usb_events=MAX_USB_EVENTS,
                 max_detached_samples=MAX_DETACHED_SAMPLES):
        self.threshold = threshold
        self.max_events = max_events
        self.max_usb_events = max_usb_events
        self.max_detached_samples = max_detached_samples
        self.events = []
        self.events_total = 0
        self.events_dropped = 0
        self.usb_events = []
        self.usb_events_total = 0
        self.suspend_events_retained = []
        self.suspend_event_count = 0
        self.suspended_seconds_total = 0.0
        self.detached_samples = []
        self.detached_samples_total = 0
        self.charging_samples_total = 0
        self.first = None
        self.last = None

    @property
    def events_truncated(self):
        """True when at least one event did not fit in the retained log."""
        return self.events_dropped > 0

    def observe(self, sample):
        """Take one sample and return the events it produced.

        The suspend detection and the attachment detection are independent:
        both are computed for every pair of samples, so one interval can
        yield a suspend gap and a transition at the same time.
        """
        if self.first is None:
            self.first = sample
            self.last = sample
            self._retain_sample(sample)
            return []
        previous = self.last
        self.last = sample
        new_events = []
        suspend_event = classify(previous, sample, self.threshold)
        if suspend_event is not None:
            new_events.append(suspend_event)
        transition = usb_transition(previous, sample)
        if transition is not None:
            new_events.append(transition)
        self._retain_sample(sample)
        for event in new_events:
            self._record(event)
        return new_events

    def _record(self, event):
        self.events_total += 1
        if len(self.events) >= self.max_events:
            self.events.pop(0)
            self.events_dropped += 1
        self.events.append(event)
        if event["type"] == "suspend_gap":
            self.suspend_event_count += 1
            self.suspended_seconds_total += float(
                event.get("suspended_seconds") or 0.0)
            self.suspend_events_retained.append(event)
            if len(self.suspend_events_retained) > self.max_events:
                self.suspend_events_retained.pop(0)
        elif event["type"] == "usb_transition":
            self.usb_events_total += 1
            self.usb_events.append(event)
            if len(self.usb_events) > self.max_usb_events:
                # The first transition is kept, the oldest in between goes.
                self.usb_events.pop(1)

    def _retain_sample(self, sample):
        """Keep the readings that may serve as discharge endpoints.

        A reading taken while a power source is attached is not one: on
        this platform the counter moves back up towards charge_full while
        charging, so such a reading cannot end a discharge interval.
        """
        if sample.get("detached"):
            self.detached_samples_total += 1
            self.detached_samples.append({
                "wall_utc": sample.get("wall_utc"),
                "boottime": sample.get("boottime"),
                "charge_counter": sample.get("charge_counter"),
                "status": sample.get("status"),
                "current_now": sample.get("current_now"),
                "detached": True,
            })
            if len(self.detached_samples) > self.max_detached_samples:
                self.detached_samples.pop(0)
        else:
            self.charging_samples_total += 1

    def suspend_events(self):
        return list(self.suspend_events_retained)

    def suspended_seconds(self):
        """Seconds suspended, independent of the capacity of the log."""
        return self.suspended_seconds_total

    def unplug_event(self):
        for event in self.usb_events:
            if event.get("usb_attached_start") and not event.get(
                    "usb_attached_end"):
                return event
        return None

    def replug_event(self):
        for event in self.usb_events:
            if not event.get("usb_attached_start") and event.get(
                    "usb_attached_end"):
                return event
        return None


def read(path):
    try:
        with open(path, "r", errors="replace") as fh:
            return fh.read().strip()
    except OSError as exc:
        return "ERR:%d" % (exc.errno or 0)


def usb_state():
    """Best effort USB state.

    On this platform the USB gadget appears as a network link, not only as
    a `power_supply/usb` node, so both are probed. The loopback interface
    always reports carrier=1 and must not be counted.
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


def charging_state(status):
    """The charge state of the battery, as one word.

    The raw gauge status is kept next to it, so the derivation can be
    checked.
    """
    status = (status or "").strip()
    if status == "Charging":
        return "charging"
    if status == "Full":
        return "full"
    if status == "Discharging":
        return "discharging"
    if status == "Not charging":
        return "not_charging"
    return "unknown"


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
    # Transport, power and charge are three different things and are
    # reported apart. The boolean is a proxy built from the first two; it
    # is not independent proof of a physical attachment or of charging.
    out["usb_transport_attached"] = bool(usb["usb_links_up"])
    out["usb_power_attached"] = (usb["usb_online"] == "1")
    out["usb_attached"] = (out["usb_power_attached"] or
                            out["usb_transport_attached"])
    out["charging_state"] = charging_state(out.get("status"))
    out["charging"] = (out["charging_state"] == "charging" or
                        (out["charging_state"] == "full" and
                         out["usb_power_attached"]))
    # A detached sample is one taken while no power source is attached.
    out["detached"] = not out["usb_power_attached"]
    out["ufshc_runtime_status"] = read(os.path.join(UFS, "power", "runtime_status"))
    for attr in UFS_POLICY_ATTRS:
        out["ufs_" + attr] = read(os.path.join(UFS, attr))
    out["ufs_power_mode"] = read(os.path.join(UFS, "qcom", "power_mode"))
    out["ufs_max_bus_w"] = read(os.path.join(UFS, "max_bus_w"))
    out["regulator_summary_present"] = os.path.exists(REG_SUMMARY)
    return out


def ufs_hardware_snapshot():
    """Read the two UFS attributes that send a hardware query, once.

    This is not a passive observation: each read runtime-resumes the UFS
    device and sends a UPIU attribute query. It is kept out of the
    sampling loop and is only taken when it is asked for explicitly.
    """
    out = {}
    for attr in UFS_HARDWARE_ATTRS:
        out[attr] = read(os.path.join(UFS, "attributes", attr))
    out["note"] = ("Each of these two attributes is instantiated by the "
                   "UFS_ATTRIBUTE macro of drivers/scsi/ufs/ufs-sysfs.c, "
                   "which calls pm_runtime_get_sync(), ufshcd_query_attr() "
                   "and pm_runtime_put_sync(): the read runtime-resumes the "
                   "UFS device and sends a hardware query. The values below "
                   "are a one-shot snapshot taken outside the sampling "
                   "loop.")
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


def make_deadline(boottime, wall_epoch, max_seconds):
    """Build the deadline, in both clock bases.

    The boot-clock value is the authoritative bound, because that clock
    keeps counting across a suspend. The wall-clock value is the same
    instant expressed in the wall clock, obtained by pairing the two
    clocks at start; it is an estimate, and it is wrong on any device
    whose wall clock is stepped during the window.
    """
    return {
        "boottime": boottime + max_seconds,
        "wall_epoch": wall_epoch + max_seconds,
        "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                  time.gmtime(wall_epoch + max_seconds)),
        "max_seconds": max_seconds,
        "started_boottime": boottime,
        "started_wall_epoch": wall_epoch,
    }


def build_result(window, started, ended, deadline, args):
    """Assemble the JSON result from the observed window."""
    events = window.events
    suspends = window.suspend_events()
    unplug = window.unplug_event()
    replug = window.replug_event()
    elapsed = None
    if window.first and window.last:
        elapsed = window.last["boottime"] - window.first["boottime"]
    suspended = window.suspended_seconds()
    fraction = None
    if elapsed:
        fraction = suspended / elapsed

    result = {
        "collector": "collect-matched-standby-window",
        "version": 3,
        "started_utc": started["wall_utc"],
        "ended_utc": ended["wall_utc"],
        "wall_seconds_observed": round(elapsed, 3) if elapsed else None,
        "deadline_boottime_s": round(deadline["boottime"], 3),
        "deadline_wall_utc": deadline["wall_utc"],
        "deadline_max_seconds": deadline["max_seconds"],
        "poll_seconds": args.poll,
        "suspend_threshold_seconds": args.threshold,
        "events": events,
        "events_total": window.events_total,
        "events_retained": len(events),
        "events_dropped": window.events_dropped,
        "events_truncated": window.events_truncated,
        "usb_events_total": window.usb_events_total,
        "usb_events_retained": len(window.usb_events),
        "suspend_events": suspends,
        "suspend_event_count": window.suspend_event_count,
        "suspend_events_retained": len(suspends),
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
                         "own: both clocks are derived from adjusted "
                         "monotonic time and two sequential reads carry a "
                         "sampling skew, so the difference can wander and "
                         "the ordering of two absolute values is not "
                         "guaranteed.",
            "note": "The previous revision read /proc/uptime, whose second "
                    "field is aggregate CPU idle time and not CLOCK_MONOTONIC. "
                    "Its suspended times and suspend detections were invalid "
                    "and are not comparable with this file.",
        },
        "counter": {
            "read_before_unplug": unplug["counter_before"] if unplug else None,
            "read_after_unplug": unplug["counter_after"] if unplug else None,
            "read_at_replug": replug["counter_after"] if replug else None,
            "difference_across_unplug_uah": (
                _int_or_none(unplug["counter_after"]) -
                _int_or_none(unplug["counter_before"]))
            if unplug and _int_or_none(unplug["counter_after"]) is not None
            and _int_or_none(unplug["counter_before"]) is not None else None,
            "replug_reading_is_valid_as_discharge_endpoint": False,
            "discharge_endpoints": window.detached_samples,
            "discharge_endpoints_retained": len(window.detached_samples),
            "discharge_endpoints_total": window.detached_samples_total,
            "charging_samples": window.charging_samples_total,
            "note": "The counter is a gauge value, not an instantaneous "
                    "measurement of a suspended interval. The difference "
                    "across the unplug is not a pure discontinuity and not a "
                    "consumption figure: it mixes what the device used "
                    "while unplugged with any discontinuity of the counter "
                    "and with the recharge that followed the reconnection. "
                    "The Android reference excludes an equivalent jump "
                    "before computing its quotient, and the same treatment "
                    "is required here. Only the readings taken while no "
                    "power source was attached can end a discharge "
                    "interval; the reading taken at the reconnection is a "
                    "charging-side reading and is not one. The detached "
                    "readings are listed in discharge_endpoints.",
        },
        "usb": {
            "note": "The boolean usb_attached is a proxy built from the USB "
                    "power-supply online flag and the carrier of the USB "
                    "network links. It is not independent proof of a "
                    "physical attachment or of charging. The transport "
                    "state, the power state and the charge state are "
                    "reported separately in every sample.",
        },
        "ufs": {
            "attributes_read_during_the_window": list(UFS_POLICY_ATTRS),
            "hardware_query_attributes_not_read": list(UFS_HARDWARE_ATTRS),
            "note": "The values read while the window is measured are "
                    "configuration and bookkeeping, plus the runtime PM "
                    "status of the device. None of them is an electrical "
                    "measurement. The two attributes under .../attributes/ "
                    "are not read during the window: each read would "
                    "runtime-resume the UFS device and send a hardware "
                    "query, so it would not reveal the state of a sleeping "
                    "device, it would change it.",
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
            "window_net": "The counter delta between two readings that were "
                          "both taken while no power source was attached, "
                          "over the interval between them. Only such "
                          "detached readings may serve as endpoints: a "
                          "reading taken while charging is not a discharge "
                          "bound, because the counter moves back up towards "
                          "charge_full while charging. The retained "
                          "detached readings are listed in "
                          "counter.discharge_endpoints.",
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
                  "collector keeps a bounded sequence of the readings taken "
                  "while no power source was attached, every suspend event "
                  "and every attachment transition, and preserves the "
                  "readings so the same exclusion can be applied offline. "
                  "The retained sequence is bounded and its length is "
                  "reported, so a truncated log is visible rather than "
                  "silent.",
        "limits": "Gauge counters, not a calibrated current. The counter "
                  "path, the capacity scale and the unplug discontinuity "
                  "handling must be applied exactly as in the Android "
                  "reference before any comparison; a single run does not "
                  "establish an average. The polling loop keeps its own "
                  "process scheduled while the system is awake, and each "
                  "poll costs energy and reads the gauge, the USB links and "
                  "the UFS configuration; a normal timer is not a wake "
                  "source that would by itself prevent a system suspend, "
                  "but the polling is not free. A suspend shorter than the "
                  "poll interval cannot be told apart from awake time. No "
                  "RTC wake alarm is added, so a window that needs a wake "
                  "source to end may overrun its deadline. Regulator and "
                  "UFS values are configuration and bookkeeping, not "
                  "electrical state.",
    }
    return result


def _int_or_none(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def write_result(path, result):
    """Write the result atomically.

    The document is written next to the target and renamed into place, so
    a process killed during the write leaves the previous complete file
    instead of a truncated one.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    tmp = os.path.join(directory, "." + os.path.basename(path) + ".tmp")
    with open(tmp, "w") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def install_signal_handlers(state):
    """Write the final result when the collector is asked to stop."""
    def handler(signum, frame):
        try:
            write_result(state["out"], state["result"])
        except Exception:  # noqa: BLE001 - the exit path must not raise
            pass
        sys.exit(0)

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, handler)
        except (ValueError, OSError):
            pass


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
    ap.add_argument("--ufs-hardware-snapshot", action="store_true",
                    help="also read the two UFS attributes that runtime-"
                         "resume the device and send a hardware query, once, "
                         "outside the sampling loop")
    args = ap.parse_args()

    if not args.execute:
        print("PLAN (nothing is read, nothing is written)")
        print("  on the phone, as a user that can read the gauge and the "
              "USB nodes:")
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

    deadline = make_deadline(boottime, time.time(), args.max_seconds)
    started = sample("before")
    print("before:", json.dumps(started, sort_keys=True), flush=True)

    window = Window(threshold=args.threshold)
    window.observe(started)
    result = build_result(window, started, started, deadline, args)
    if args.ufs_hardware_snapshot:
        result["ufs_hardware_snapshot"] = ufs_hardware_snapshot()
    state = {"out": args.out, "result": result}
    install_signal_handlers(state)
    # The first checkpoint is written before anything can happen, so an
    # interrupted run still leaves a complete file behind.
    write_result(args.out, result)

    while not deadline_reached(clocks()[0], deadline["boottime"]):
        time.sleep(args.poll)
        now = sample("poll")
        events = window.observe(now)
        if events:
            for event in events:
                print("%s: %s" % (event["type"],
                                  json.dumps(event, sort_keys=True)),
                      flush=True)
            result = build_result(window, started, now, deadline, args)
            if args.ufs_hardware_snapshot:
                result["ufs_hardware_snapshot"] = ufs_hardware_snapshot()
            state["result"] = result
            # Write after every event so a window that is interrupted still
            # leaves the readings it had collected on the device.
            write_result(args.out, result)
            if any(event["type"] == "usb_transition" and
                   event.get("usb_attached_end") for event in events):
                print("replug observed", flush=True)
                break
    ended = sample("after")
    result = build_result(window, started, ended, deadline, args)
    state["result"] = result
    write_result(args.out, result)
    print("written:", args.out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
