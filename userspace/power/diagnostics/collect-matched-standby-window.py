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

Revision 4, after the independent revision 3 review of 2026-10-22. That
review confirmed the fixes of revision 3 and found two defects in it, both
fixed here:

  * The discharge endpoint was qualified by the absence of a USB power
    source, computed as "the online flag does not read 1". A missing node,
    a denied read or an error therefore read as an offline source, and a
    sample taken while the battery was charging could be kept as a
    discharge endpoint. The endpoint is now qualified explicitly: the USB
    online flag must be validated offline, every other power source must
    be known and not online, and the gauge must report Discharging. Any
    unknown or failed reading disqualifies the sample, and the reason is
    kept with the evidence. An offline USB node is not independent proof
    of a physically unplugged phone, and the result says so.
  * The optional UFS hardware snapshot was read again after every event,
    which reintroduced the runtime-resuming hardware queries the option
    is meant to isolate. It is now read once and reused.

A third, smaller defect: the UFS attribute was read under the name
max_bus_w, while the attribute the driver creates is max_bus_bw. The
correct name is used now.

Revision 3 had already fixed, and this revision keeps:

  * one pair of samples can carry a suspend gap and a USB transition at
    the same time;
  * the retained log stays bounded while the totals live in counters and
    the USB transitions have their own bounded list;
  * the deadline carries an explicit boot-clock value and a wall-clock
    value;
  * the result is written before the first event, every write is atomic,
    and a termination signal writes the final result;
  * the two UFS attributes that runtime-resume the device and send a
    hardware query are not read while the window is measured.

The claims the API review of 2026-10-22 rejected are corrected as well:
both clocks derive from adjusted monotonic time, a normal timer is not a
suspend wake source, the USB boolean is a proxy, the difference across
the unplug is not a pure discontinuity and not a consumption figure, and
the result does not claim to keep every sample.

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
POWER_SUPPLY = "/sys/class/power_supply"
UFS = "/sys/bus/platform/devices/1d84000.ufshc"
REG_SUMMARY = "/sys/kernel/debug/regulator/regulator_summary"

MAX_EVENTS = 512
MAX_USB_EVENTS = 64
MAX_ENDPOINT_SAMPLES = 256

ONLINE_PRESENT = "1"
ONLINE_ABSENT = "0"

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
        "counter_before_is_discharge_endpoint": previous.get(
            "discharge_endpoint"),
        "counter_after_is_discharge_endpoint": current.get(
            "discharge_endpoint"),
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
                 max_endpoint_samples=MAX_ENDPOINT_SAMPLES):
        self.threshold = threshold
        self.max_events = max_events
        self.max_usb_events = max_usb_events
        self.max_endpoint_samples = max_endpoint_samples
        self.events = []
        self.events_total = 0
        self.events_dropped = 0
        self.usb_events = []
        self.usb_events_total = 0
        self.suspend_events_retained = []
        self.suspend_event_count = 0
        self.suspended_seconds_total = 0.0
        self.endpoint_samples = []
        self.endpoint_samples_total = 0
        self.rejected_endpoint_reasons = {}
        self.samples_total = 0
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
            self.samples_total += 1
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
        self.samples_total += 1
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

        Only a sample that qualifies as a discharge endpoint is kept. A
        reading taken while a power source is attached, while the gauge
        reports Charging or Full, or while any of the readings needed to
        qualify it is unknown, is counted with the reason it was rejected
        and is not offered as an endpoint.
        """
        if sample.get("discharge_endpoint"):
            self.endpoint_samples_total += 1
            self.endpoint_samples.append({
                "wall_utc": sample.get("wall_utc"),
                "boottime": sample.get("boottime"),
                "charge_counter": sample.get("charge_counter"),
                "status": sample.get("status"),
                "current_now": sample.get("current_now"),
                "usb_online_raw": sample.get("usb_online_raw"),
                "discharge_endpoint": True,
            })
            if len(self.endpoint_samples) > self.max_endpoint_samples:
                self.endpoint_samples.pop(0)
        else:
            reason = sample.get("discharge_endpoint_reason") or "unknown"
            self.rejected_endpoint_reasons[reason] = \
                self.rejected_endpoint_reasons.get(reason, 0) + 1

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


def supply_online_paths():
    """The online flag of every power supply that exposes one."""
    paths = []
    try:
        names = sorted(os.listdir(POWER_SUPPLY))
    except OSError:
        return paths
    for name in names:
        path = os.path.join(POWER_SUPPLY, name, "online")
        if os.path.exists(path):
            paths.append(path)
    return paths


def parse_online(raw):
    """Tri-state reading of a power supply online flag.

    "1" means the source is present and "0" means it is not. Anything
    else is unknown: the node was missing, the read was denied, the read
    failed, or the value is not a number. An unknown reading is never
    read as an absent source.
    """
    if raw == ONLINE_PRESENT:
        return True
    if raw == ONLINE_ABSENT:
        return False
    return None


def usb_links():
    """The USB network links that report a carrier.

    The loopback interface always reports carrier=1 and must not be
    counted.
    """
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
    return links


def usb_state():
    """Best effort USB state.

    On this platform the USB gadget appears as a network link, not only as
    a `power_supply/usb` node, so both are probed. The raw online
    values are kept as they were read, including the reads that failed,
    because the qualification of a discharge endpoint depends on them.
    """
    online_raw = {}
    for path in supply_online_paths():
        online_raw[os.path.basename(os.path.dirname(path))] = read(path)
    return {"online_raw": online_raw,
            "usb_online_raw": online_raw.get("usb"),
            "usb_links_up": usb_links()}


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


def discharge_endpoint(sample):
    """Whether this sample may end a discharge interval, and why not.

    A discharge endpoint needs three independent things, because this
    measurement is made over a USB cable:

      * the USB power path must be validated offline, that is its raw
        online flag must read exactly "0". A missing node, a denied read
        or an error is unknown, and an unknown is not an absent source;
      * every other power source must be known, and none of them may be
        online, so the phone is not charged from anywhere else;
      * the gauge must report Discharging, because a Charging or Full
        reading means the counter can move back up towards charge_full and
        such a reading cannot end a discharge interval.

    Any unknown or failed reading disqualifies the sample. The evidence
    is kept either way, with the reason.
    """
    raw = sample.get("online_raw") or {}
    usb_raw = raw.get("usb")
    if usb_raw is None:
        return False, "usb_online_missing"
    usb_state_value = parse_online(usb_raw)
    if usb_state_value is None:
        return False, "usb_online_unknown"
    if usb_state_value is True:
        return False, "usb_online_present"
    for name, value in sorted(raw.items()):
        if name == "usb":
            continue
        other = parse_online(value)
        if other is None:
            return False, "other_source_unknown:%s" % name
        if other is True:
            return False, "other_source_online:%s" % name
    status = (sample.get("status") or "").strip()
    if status != "Discharging":
        return False, "battery_status:%s" % (status or "unknown")
    return True, "usb_validated_offline_and_discharging"


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
    out["online_raw"] = usb["online_raw"]
    out["usb_online_raw"] = usb["usb_online_raw"]
    out["usb_links_up"] = usb["usb_links_up"]
    # Transport, power and charge are three different things and are
    # reported apart. The boolean is a proxy built from the first two; it
    # is not independent proof of a physical attachment or of charging.
    out["usb_transport_attached"] = bool(usb["usb_links_up"])
    out["usb_power_attached"] = parse_online(usb["usb_online_raw"])
    out["usb_attached"] = (out["usb_power_attached"] is True or
                            out["usb_transport_attached"])
    out["charging_state"] = charging_state(out.get("status"))
    out["charging"] = (out["charging_state"] == "charging" or
                        (out["charging_state"] == "full" and
                         out["usb_power_attached"] is True))
    endpoint, reason = discharge_endpoint(out)
    out["discharge_endpoint"] = endpoint
    out["discharge_endpoint_reason"] = reason
    out["ufshc_runtime_status"] = read(os.path.join(UFS, "power", "runtime_status"))
    for attr in UFS_POLICY_ATTRS:
        out["ufs_" + attr] = read(os.path.join(UFS, attr))
    out["ufs_power_mode"] = read(os.path.join(UFS, "qcom", "power_mode"))
    out["ufs_max_bus_bw"] = read(os.path.join(UFS, "max_bus_bw"))
    out["regulator_summary_present"] = os.path.exists(REG_SUMMARY)
    return out


def ufs_hardware_snapshot():
    """Read the two UFS attributes that send a hardware query, once.

    This is not a passive observation: each read runtime-resumes the UFS
    device and sends a UPIU attribute query. It is kept out of the
    sampling loop, it is taken at most once per run, and it says what it
    is.
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
        "version": 4,
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
            "discharge_endpoints": window.endpoint_samples,
            "discharge_endpoints_retained": len(window.endpoint_samples),
            "discharge_endpoints_total": window.endpoint_samples_total,
            "samples_total": window.samples_total,
            "rejected_endpoint_reasons": dict(window.rejected_endpoint_reasons),
            "note": "The counter is a gauge value, not an instantaneous "
                    "measurement of a suspended interval. The difference "
                    "across the unplug is not a pure discontinuity and not a "
                    "consumption figure: it mixes what the device used "
                    "while unplugged with any discontinuity of the counter "
                    "and with the recharge that followed the reconnection. "
                    "The Android reference excludes an equivalent jump "
                    "before computing its quotient, and the same treatment "
                    "is required here. Only a reading that qualifies as a "
                    "discharge endpoint may end a discharge interval: the "
                    "USB power path must be validated offline, every other "
                    "power source must be known and not online, and the "
                    "gauge must report Discharging. A reading taken while "
                    "charging, or while any of those readings is unknown, "
                    "is kept as evidence with its reason and is not an "
                    "endpoint. The retained endpoints are listed in "
                    "discharge_endpoints.",
        },
        "usb": {
            "note": "The boolean usb_attached is a proxy built from the USB "
                    "power-supply online flag and the carrier of the USB "
                    "network links. It is not independent proof of a "
                    "physical attachment or of charging. The transport "
                    "state, the power state and the charge state are "
                    "reported separately in every sample, and the raw "
                    "online readings are kept as they were read, including "
                    "the ones that failed.",
        },
        "ufs": {
            "attributes_read_during_the_window": list(UFS_POLICY_ATTRS),
            "hardware_query_attributes_not_read": list(UFS_HARDWARE_ATTRS),
            "note": "The values read while the window is measured are "
                    "configuration and bookkeeping, plus the runtime PM "
                    "status of the device. None of them is an electrical "
                    "measurement. The two attributes under .../attributes/ "
                    "are not read while the window is measured: each read "
                    "would runtime-resume the UFS device and send a "
                    "hardware query, so it would not reveal the state of a "
                    "sleeping device, it would change it. The optional "
                    "snapshot is taken at most once per run.",
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
                          "both qualified as discharge endpoints, over the "
                          "interval between them. A reading taken while "
                          "charging, or while any of the readings needed to "
                          "qualify it is unknown, cannot end a discharge "
                          "interval: the counter moves back up towards "
                          "charge_full while charging. The retained "
                          "endpoints are listed in "
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
                  "collector keeps a bounded sequence of the readings that "
                  "qualify as discharge endpoints, every suspend event and "
                  "every attachment transition, and preserves the readings "
                  "so the same exclusion can be applied offline. The "
                  "retained sequence is bounded and its length is reported, "
                  "so a truncated log is visible rather than silent.",
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
                  "electrical state. An offline USB node is not independent "
                  "proof of a physically unplugged phone.",
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
        # Read at most once per run. Reading it again after every event
        # would reintroduce the runtime-resuming hardware queries this
        # option exists to isolate.
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
                result["ufs_hardware_snapshot"] = \
                    state["result"].get("ufs_hardware_snapshot")
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
    if args.ufs_hardware_snapshot:
        result["ufs_hardware_snapshot"] = \
            state["result"].get("ufs_hardware_snapshot")
    state["result"] = result
    write_result(args.out, result)
    print("written:", args.out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
