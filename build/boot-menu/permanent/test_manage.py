import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import manage

spec = importlib.util.spec_from_file_location('verify_mobian', Path(__file__).with_name('verify-mobian.py'))
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class MenuTests(unittest.TestCase):
    def test_no_flash_or_device_contact_without_runtime_proof(self):
        run = unittest.mock.Mock()
        with self.assertRaises(RuntimeError):
            manage.install(Path('unused'), {'entries': {}}, run)
        run.assert_not_called()

    def test_missing_outcome_blocks_installation(self):
        value = {'mobian_proof': {'menu_sha256': manage.MENU_SHA,
                 'direct_marker': True, 'dedicated_root_confirmed': True}, 'entries': {}}
        with self.assertRaises(RuntimeError):
            manage.require_qualified(value)

    def test_wrong_product_refuses_before_write(self):
        outputs = iter(['serial fastboot\n', 'product: other\n'])
        with self.assertRaises(RuntimeError):
            manage.fastboot_preflight(Path('fake.exe'), lambda *args: next(outputs))

    def test_wrong_partition_refuses_before_write(self):
        outputs = iter(['serial fastboot\n', 'product: lmi\n', 'partition-size:boot: 0x1000\n'])
        with self.assertRaises(RuntimeError):
            manage.fastboot_preflight(Path('fake.exe'), lambda *args: next(outputs))

    def test_two_devices_refused(self):
        with self.assertRaises(RuntimeError):
            manage.fastboot_preflight(Path('fake.exe'), lambda *args: 'one fastboot\ntwo fastboot\n')

    def test_visual_mobian_return_without_marker_is_not_direct_boot(self):
        with self.assertRaises(RuntimeError):
            verify.validate_runtime({'cmdline': 'root=UUID=example'})

    def test_wrong_root_backing_refused(self):
        with self.assertRaises(RuntimeError):
            verify.validate_runtime({'cmdline': 'lmi_menu=outer-v1',
                'root_block': 'loop0p2', 'root_loop_backing': '/dev/sda34'})

    def test_marker_and_dedicated_root_accepted(self):
        verify.validate_runtime({'cmdline': 'quiet lmi_menu=outer-v1',
            'root_block': 'loop0p2', 'root_loop_backing': '/dev/sda35',
            'mobian_partition_sectors': str(17179869184 // 512)})

    def test_installed_readback_must_match(self):
        with self.assertRaises(RuntimeError):
            verify.validate_runtime({'cmdline': 'lmi_menu=outer-v1',
                'root_block': 'loop0p2', 'root_loop_backing': '/dev/sda35',
                'mobian_partition_sectors': str(17179869184 // 512),
                'installed_boot_prefix_sha256': 'wrong'}, installed=True)


if __name__ == '__main__':
    unittest.main()
