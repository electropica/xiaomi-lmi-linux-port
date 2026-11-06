import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('guard', pathlib.Path(__file__).with_name('lmi-usb-pc-guard.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class SnapshotTests(unittest.TestCase):
    def test_equivalent_decision_and_skip_only_when_safe(self):
        from itertools import product
        for online, udc, carrier, partner, vbus, held in product(
            ('0', '1', None), ('configured', 'not attached'), ('0', '1'),
            (False, True), ('5000000', '3999999', None), (False, True)
        ):
            with tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                partner_path = root / 'class/typec/port0-partner'
                if partner:
                    partner_path.mkdir(parents=True)
                reads = []
                def fake_read(path):
                    reads.append(str(path))
                    if str(path).endswith('/online'): return online
                    if str(path).endswith('/state'): return udc
                    if str(path).endswith('/carrier'): return carrier
                    return vbus
                with patch.object(guard, 'read', side_effect=fake_read):
                    result = guard.snapshot(root, held)
                candidate = online == '1' and udc == 'configured' and carrier == '1' and partner
                original = {'online': online, 'udc': udc, 'carrier': carrier, 'partner': partner, 'vbus': vbus}
                self.assertEqual(guard.qualifies(result), guard.qualifies(original))
                self.assertEqual(any('in_voltage_usbin_v_input' in p for p in reads), candidate or held)
                self.assertEqual(result['vbus_skipped'], not (candidate or held))


if __name__ == '__main__':
    unittest.main()
