#!/usr/bin/env python3
"""Offline tests for the matched standby window collector.

Run from the repository root:

    python3 userspace/power/diagnostics/test-collect-matched-standby-window.py

No phone is contacted. The collector module is imported and driven with
synthetic samples, so every test here is reproducible without a device.

The collector under test can be chosen with the MINIMAX_COLLECTOR
environment variable. That is how the regression tests are demonstrated:
the same suite is run against the previous revision, taken from the
repository history, and the new tests must fail there and pass here.

Two revisions are covered.

Revision 2 was born from a blocking defect: the collector read
/proc/uptime and treated its second field as CLOCK_MONOTONIC. That field
is the aggregate CPU idle time. Every suspended-time value and every
suspend detection built on it was invalid, and the defect was invisible
in the output: the file looked complete and the numbers looked plausible.

Revision 3 comes from the API review of 2026-10-22, whose results are in
work/MINIMAX-API-REVIEW-RESULTS-20261022.md. The review confirmed five
defects in revision 2, each covered by a test below that fails against
revision 2:

  * one pair of samples could not carry both a suspend gap and a USB
    transition, so a detach happening inside a suspend interval was
    lost, with the counter readings on both sides of it;
  * the event log was bounded by dropping events, so a saturated log
    could hide the terminal replug, and the suspended total was the sum
    of the surviving events, so a full log also shortened the measured
    sleep;
  * the deadline was printed as a wall-clock date but was computed from
    the boot clock, which produced a 1970-era timestamp;
  * the result was written only when an event happened and the write was
    not atomic, so an interrupted run could leave nothing behind or a
    truncated file;
  * the UFS attributes current_power_mode and psa_state were read on
    every poll, and each of those reads runtime-resumes the UFS device
    and sends a hardware query.

The review also rejected several claims that the collector used to make.
The test that checks the claims is part of the suite.
"""

import ast
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

COLLECTOR = pathlib.Path(os.environ.get(
    "MINIMAX_COLLECTOR",
    str(pathlib.Path(__file__).with_name("collect-matched-standby-window.py"))))
spec = importlib.util.spec_from_file_location("collect_matched_standby_window",
                                              COLLECTOR)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class FakeClock(object):
    """Stand-in for the time module, with a controllable clock pair."""

    def __init__(self, boottime=1000.0, monotonic=900.0):
        self.boottime = boottime
        self.monotonic = monotonic
        self.calls = []

    def clock_gettime(self, which):
        self.calls.append(which)
        real_time = sys.modules["time"]
        if which == real_time.CLOCK_BOOTTIME:
            return self.boottime
        if which == real_time.CLOCK_MONOTONIC:
            return self.monotonic
        raise AssertionError("unexpected clock %r" % (which,))


def make_sample(boottime, monotonic, counter="2676998", usb=True,
                label="poll", wall="2026-10-22T15:19:48Z", power=None,
                status=None):
    """A synthetic sample, shaped like the ones the collector builds."""
    if power is None:
        power = usb
    if status is None:
        status = "Full" if power else "Discharging"
    return {
        "label": label,
        "wall_utc": wall,
        "boottime": boottime,
        "monotonic": monotonic,
        "suspended_accumulated": boottime - monotonic,
        "charge_counter": counter,
        "status": status,
        "current_now": "0",
        "usb_attached": usb,
        "usb_power_attached": power,
        "usb_transport_attached": usb,
        "usb_links_up": ["usb0"] if usb else [],
        "usb_online": "1" if power else "0",
        "usb_power_supply": ["usb=%d" % (1 if power else 0)],
        "charging": power,
        "charging_state": "full" if power else "discharging",
        "detached": not power,
    }


def deadline_for(boottime=1000.0, wall_epoch=1792688000.0, max_seconds=1000.0):
    """Build the deadline the way the collector under test expects it.

    Revision 2 took a bare boot-clock value, revision 3 takes both clock
    bases. The helper keeps the tests that are not about the deadline
    meaningful against either revision.
    """
    if hasattr(collector, "make_deadline"):
        return collector.make_deadline(boottime, wall_epoch, max_seconds)
    return boottime + max_seconds


def args_stub():
    return type("Args", (), {"poll": 5.0, "threshold": 1.0})()


def code_strings_without_docstrings(source):
    """Every string literal of the module except the documentation ones."""
    tree = ast.parse(source)
    docstring_nodes = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            docstring_nodes.add(id(first.value))
    out = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in docstring_nodes):
            out.append(node.value)
    return out


# ---------------------------------------------------------------- revision 2


def test_clocks_use_clock_gettime_not_proc_uptime():
    """The clocks must come from clock_gettime, not from /proc/uptime."""
    fake = FakeClock(boottime=1234.5, monotonic=1000.25)
    real_time = sys.modules["time"]
    saved = real_time.clock_gettime
    try:
        real_time.clock_gettime = fake.clock_gettime
        boottime, monotonic = collector.clocks()
    finally:
        real_time.clock_gettime = saved
    assert boottime == 1234.5, boottime
    assert monotonic == 1000.25, monotonic
    assert fake.calls, "clock_gettime was never called"


def test_collector_code_does_not_read_proc_uptime():
    """The old defect was reading /proc/uptime for the clock pair.

    The documentation of the defect may name the file in prose; what the
    executable code must not contain is a path to it.
    """
    source = COLLECTOR.read_text(encoding="utf-8")
    for literal in code_strings_without_docstrings(source):
        assert not literal.startswith("/proc/uptime"), (
            "the collector reads /proc/uptime again: %r" % (literal,))
        assert "open(\"/proc/uptime" not in literal, (
            "the collector reads /proc/uptime again: %r" % (literal,))


def test_real_clock_pair_is_close_and_matches_the_posix_clocks():
    """The real clocks must be the ones the collector reports.

    CLOCK_BOOTTIME keeps counting across a suspend and CLOCK_MONOTONIC
    does not, but the two are not independent clocks: both are derived
    from adjusted monotonic time, so the difference between them is not
    guaranteed to be constant, and two sequential reads carry a sampling
    skew. The collector must therefore measure a suspend as the change
    between two readings, never as an absolute difference.
    """
    real_time = sys.modules["time"]
    boottime, monotonic = collector.clocks()
    assert abs(boottime - monotonic) < 1.0, (boottime, monotonic)
    assert abs(boottime - real_time.clock_gettime(
        real_time.CLOCK_BOOTTIME)) < 1.0
    assert abs(monotonic - real_time.clock_gettime(
        real_time.CLOCK_MONOTONIC)) < 1.0


def test_a_drift_between_the_two_readings_is_not_a_suspend():
    """A slow drift of the difference between the readings is not a sleep.

    Both clocks derive from adjusted monotonic time, so the difference
    between them can wander slowly. Over a whole window that wander
    reaches seconds, but the collector compares two readings that are one
    poll interval apart, so the drift it has to reject is the drift of a
    single interval. A detector that compares two readings is immune; one
    that trusts an absolute difference is not.
    """
    window = collector.Window()
    poll = 5.0
    drift = 500e-6
    for step in range(720):
        elapsed = poll * step
        window.observe(make_sample(elapsed, elapsed * (1.0 - drift)))
    assert window.suspend_events() == [], window.events[:3]
    assert window.suspended_seconds() == 0.0


def test_the_aggregate_idle_field_is_not_a_monotonic_clock():
    """Pin the defect itself: /proc/uptime field 2 is aggregate idle time.

    On this host the value is larger than the uptime field, which is
    impossible for a monotonic clock, and it grows with the idle time of
    every CPU. Treating it as CLOCK_MONOTONIC is what invalidated the
    previous revision.
    """
    fields = pathlib.Path("/proc/uptime").read_text().split()
    uptime, idle = float(fields[0]), float(fields[1])
    assert idle > uptime, (uptime, idle)
    assert (uptime - idle) < 0.0, (uptime, idle)


def test_missing_clock_is_refused():
    """Without CLOCK_BOOTTIME the collector must refuse, not guess."""
    real_time = sys.modules["time"]
    saved_boottime = real_time.CLOCK_BOOTTIME
    try:
        del real_time.CLOCK_BOOTTIME
        try:
            collector.clocks()
        except collector.ClockUnavailable:
            pass
        else:
            raise AssertionError("a missing clock was not refused")
    finally:
        real_time.CLOCK_BOOTTIME = saved_boottime


def test_awake_passage_is_not_a_suspend():
    """Time passing while the processor stays up is not a suspend."""
    first = make_sample(1000.0, 900.0)
    second = make_sample(1005.0, 905.0)
    assert collector.suspend_gap(first, second, 1.0) == 0.0
    window = collector.Window()
    window.observe(first)
    assert window.observe(second) == []
    assert window.suspend_events() == []
    assert window.suspended_seconds() == 0.0


def test_real_suspend_gap_is_detected_and_measured():
    """A suspend is a growth of the boottime-minus-monotonic total.

    600 s of suspend followed by 5 s of awake time: the boot clock advanced
    by 605 s, the monotonic clock by 5 s.
    """
    first = make_sample(1000.0, 900.0)
    second = make_sample(1605.0, 905.0)
    gap = collector.suspend_gap(first, second, 1.0)
    assert abs(gap - 600.0) < 1e-6, gap
    event = collector.classify(first, second, 1.0)
    assert event is not None
    assert event["type"] == "suspend_gap"
    assert abs(event["suspended_seconds"] - 600.0) < 1e-6, event
    assert abs(event["awake_seconds_between_reads"] - 5.0) < 1e-6, event


def test_resume_after_a_suspend_is_reported_once():
    """The pair of readings around a suspend yields one event, not two."""
    window = collector.Window()
    window.observe(make_sample(1000.0, 900.0))
    window.observe(make_sample(1605.0, 905.0))
    window.observe(make_sample(1610.0, 910.0))
    assert len(window.suspend_events()) == 1, window.events
    assert abs(window.suspended_seconds() - 600.0) < 1e-6


def test_several_suspends_are_kept_as_a_sequence():
    """The previous revision kept only the first suspend."""
    window = collector.Window()
    window.observe(make_sample(1000.0, 900.0))
    window.observe(make_sample(1605.0, 905.0))
    window.observe(make_sample(1610.0, 910.0))
    window.observe(make_sample(2215.0, 915.0))
    window.observe(make_sample(2220.0, 920.0))
    events = window.suspend_events()
    assert len(events) == 2, events
    assert abs(window.suspended_seconds() - 1200.0) < 1e-6
    assert abs(events[0]["suspended_seconds"] - 600.0) < 1e-6, events[0]
    assert abs(events[1]["suspended_seconds"] - 600.0) < 1e-6, events[1]


def test_usb_transition_is_recorded_as_an_event():
    """The unplug and the replug must be visible with both readings."""
    window = collector.Window()
    window.observe(make_sample(1000.0, 900.0, counter="2676998", usb=True))
    window.observe(make_sample(1005.0, 905.0, counter="2676998", usb=False))
    window.observe(make_sample(1010.0, 910.0, counter="2676900", usb=False))
    window.observe(make_sample(1015.0, 915.0, counter="2676800", usb=True))
    usb_events = [e for e in window.events if e["type"] == "usb_transition"]
    assert len(usb_events) == 2, window.events
    assert usb_events[0]["usb_attached_start"] is True
    assert usb_events[0]["usb_attached_end"] is False
    assert usb_events[1]["usb_attached_start"] is False
    assert usb_events[1]["usb_attached_end"] is True


def test_event_sequence_is_bounded():
    """The event list must not grow without limit."""
    window = collector.Window(max_events=3)
    window.observe(make_sample(1000.0, 900.0))
    for index in range(10):
        window.observe(make_sample(1605.0 + 605 * index, 905.0 + index))
    assert window.events_truncated is True
    assert len(window.events) <= 3, window.events
    assert window.events_total == 10, window.events_total


def test_deadline_uses_the_wall_clock():
    """The deadline must be reached on the boot clock, not the monotonic one."""
    assert collector.deadline_reached(1000.0, 1000.0) is True
    assert collector.deadline_reached(999.9, 1000.0) is False
    # A suspend advances the boot clock and not the monotonic clock, so a
    # deadline taken on the boot clock is reached even though the collector
    # was not running.
    assert collector.deadline_reached(1600.0, 1500.0) is True


def test_poll_and_max_seconds_reject_bad_values():
    """Non-positive and non-finite sampling arguments are refused."""
    for bad in ("0", "-1", "nan", "inf", "-inf"):
        try:
            collector.positive_finite(bad)
        except Exception as exc:
            assert "strictly positive" in str(exc) or "finite" in str(exc), exc
        else:
            raise AssertionError("%r was accepted" % (bad,))
    assert collector.positive_finite("2.5") == 2.5


def test_collector_refuses_to_run_without_the_clocks():
    """The command line entry point must fail closed."""
    real_time = sys.modules["time"]
    saved = real_time.CLOCK_BOOTTIME
    try:
        del real_time.CLOCK_BOOTTIME
        saved_argv = sys.argv
        sys.argv = ["collect-matched-standby-window.py", "--execute"]
        try:
            code = collector.main()
        finally:
            sys.argv = saved_argv
    finally:
        real_time.CLOCK_BOOTTIME = saved
    assert code == 2, code


def test_result_reports_the_suspended_fraction():
    """The window must state how much of it was actually suspended."""
    window = collector.Window()
    started = make_sample(1000.0, 900.0)
    window.observe(started)
    window.observe(make_sample(1600.0, 900.0))
    window.observe(make_sample(1700.0, 1000.0))
    result = collector.build_result(
        window, started, started, deadline_for(), args_stub())
    assert result["suspend_event_count"] == 1, result["suspend_event_count"]
    assert abs(result["suspended_seconds_total"] - 600.0) < 1e-6
    assert result["suspended_fraction_of_window"] is not None
    assert 0.0 < result["suspended_fraction_of_window"] < 1.0


def test_result_never_claims_a_calibrated_current():
    """The result must not present a counter quotient as a current."""
    window = collector.Window()
    started = make_sample(1000.0, 900.0)
    window.observe(started)
    window.observe(make_sample(1600.0, 900.0))
    result = collector.build_result(
        window, started, started, deadline_for(), args_stub())
    text = result["estimators"]["sleep_window_net"].lower()
    assert "not a calibrated" in text or "not" in text
    assert "calibrated sleep current" in text


# ---------------------------------------------------------------- revision 3


def test_one_sample_pair_can_carry_both_a_suspend_gap_and_a_usb_transition():
    """A detach that happens inside a suspend interval must not be lost.

    Revision 2 let the suspend take the interval and skipped the
    transition, so the unplug disappeared together with the counter
    readings on both sides of it, and the collector could not stop on the
    replug either.
    """
    window = collector.Window()
    window.observe(make_sample(1000.0, 900.0, counter="2676998", usb=True))
    window.observe(make_sample(1605.0, 905.0, counter="2676900", usb=False))
    kinds = sorted(event["type"] for event in window.events)
    assert kinds == ["suspend_gap", "usb_transition"], window.events
    unplug = [e for e in window.events if e["type"] == "usb_transition"][0]
    assert unplug["counter_before"] == "2676998", unplug
    assert unplug["counter_after"] == "2676900", unplug


def test_a_saturated_event_log_does_not_hide_the_replug():
    """A long window must keep its terminal transition.

    Revision 2 dropped events once the log was full, so the replug could
    be dropped, and the collector would then never stop and never write
    the terminal result.
    """
    window = collector.Window(max_events=3)
    window.observe(make_sample(1000.0, 900.0, usb=True))
    for index in range(10):
        window.observe(make_sample(1605.0 + 605 * index, 905.0 + index,
                                   usb=True))
    window.observe(make_sample(3000.0, 1500.0, usb=False))
    window.observe(make_sample(3005.0, 1505.0, counter="2676900", usb=True))
    replug = window.replug_event()
    assert replug is not None, window.events
    assert replug["counter_after"] == "2676900", replug
    assert window.events_truncated is True


def test_the_suspended_total_is_not_limited_by_the_log_capacity():
    """A full log must not shorten the measured suspended time.

    Revision 2 summed the events that survived in the log, so a saturated
    log silently under-reported the sleep.
    """
    window = collector.Window(max_events=3)
    window.observe(make_sample(1000.0, 900.0))
    for index in range(10):
        # Each step advances the boot clock by 605 s and the monotonic clock
        # by 5 s, so every gap is exactly 600 s of suspended time.
        window.observe(make_sample(1000.0 + 605 * (index + 1),
                                   900.0 + 5 * (index + 1)))
    assert window.suspend_event_count == 10, window.suspend_event_count
    assert abs(window.suspended_seconds() - 6000.0) < 1e-6, \
        window.suspended_seconds()


def test_the_readings_on_both_sides_of_the_unplug_are_preserved():
    """The counter readings around the unplug must survive the fix.

    The name of the field changed on purpose: revision 2 called it a
    jump, which presented a difference as a pure discontinuity.
    """
    window = collector.Window()
    started = make_sample(1000.0, 900.0, counter="2676998", usb=True)
    window.observe(started)
    window.observe(make_sample(1005.0, 905.0, counter="2508679", usb=False))
    window.observe(make_sample(1010.0, 910.0, counter="2508600", usb=False))
    window.observe(make_sample(1015.0, 915.0, counter="2508500", usb=True))
    result = collector.build_result(
        window, started, started, deadline_for(), args_stub())
    counter = result["counter"]
    assert counter["read_before_unplug"] == "2676998", counter
    assert counter["read_after_unplug"] == "2508679", counter
    assert "jump_across_unplug_uah" not in counter, counter
    assert counter["difference_across_unplug_uah"] == 2508679 - 2676998, counter
    note = counter["note"].lower()
    assert "not a pure discontinuity" in note, counter["note"]
    assert "not a consumption figure" in note, counter["note"]


def test_a_reading_taken_while_charging_is_not_a_discharge_endpoint():
    """The replug-side reading cannot end a discharge interval.

    On this platform the counter moves back up towards charge_full while
    charging, so a reading taken after the reconnection is a
    charging-side reading and must be labelled as such.
    """
    window = collector.Window()
    started = make_sample(1000.0, 900.0, counter="2676998", usb=True)
    window.observe(started)
    window.observe(make_sample(1005.0, 905.0, counter="2676900", usb=False))
    window.observe(make_sample(1010.0, 910.0, counter="2676800", usb=False))
    window.observe(make_sample(1015.0, 915.0, counter="2676990", usb=True))
    result = collector.build_result(
        window, started, started, deadline_for(), args_stub())
    counter = result["counter"]
    assert counter["read_at_replug"] == "2676990", counter
    assert counter["replug_reading_is_valid_as_discharge_endpoint"] is False, \
        counter
    endpoints = counter["discharge_endpoints"]
    assert endpoints, counter
    assert all(point["detached"] for point in endpoints), endpoints
    assert not any(point["charge_counter"] == "2676990"
                   for point in endpoints), endpoints


def test_the_deadline_is_labelled_with_a_valid_wall_clock_and_the_boot_clock():
    """The deadline must not be a boot-clock value printed as a date.

    Revision 2 called gmtime() on a boot-clock value, which produced a
    date in 1970.
    """
    deadline = collector.make_deadline(1000.0, 1792688000.0, 600.0)
    window = collector.Window()
    started = make_sample(1000.0, 900.0)
    window.observe(started)
    result = collector.build_result(
        window, started, started, deadline, args_stub())
    label = result["deadline_wall_utc"]
    assert label.startswith("2026-"), label
    assert "1970" not in label, label
    assert abs(result["deadline_boottime_s"] - 1600.0) < 1e-6, result
    assert "deadline_utc" not in result, sorted(result)


def test_the_result_is_persisted_before_the_first_event():
    """An interrupted run must leave a complete file behind.

    Revision 2 wrote the result only when an event happened, so a run
    that was stopped before the first event left nothing at all.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "window.json")
        proc = subprocess.Popen(
            [sys.executable, str(COLLECTOR), "--execute", "--out", out,
             "--poll", "0.2", "--max-seconds", "60"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            limit = time.time() + 20.0
            appeared = None
            while time.time() < limit:
                if os.path.exists(out):
                    appeared = time.time()
                    break
                time.sleep(0.2)
            assert appeared is not None, "no result file before the first event"
            with open(out) as fh:
                first = json.load(fh)
            assert first.get("version") == 3, first.get("version")
            assert first.get("before"), first
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=15)
        with open(out) as fh:
            final = json.load(fh)
        assert final.get("version") == 3, final.get("version")


def test_a_write_interrupted_by_an_error_leaves_the_previous_file_intact():
    """The result file is replaced atomically, never truncated in place.

    Revision 2 opened the target and wrote into it, so a process killed
    during the write left a partial file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "window.json")
        collector.write_result(out, {"version": 3, "marker": "first"})
        with open(out) as fh:
            good = fh.read()
        real_dump = json.dump

        def broken(*args, **kwargs):
            raise RuntimeError("simulated failure during the write")

        json.dump = broken
        try:
            collector.write_result(out, {"version": 3, "marker": "second"})
        except RuntimeError:
            pass
        finally:
            json.dump = real_dump
        with open(out) as fh:
            assert fh.read() == good, "the previous result was damaged"
        assert json.loads(good)["marker"] == "first"


def test_the_periodic_sample_does_not_query_the_ufs_hardware_attributes():
    """Reading current_power_mode or psa_state is a hardware query.

    In drivers/scsi/ufs/ufs-sysfs.c the UFS_ATTRIBUTE macro calls
    pm_runtime_get_sync(), ufshcd_query_attr() and pm_runtime_put_sync(),
    and current_power_mode and psa_state instantiate that macro. Each
    read therefore runtime-resumes the UFS device and sends a query, so
    it is not a passive observation of a sleeping device and it must not
    happen on every poll of a standby window.
    """
    paths = []
    real_read = collector.read

    def recording_read(path):
        paths.append(path)
        return real_read(path)

    collector.read = recording_read
    try:
        sample = collector.sample("poll")
    finally:
        collector.read = real_read
    for path in paths:
        assert "/attributes/" not in path, path
        assert "current_power_mode" not in path, path
        assert "psa_state" not in path, path
    for attr in collector.UFS_HARDWARE_ATTRS:
        assert ("ufs_" + attr) not in sample, sorted(sample)
    snapshot = collector.ufs_hardware_snapshot()
    assert "hardware query" in snapshot["note"], snapshot


def test_transport_power_and_charge_are_reported_separately():
    """The USB boolean is a proxy, not proof of attachment or charging.

    A data link can be up while no power source is attached, and a power
    source can be attached while the data link is down. The three states
    are reported apart, and only a sample taken with no power source
    attached may serve as a discharge endpoint.
    """
    real_usb_state = collector.usb_state
    try:
        collector.usb_state = lambda: {
            "usb_power_supply": ["usb=1"], "usb_online": "1",
            "usb_links_up": []}
        sample = collector.sample("poll")
        assert sample["usb_power_attached"] is True, sample
        assert sample["usb_transport_attached"] is False, sample
        assert sample["usb_attached"] is True, sample
        assert sample["detached"] is False, sample

        collector.usb_state = lambda: {
            "usb_power_supply": ["usb=0"], "usb_online": "0",
            "usb_links_up": ["usb0"]}
        sample = collector.sample("poll")
        assert sample["usb_power_attached"] is False, sample
        assert sample["usb_transport_attached"] is True, sample
        assert sample["usb_attached"] is True, sample
        assert sample["detached"] is True, sample
    finally:
        collector.usb_state = real_usb_state


def test_the_output_does_not_repeat_the_rejected_claims():
    """The result must not state what the review rejected.

    The review rejected three claims of the previous revision: that the
    collector records every sample, that a poll wakes the processor, and
    that one of the two clocks is slewed while the other is not.
    """
    window = collector.Window()
    started = make_sample(1000.0, 900.0)
    window.observe(started)
    window.observe(make_sample(1605.0, 905.0, usb=False))
    result = collector.build_result(
        window, started, started, deadline_for(), args_stub())
    text = json.dumps(result).lower()
    forbidden = [
        "records every sample",
        "wakes the processor every",
        "the monotonic clock is slewed by the timekeeping layer and the "
        "boot clock is not",
    ]
    for phrase in forbidden:
        assert phrase not in text, phrase
    source = COLLECTOR.read_text(encoding="utf-8").lower()
    for phrase in forbidden:
        assert phrase not in source, phrase


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as exc:  # noqa: BLE001 - the runner reports them
            failures.append((t.__name__, exc))
            print("FAIL %s: %s: %s" % (t.__name__, type(exc).__name__, exc))
        else:
            print("PASS %s" % t.__name__)
    print("%d tests, %d failures" % (len(tests), len(failures)))
    if failures:
        print("failing: %s" % ", ".join(name for name, _ in failures))
        return 1
    print("%d tests passed" % len(tests))
    return 0


if __name__ == "__main__":
    sys.exit(main())
