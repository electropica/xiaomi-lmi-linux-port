"""Pure clock-model checks: no device access or clock-setting calls."""
from importlib.machinery import SourceFileLoader
from pathlib import Path
import unittest

model = SourceFileLoader('rtc_anchor_model', str(Path(__file__).with_name('rtc-time-anchor.py'))).load_module()


class AnchorTests(unittest.TestCase):
    def setUp(self):
        self.anchor = {'version': 1, 'rtc_name': 'test-rtc', 'rtc_epoch': 1000,
                       'unix_epoch': 1792382400.25}

    def test_offline_elapsed_time_advances_stale_clock(self):
        result = model.evaluate(self.anchor, 'test-rtc', 4600, 1792382400)
        self.assertEqual(result['action'], 'advance')
        self.assertEqual(result['target_epoch'], 1792386000.25)
        self.assertTrue(result['rtc_not_written'])

    def test_current_or_newer_clock_is_never_moved_back(self):
        for now in (1792386000, 1792386001, 1792387000):
            self.assertEqual(model.evaluate(self.anchor, 'test-rtc', 4600, now)['action'], 'unchanged')

    def test_counter_reset_is_rejected(self):
        with self.assertRaises(ValueError):
            model.evaluate(self.anchor, 'test-rtc', 999, 1792382400)

    def test_large_epoch_change_or_expiry_is_rejected(self):
        with self.assertRaises(ValueError):
            model.evaluate(self.anchor, 'test-rtc', 1001+model.MAX_ELAPSED, 1792382400)

    def test_different_rtc_is_rejected(self):
        with self.assertRaises(ValueError):
            model.evaluate(self.anchor, 'other-rtc', 4600, 1792382400)

    def test_invalid_reference_is_rejected(self):
        for value in (float('nan'), float('inf'), True, 1000, '1792382400'):
            with self.assertRaises(ValueError):
                model.evaluate({**self.anchor, 'unix_epoch': value}, 'test-rtc', 1000, 1792382400)

    def test_unknown_state_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            model.evaluate({**self.anchor, 'extra': 1}, 'test-rtc', 1000, 1792382400)


if __name__ == '__main__':
    unittest.main()
