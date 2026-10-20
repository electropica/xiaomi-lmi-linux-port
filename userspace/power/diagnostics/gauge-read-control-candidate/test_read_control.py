"""Deterministic tests for read_control.py; all device reads are fakes."""
import unittest

from read_control import (MAX_PLAN_READS, MODE_SEQUENCE, ReadControl)


class FakeClock:
    def __init__(self):
        self.boot = 100.0
        self.mono = 20.0
        self.wall = 1000.0
        self.jump_before_next_stamp = False

    def advance(self, seconds):
        self.boot += seconds
        self.mono += seconds
        self.wall += seconds

    def epoch(self):
        return self.wall

    def boottime(self):
        return self.boot

    def monotonic(self):
        value = self.mono
        if self.jump_before_next_stamp:
            self.jump_before_next_stamp = False
            self.advance(0.4)
        return value


class FakeBackend:
    def __init__(self, clock, time_only=False, access_effect=False):
        self.clock = clock
        self.time_only = time_only
        self.access_effect = access_effect
        self.calls = []
        self.writes = []
        self.callback_start = clock.mono
        self.offset_ua = 0
        self.usb_values = ["0"]
        self.slow_attribute = None
        self.error_attribute = None

    def begin_callback(self):
        self.callback_start = self.clock.mono
        self.offset_ua = 0

    def read(self, attribute):
        self.calls.append(attribute)
        if attribute == self.error_attribute:
            raise OSError("synthetic read error")
        if attribute == "usb/online":
            index = sum(x == attribute for x in self.calls) - 1
            value = self.usb_values[min(index, len(self.usb_values) - 1)]
        elif attribute == "battery/status":
            value = "Discharging"
        elif attribute == "wakeup_reasons/last_resume_reason":
            value = "438 msoc-delta"
        elif attribute == "bms/current_now":
            value = "49316"
        elif attribute == "bms/current_avg":
            elapsed = self.clock.mono - self.callback_start
            value = str(49000 + int(elapsed * 1000) + self.offset_ua)
        elif attribute in ("bms/charge_counter", "bms/charge_counter_shadow", "bms/charge_now_raw"):
            value = "1000000"
            if self.access_effect and attribute == "bms/charge_now_raw":
                self.offset_ua += 1000
        else:
            raise AssertionError("Unexpected read attribute: " + attribute)
        self.clock.advance(0.01 if attribute != self.slow_attribute else 0.4)
        if attribute == "bms/current_now" and self.clock.jump_before_next_stamp:
            # monotonic() after this read schedules a gap before the next read.
            pass
        return value

    def write(self, _attribute, _value):
        self.writes.append((_attribute, _value))
        raise AssertionError("This control must be read-only")


def make_control(clock, backend, **kwargs):
    return ReadControl(backend.read, clock.boottime, clock.monotonic,
                       clock.epoch, service_start_boottime=100.0, **kwargs)


class ReadControlTests(unittest.TestCase):
    def test_plan_is_exact_timestamped_read_only_and_no_import_io(self):
        self.assertEqual(MODE_SEQUENCE, (
            "treatment", "control", "control", "treatment",
            "treatment", "control", "control", "treatment",
        ))
        clock = FakeClock()
        backend = FakeBackend(clock)
        control = make_control(clock, backend)
        self.assertEqual(backend.calls, [])
        result = control.capture()
        self.assertEqual([x["label"] for x in result["plan"]], [
            "usb_pre", "status_pre", "wake_reason", "current_now_pre",
            "current_avg_pre", "middle_charge_counter", "middle_shadow",
            "middle_raw", "usb_mid", "status_mid", "current_avg_post",
            "current_now_post", "status_post", "usb_post",
        ])
        self.assertEqual(len(result["plan"]), MAX_PLAN_READS)
        self.assertEqual(len(result["trace"]), MAX_PLAN_READS)
        for item in result["trace"]:
            self.assertIn("before", item)
            self.assertIn("after", item)
            self.assertIn("value", item)
            self.assertLessEqual(item["duration_s"], 0.25)
        self.assertTrue(result["complete"])
        self.assertFalse(any("charge_done" in x for x in backend.calls))
        self.assertFalse(any("set_" in x or "write" in x for x in backend.calls))
        self.assertEqual(backend.writes, [])

    def test_simple_before_after_false_positive_from_time_alone(self):
        clock = FakeClock()
        backend = FakeBackend(clock, time_only=True)
        backend.begin_callback()
        naive_before = int(backend.read("bms/current_avg"))
        clock.advance(2.0)
        naive_after = int(backend.read("bms/current_avg"))
        self.assertEqual(naive_after - naive_before, 2010)  # slope × elapsed, no access effect

        deltas = {"treatment": [], "control": []}
        control = make_control(clock, backend)
        for _ in range(8):
            backend.begin_callback()
            rec = control.capture()
            vals = rec["observed"]
            deltas[rec["mode"]].append(int(vals["current_avg_post"]) - int(vals["current_avg_pre"]))
        self.assertEqual(len(deltas["treatment"]), 4)
        self.assertEqual(len(deltas["control"]), 4)
        self.assertEqual(set(deltas["treatment"]), {60})
        self.assertEqual(set(deltas["control"]), {60})
        self.assertEqual(statistic_mean(deltas["treatment"]), statistic_mean(deltas["control"]))

    def test_synthetic_access_effect_is_detectable_but_not_mechanistically_identified(self):
        clock = FakeClock()
        backend = FakeBackend(clock, time_only=True, access_effect=True)
        control = make_control(clock, backend)
        deltas = {"treatment": [], "control": []}
        for _ in MODE_SEQUENCE:
            backend.begin_callback()
            rec = control.capture()
            self.assertTrue(rec["complete"])
            vals = rec["observed"]
            deltas[rec["mode"]].append(int(vals["current_avg_post"]) - int(vals["current_avg_pre"]))
        self.assertEqual(len(backend.calls), 8 * MAX_PLAN_READS)
        self.assertEqual(set(deltas["treatment"]), {1060})
        self.assertEqual(set(deltas["control"]), {60})
        # This only verifies the planned contrast against a deliberately synthetic backend.
        # It does not show that real SRAM/DMA access causes a hardware filter update.

    def test_stop_on_usb_reconnect_at_midpoint(self):
        clock = FakeClock()
        backend = FakeBackend(clock)
        backend.usb_values = ["0", "1"]  # preflight then midpoint
        control = make_control(clock, backend)
        result = control.capture()
        self.assertEqual(result["stop_reason"], "usb_not_disconnected")
        self.assertNotIn("bms/current_avg", backend.calls[backend.calls.index("usb/online", 1) + 1:])
        before = len(backend.calls)
        self.assertFalse(control.capture()["captured"])
        self.assertEqual(len(backend.calls), before)

    def test_stop_immediately_after_read_error(self):
        clock = FakeClock()
        backend = FakeBackend(clock)
        backend.error_attribute = "bms/charge_counter"
        control = make_control(clock, backend)
        result = control.capture()
        self.assertEqual(result["stop_reason"], "read_error")
        self.assertEqual(result["trace"][-1]["error"]["type"], "OSError")
        self.assertIn("before", result["trace"][-1])
        self.assertIn("after", result["trace"][-1])
        self.assertEqual(backend.calls[-1], "bms/charge_counter")
        self.assertNotIn("bms/current_avg", backend.calls[backend.calls.index("bms/charge_counter") + 1:])

    def test_read_budget_exhaustion_stops_before_next_attempt(self):
        clock = FakeClock()
        backend = FakeBackend(clock)
        control = make_control(clock, backend, read_budget=5)
        result = control.capture()
        self.assertEqual(result["stop_reason"], "read_budget_exhausted")
        self.assertEqual(len(result["trace"]), 5)
        self.assertEqual(len(backend.calls), 5)

    def test_blocked_read_is_detected_only_after_return(self):
        clock = FakeClock()
        backend = FakeBackend(clock)
        backend.slow_attribute = "bms/current_avg"
        control = make_control(clock, backend)
        result = control.capture()
        self.assertEqual(result["stop_reason"], "read_duration_over_limit")
        self.assertGreater(result["trace"][-1]["duration_s"], 0.25)
        self.assertEqual(backend.calls[-1], "bms/current_avg")
        self.assertEqual(len(backend.calls), len(result["trace"]))

    def test_interread_gap_is_checked_before_next_read(self):
        clock = FakeClock()
        backend = FakeBackend(clock)
        control = make_control(clock, backend, max_interread_gap_s=0.25)
        # Advance between completed read and the next read's before timestamp.
        original_after = control._stamp
        stamps = 0
        def jump_after_first_read():
            nonlocal stamps
            stamps += 1
            # callback-start=1, first-read-before=2, first-read-after=3;
            # make next read's before stamp observe the gap.
            if stamps == 4:
                clock.advance(0.4)
            return original_after()
        control._stamp = jump_after_first_read
        result = control.capture()
        self.assertEqual(result["stop_reason"], "interread_gap_over_limit")
        self.assertEqual(len(result["trace"]), 1)
        self.assertEqual(len(backend.calls), 1)

    def test_deadline_and_eight_callback_cap(self):
        clock = FakeClock()
        backend = FakeBackend(clock)
        control = make_control(clock, backend, max_callbacks=2)
        self.assertTrue(control.capture()["captured"])
        self.assertTrue(control.capture()["captured"])
        before = len(backend.calls)
        self.assertEqual(control.capture()["stop_reason"], "callback_limit_reached")
        self.assertEqual(len(backend.calls), before)

        late_clock = FakeClock()
        late_backend = FakeBackend(late_clock)
        late_control = make_control(late_clock, late_backend)
        late_clock.advance(64800.0)
        result = late_control.capture()
        self.assertFalse(result["captured"])
        self.assertEqual(result["stop_reason"], "service_deadline")
        self.assertEqual(late_backend.calls, [])

        edge_clock = FakeClock()
        edge_backend = FakeBackend(edge_clock)
        edge_control = make_control(edge_clock, edge_backend)
        edge_clock.advance(64799.99)
        edge_backend.begin_callback()
        edge_result = edge_control.capture()
        self.assertEqual(edge_result["stop_reason"], "service_deadline")
        self.assertEqual(len(edge_backend.calls), 1)


def statistic_mean(groups):
    return sum(groups) / len(groups)


if __name__ == "__main__":
    unittest.main(verbosity=2)

