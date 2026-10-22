#!/usr/bin/env python3
"""Offline tests for the matched standby window collector.

Run from the repository root:

    python3 userspace/power/diagnostics/test-collect-matched-standby-window.py

No phone is contacted. The collector module is imported and driven with
synthetic samples, so every test here is reproducible without a device.

These tests exist because the previous collector revision read /proc/uptime
and treated its second field as CLOCK_MONOTONIC. That field is the aggregate
CPU idle time. Every suspended-time value and every suspend detection built
on it was invalid, and the defect was invisible in the output: the file
looked complete and the numbers looked plausible. The tests below pin the
clock source, the detection of a real suspend gap and the refusal to collect
when the clocks are missing.
"""

import ast
import importlib.util
import pathlib
import sys

COLLECTOR = pathlib.Path(__file__).with_name("collect-matched-standby-window.py")
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
                label="poll", wall="2026-10-22T15:19:48Z"):
    return {
        "label": label,
        "wall_utc": wall,
        "boottime": boottime,
        "monotonic": monotonic,
        "suspended_accumulated": boottime - monotonic,
        "charge_counter": counter,
        "usb_attached": usb,
    }


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

    On Linux CLOCK_BOOTTIME keeps counting across a suspend and
    CLOCK_MONOTONIC does not, but the two are not the same clock: the
    monotonic clock is slewed by the timekeeping layer and the boot clock
    is not, so they drift apart slowly and the ordering is not guaranteed.
    The collector must therefore measure a suspend as the change between
    two readings, never as an absolute difference.
    """
    real_time = sys.modules["time"]
    boottime, monotonic = collector.clocks()
    assert abs(boottime - monotonic) < 1.0, (boottime, monotonic)
    assert abs(boottime - real_time.clock_gettime(
        real_time.CLOCK_BOOTTIME)) < 1.0
    assert abs(monotonic - real_time.clock_gettime(
        real_time.CLOCK_MONOTONIC)) < 1.0


def test_clock_slew_does_not_create_a_false_suspend():
    """A slewed monotonic clock must not be read as a suspend.

    The monotonic clock is corrected by the timekeeping layer and the boot
    clock is not, so the two drift apart at up to a few hundred parts per
    million. Over a whole window that drift reaches seconds, but the
    collector compares two readings that are one poll interval apart, so
    the drift it has to reject is the drift of a single interval: 2.5 ms
    at the extreme rate over a 5 s poll. A detector that compares two
    readings is immune; one that trusts an absolute difference is not.
    """
    window = collector.Window()
    poll = 5.0
    slew = 500e-6
    for step in range(720):
        elapsed = poll * step
        window.observe(make_sample(elapsed, elapsed * (1.0 - slew)))
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
    assert window.observe(second) is None
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


def test_counter_jump_across_the_unplug_is_preserved():
    """The discontinuity at the unplug must be reported, not smoothed."""
    window = collector.Window()
    started = make_sample(1000.0, 900.0, counter="2676998", usb=True)
    window.observe(started)
    window.observe(make_sample(1005.0, 905.0, counter="2508679", usb=False))
    window.observe(make_sample(1010.0, 910.0, counter="2508600", usb=False))
    window.observe(make_sample(1015.0, 915.0, counter="2508500", usb=True))
    result = collector.build_result(
        window, started, started, 2000.0,
        type("Args", (), {"poll": 5.0, "threshold": 1.0})())
    jump = result["counter"]["jump_across_unplug_uah"]
    assert jump is not None, result["counter"]
    assert jump == 2508679 - 2676998, jump
    assert result["counter"]["read_before_unplug"] == "2676998"
    assert result["counter"]["read_after_unplug"] == "2508679"


def test_result_reports_the_suspended_fraction():
    """The window must state how much of it was actually suspended."""
    window = collector.Window()
    started = make_sample(1000.0, 900.0)
    window.observe(started)
    window.observe(make_sample(1600.0, 900.0))
    window.observe(make_sample(1700.0, 1000.0))
    result = collector.build_result(
        window, started, started, 3000.0,
        type("Args", (), {"poll": 5.0, "threshold": 1.0})())
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
        window, started, started, 3000.0,
        type("Args", (), {"poll": 5.0, "threshold": 1.0})())
    text = result["estimators"]["sleep_window_net"].lower()
    assert "not a calibrated" in text or "not" in text
    assert "calibrated sleep current" in text


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS %s" % t.__name__)
    print("%d tests passed" % len(tests))
    return 0


if __name__ == "__main__":
    sys.exit(main())
