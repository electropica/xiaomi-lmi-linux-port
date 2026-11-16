import csv
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('boundary', Path(__file__).with_name('battery-sleep-boundaries.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class BoundaryTests(unittest.TestCase):
    def test_snapshot_preserves_values_and_missing_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            battery = root / 'sys/class/power_supply/qcom-battery'
            battery.mkdir(parents=True)
            (battery / 'capacity').write_text('72\n')
            (battery / 'status').write_text('Discharging\n')
            reg = root / 'sys/kernel/debug/regmap/0-02/registers'
            reg.parent.mkdir(parents=True)
            with reg.open('wb') as f:
                f.seek(0x4009 * 9)
                f.write(b'4009: a1\n400a: a1\n')
            def clock(clock_id):
                return 100.0 if clock_id == b.time.CLOCK_BOOTTIME else 90.0
            row = dict(zip(b.FIELDS, b.snapshot(root, 'pre', clock)))
            self.assertEqual((row['capacity_pct'], row['status']), ('72', 'Discharging'))
            self.assertEqual((row['msoc'], row['msoc_mirror']), ('161', '161'))
            self.assertTrue(row['voltage_uv'].startswith('N/A:'))
            self.assertEqual((row['boottime_s'], row['monotonic_s']), ('100.000000', '90.000000'))
            with self.assertRaises(ValueError):
                b.snapshot(root, 'invalid', clock)

    @unittest.skipUnless(os.geteuid() == 0, 'root required for ownership checks')
    def test_append_and_refuse_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            row = tuple('value' for _ in b.FIELDS)
            b.append_record(directory, row)
            b.append_record(directory, row)
            with (directory / 'sleep-boundaries.csv').open() as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[0], list(b.FIELDS))
            self.assertEqual(rows[1:], [list(row), list(row)])
            (directory / 'sleep-boundaries.csv').unlink()
            (directory / 'sleep-boundaries.csv').write_text('unexpected,header\n')
            with self.assertRaises(ValueError):
                b.append_record(directory, row)
            self.assertEqual((directory / 'sleep-boundaries.csv').read_text(), 'unexpected,header\n')
            (directory / 'sleep-boundaries.csv').unlink()
            target = directory / 'other'
            target.write_text('untouched')
            (directory / 'sleep-boundaries.csv').symlink_to(target)
            with self.assertRaises(OSError):
                b.append_record(directory, row)
            self.assertEqual(target.read_text(), 'untouched')

if __name__ == '__main__':
    unittest.main()
