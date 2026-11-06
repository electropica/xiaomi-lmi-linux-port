import unittest
from compare_sleep import compare, ddr_rows


def row(phase, boot, bt, mono, count, duration):
    return {'event': 'systemd-sleep-hook', 'phase': phase, 'boot_id': boot,
            'boottime_seconds': bt, 'monotonic_seconds': mono,
            'qcom_stats': {'aosd': f'Count: {count}\nAccumulated Duration: {duration}\n'}}


class SleepComparisonTests(unittest.TestCase):
    def test_ddr_freq_and_low_power_stats_are_read_without_assuming_units(self):
        text = ('DDR LPM Stat Name:0xd4\tcount:0\tDuration (ticks):0\n'
                'DDR Freq 300Mhz:\tCP IDX:3\tcount:12\tDuration (ticks):240\n')
        self.assertEqual(ddr_rows(text)['DDR LPM Stat Name:0xd4'], (0, 0))
        self.assertEqual(ddr_rows(text)['DDR Freq 300Mhz'], (12, 240))

    def test_pairs_same_boot_and_reports_raw_counter_delta(self):
        result = compare([row('pre', 'boot', 100, 80, 3, 100), row('post', 'boot', 160, 85, 4, 125)])[0]
        self.assertEqual(result['suspended_seconds_estimate'], 55)
        self.assertEqual(result['counter_deltas_raw']['aosd']['Count'], 1)
        self.assertEqual(result['counter_deltas_raw']['aosd']['Accumulated Duration'], 25)
        self.assertIsNone(result['counter_deltas_raw']['cxsd']['Count'])

    def test_new_boot_and_counter_reset_are_not_interpreted_as_gain(self):
        self.assertEqual(compare([row('pre', 'a', 1, 1, 3, 4), row('post', 'b', 2, 2, 1, 2)])[0]['status'], 'identifiant de démarrage différent ou indisponible')
        result = compare([row('pre', 'a', 1, 1, 3, 4), row('post', 'a', 2, 2, 1, 2)])[0]
        self.assertIsNone(result['counter_deltas_raw']['aosd']['Count'])


if __name__ == '__main__':
    unittest.main()
