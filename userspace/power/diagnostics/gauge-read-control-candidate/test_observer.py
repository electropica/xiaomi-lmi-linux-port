"""Lifecycle integration tests with only fake clocks, readers, and sinks."""
import sys
import unittest
from contextlib import redirect_stderr
from io import StringIO

import observer


class FakeClock:
    def __init__(self):
        self.boot = 100.0
        self.mono = 20.0
        self.epoch_value = 1000.0

    def advance(self, seconds):
        self.boot += seconds
        self.mono += seconds
        self.epoch_value += seconds

    def boottime(self):
        return self.boot

    def monotonic(self):
        return self.mono

    def epoch(self):
        return self.epoch_value


class FakeReader:
    def __init__(self, clock):
        self.clock = clock
        self.calls = []
        self.usb = "1"
        self.usb_script = []
        self.fail_attribute = None
        self.slow_attribute = None
        self.gauge_calls = []
        self.usb_reads = 0

    def __call__(self, attribute):
        self.calls.append(attribute)
        if attribute.startswith("bms/"):
            self.gauge_calls.append(attribute)
        try:
            if attribute == self.fail_attribute:
                raise OSError("simulated sysfs read error")
            if attribute == "usb/online":
                self.usb_reads += 1
                if self.usb_script:
                    value = self.usb_script.pop(0)
                else:
                    value = self.usb
            elif attribute == "battery/status":
                value = "Discharging"
            elif attribute == "wakeup_reasons/last_resume_reason":
                value = "438 msoc-delta"
            elif attribute == "bms/current_now":
                value = "49316"
            elif attribute == "bms/current_avg":
                value = "49313"
            elif attribute in ("bms/charge_counter", "bms/charge_counter_shadow", "bms/charge_now_raw"):
                value = "1000000"
            else:
                raise AssertionError("Unexpected fake read: " + attribute)
            return value
        finally:
            self.clock.advance(0.3 if attribute == self.slow_attribute else 0.01)

class FakeSink:
    def __init__(self):
        self.rows = []
        self.close_count = 0

    def write(self, row):
        self.rows.append(row)

    def close(self):
        self.close_count += 1


class ObserverIntegrationTests(unittest.TestCase):
    def make_engine(self, **kwargs):
        clock = FakeClock()
        reader = FakeReader(clock)
        sink = FakeSink()
        engine = observer.LifecycleEngine(
            reader, clock.boottime, clock.monotonic, clock.epoch,
            sink.write, close_sink=sink.close, **kwargs)
        return clock, reader, sink, engine

    def connect_to_observation(self, clock, reader, engine):
        self.assertTrue(engine.arm())
        reader.usb = "1"
        self.assertTrue(engine.poll_while_awake())
        reader.usb = "0"
        self.assertTrue(engine.poll_while_awake())
        self.assertEqual(engine.phase, observer.OBSERVING)

    def test_waiting_or_plugged_state_never_measures_gauge(self):
        clock, reader, sink, engine = self.make_engine()
        engine.arm()
        engine.on_prepare_for_sleep(True)
        engine.on_prepare_for_sleep(False)
        self.assertEqual(reader.calls, [])
        reader.usb = "1"
        engine.poll_while_awake()
        self.assertEqual(reader.gauge_calls, [])
        reader.usb = "0"
        engine.poll_while_awake()
        self.assertEqual(engine.phase, observer.OBSERVING)
        self.assertEqual(reader.gauge_calls, [])
        self.assertTrue(engine.on_prepare_for_sleep(False))
        self.assertGreater(len(reader.gauge_calls), 0)

    def test_natural_resume_control_is_first_gauge_read_and_entry_time_is_preserved(self):
        clock, reader, sink, engine = self.make_engine()
        self.connect_to_observation(clock, reader, engine)
        engine.on_prepare_for_sleep(True)
        gauge_before = len(reader.gauge_calls)
        callback_entry = clock.boottime()
        engine.on_prepare_for_sleep(False)
        resume = [x for x in sink.rows if x["event"] == "resume-signal"][-1]
        trace = resume["probe"]["trace"]
        self.assertEqual(resume["boottime"], callback_entry)
        self.assertLessEqual(resume["boottime"], resume["probe"]["callback_start"]["boottime"])
        self.assertEqual(reader.gauge_calls[gauge_before], "bms/current_now")
        self.assertNotIn("battery/charge_counter", reader.calls)
        self.assertEqual(trace[3]["label"], "current_now_pre")
        self.assertLessEqual(resume["boottime"], trace[3]["before"]["boottime"])
        traced_gauge_reads = [x["attribute"] for x in trace if x["attribute"].startswith("bms/")]
        self.assertEqual(reader.gauge_calls[gauge_before:], traced_gauge_reads)

    def test_eighth_attempt_finishes_once_and_ninth_invocation_reads_nothing(self):
        clock, reader, sink, engine = self.make_engine()
        self.connect_to_observation(clock, reader, engine)
        for index in range(8):
            if index:
                self.assertTrue(engine.on_prepare_for_sleep(True))
            engine.on_prepare_for_sleep(False)
        self.assertTrue(engine.stopped)
        self.assertEqual(engine.stop_reason, "callback_limit")
        self.assertEqual(engine.control.callbacks_attempted, 8)
        before = len(reader.calls)
        engine.on_prepare_for_sleep(False)
        engine.poll_while_awake()
        self.assertEqual(len(reader.calls), before)
        self.assertEqual(sum(x["event"] == "finished" for x in sink.rows), 1)
        self.assertEqual(sink.close_count, 1)
        engine.finish("duplicate-stop")
        self.assertEqual(sum(x["event"] == "finished" for x in sink.rows), 1)
        self.assertEqual(sink.close_count, 1)

    def test_reconnect_inside_probe_is_traced_then_stops_without_more_reads(self):
        clock, reader, sink, engine = self.make_engine()
        engine.arm()
        reader.usb_script = ["1", "0", "0", "0", "1"]
        engine.poll_while_awake()
        engine.poll_while_awake()
        engine.on_prepare_for_sleep(True)
        before_resume = len(reader.calls)
        engine.on_prepare_for_sleep(False)
        resume = [x for x in sink.rows if x["event"] == "resume-signal"][-1]
        self.assertEqual(resume["probe"]["stop_reason"], "usb_not_disconnected")
        labels = [x["label"] for x in resume["probe"]["trace"]]
        self.assertIn("usb_mid", labels)
        self.assertNotIn("current_avg_post", labels)
        self.assertTrue(engine.stopped)
        self.assertEqual(engine.stop_reason, "usb_reconnected")
        self.assertEqual(reader.calls[-1], "usb/online")
        calls_at_return = len(reader.calls)
        self.assertEqual(calls_at_return, before_resume + len(resume["probe"]["trace"]))
        self.assertEqual(sink.close_count, 1)

    def test_getter_error_is_logged_and_no_later_gauge_read_occurs(self):
        clock, reader, sink, engine = self.make_engine()
        self.connect_to_observation(clock, reader, engine)
        engine.on_prepare_for_sleep(True)
        reader.fail_attribute = "bms/charge_counter"
        engine.on_prepare_for_sleep(False)
        resume = [x for x in sink.rows if x["event"] == "resume-signal"][-1]
        self.assertEqual(engine.stop_reason, "gauge_read_error")
        self.assertEqual(resume["probe"]["trace"][-1]["error"]["type"], "OSError")
        self.assertEqual(reader.calls[-1], "bms/charge_counter")
        self.assertEqual(sink.close_count, 1)

    def test_wait_and_total_deadlines_are_from_arm_and_do_not_read_after_expiry(self):
        clock, reader, sink, engine = self.make_engine()
        engine.arm()
        clock.advance(observer.MAX_UNPLUG_WAIT_SECONDS)
        self.assertFalse(engine.poll_while_awake())
        self.assertEqual(engine.stop_reason, "unplug_wait_timeout")
        self.assertEqual(reader.calls, [])
        self.assertEqual(sink.close_count, 1)

        clock2, reader2, sink2, engine2 = self.make_engine()
        self.connect_to_observation(clock2, reader2, engine2)
        clock2.advance(observer.MAX_TOTAL_SECONDS)
        before = len(reader2.calls)
        self.assertFalse(engine2.poll_while_awake())
        self.assertEqual(engine2.stop_reason, "total_timeout")
        self.assertEqual(len(reader2.calls), before)
        self.assertEqual(reader2.gauge_calls, [])

    def test_parent_metadata_budget_and_latency_stop_without_gauge_access(self):
        clock, reader, sink, engine = self.make_engine(max_parent_metadata_reads=1)
        engine.arm()
        reader.usb = "1"
        self.assertTrue(engine.poll_while_awake())
        self.assertFalse(engine.poll_while_awake())
        self.assertEqual(engine.stop_reason, "parent_metadata_budget")
        self.assertEqual(reader.usb_reads, 1)
        self.assertEqual(reader.gauge_calls, [])
        self.assertEqual(sink.close_count, 1)

        clock2, reader2, sink2, engine2 = self.make_engine()
        engine2.arm()
        reader2.slow_attribute = "usb/online"
        self.assertFalse(engine2.poll_while_awake())
        self.assertEqual(engine2.stop_reason, "parent_metadata_read_over_limit")
        self.assertEqual(reader2.gauge_calls, [])
        self.assertEqual(sink2.close_count, 1)

    def test_import_does_not_load_gi_or_start_a_collector(self):
        self.assertNotIn("gi", sys.modules)
        clock, reader, sink, engine = self.make_engine()
        self.assertEqual(engine.phase, "new")
        self.assertEqual(reader.calls, [])
        with redirect_stderr(StringIO()):
            self.assertEqual(observer.main([]), 2)
        self.assertNotIn("gi", sys.modules)


if __name__ == "__main__":
    unittest.main(verbosity=2)
