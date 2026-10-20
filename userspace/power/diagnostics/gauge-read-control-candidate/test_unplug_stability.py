"""Replay the observed early USB cycle with fake clocks and no device access."""
import unittest
from observer import LifecycleEngine, WAITING_UNPLUG, OBSERVING
from test_observer import FakeClock, FakeReader, FakeSink


class StabilityTests(unittest.TestCase):
    def make_engine(self):
        clock = FakeClock()
        reader = FakeReader(clock)
        sink = FakeSink()
        engine = LifecycleEngine(reader, clock.boottime, clock.monotonic,
                                 clock.epoch, sink.write, close_sink=sink.close)
        engine.arm()
        return clock, reader, sink, engine

    def test_five_second_disconnect_then_reconnect_does_not_end_observation(self):
        clock, reader, sink, engine = self.make_engine()
        reader.usb = '0'
        engine.poll_while_awake()
        engine.on_prepare_for_sleep(False)
        self.assertEqual(reader.gauge_calls, [])
        clock.advance(5)
        reader.usb = '1'
        engine.poll_while_awake()
        self.assertFalse(engine.stopped)
        self.assertEqual(engine.phase, WAITING_UNPLUG)
        self.assertIn('unplug-candidate-cancelled', [r['event'] for r in sink.rows])
        self.assertNotIn('finished', [r['event'] for r in sink.rows])

        # The later real unplug must start its own full stability interval.
        reader.usb = '0'
        engine.poll_while_awake()
        clock.advance(19)
        engine.poll_while_awake()
        self.assertEqual(engine.phase, WAITING_UNPLUG)
        self.assertEqual(reader.gauge_calls, [])
        clock.advance(1)
        engine.poll_while_awake()
        self.assertEqual(engine.phase, OBSERVING)
        self.assertEqual(sum(r['event'] == 'unplugged' for r in sink.rows), 1)
        engine.on_prepare_for_sleep(False)
        self.assertEqual(engine.control.callbacks_attempted, 1)

    def test_reconnection_after_stable_start_still_stops_immediately(self):
        clock, reader, sink, engine = self.make_engine()
        reader.usb = '0'
        engine.poll_while_awake()
        clock.advance(20)
        engine.poll_while_awake()
        self.assertEqual(engine.phase, OBSERVING)
        reader.usb = '1'
        engine.poll_while_awake()
        self.assertTrue(engine.stopped)
        self.assertEqual(engine.stop_reason, 'usb_reconnected')
        before = len(reader.calls)
        engine.on_prepare_for_sleep(False)
        engine.poll_while_awake()
        self.assertEqual(len(reader.calls), before)
        self.assertEqual(reader.gauge_calls, [])
        self.assertEqual(sink.close_count, 1)


if __name__ == '__main__':
    unittest.main()
