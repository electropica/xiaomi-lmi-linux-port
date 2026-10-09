"""Synthetic metadata guards; captured device reports stay outside Git."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('mount_preparer', here/'prepare-android-super-mounts.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

TEXT = '''Metadata version: 10.0
Partition table:
------------------------
  Name: system
  Group: test_dynamic
  Attributes: readonly
  Extents:
    0 .. 2237583 linear super 2048
------------------------
  Name: vendor
  Group: test_dynamic
  Attributes: readonly
  Extents:
    0 .. 1602399 linear super 2240512
------------------------
Super partition layout:
------------------------
Block device table:
------------------------
  Partition name: super
  First sector: 2048
  Size: 3221225472 bytes
  Flags: none
'''
DOCUMENT = {'enabled': True, 'block_devices': [{'name': 'super', 'size': '3221225472'}],
            'partitions': [{'name': 'system', 'is_dynamic': True, 'size': '1145643008', 'fs_type': 'ext4'},
                           {'name': 'vendor', 'is_dynamic': True, 'size': '820428800', 'fs_type': 'erofs'}]}

class Guards(unittest.TestCase):
    def test_reviewed_values_and_only_mount_lines_changed(self):
        reference = here.parent/'scripts/lmi-android-wifi-mounts'
        if not reference.is_file():
            reference = here/'lmi-android-wifi-mounts-reference.sh'
        original = reference.read_bytes()
        candidate, report = module.prepare(TEXT.encode(), json.dumps(DOCUMENT).encode(), original)
        self.assertEqual(report['partitions']['vendor']['offset'], 1147142144)
        self.assertEqual(report['partitions']['system']['size'], 1145643008)
        changed = [(a,b) for a,b in zip(original.decode().splitlines(),candidate.splitlines()) if a!=b]
        self.assertEqual(len(changed), 2)
        self.assertTrue(all(a.startswith('mount_loop_ro "$super"') for a,b in changed))

    def test_multiple_extents_rejected(self):
        text = TEXT.replace('0 .. 1602399 linear super 2240512', '0 .. 799999 linear super 2240512\n    800000 .. 1602399 linear super 4000000')
        with self.assertRaises(ValueError):module.layout(text, DOCUMENT)

    def test_foreign_device_rejected(self):
        with self.assertRaises(ValueError):module.layout(TEXT.replace('linear super 2240512','linear userdata 2240512'), DOCUMENT)

    def test_overlapping_extents_rejected(self):
        with self.assertRaises(ValueError):module.layout(TEXT.replace('linear super 2240512','linear super 2048'), DOCUMENT)

    def test_out_of_bounds_rejected(self):
        with self.assertRaises(ValueError):module.layout(TEXT.replace('linear super 2240512','linear super 9000000'), DOCUMENT)

    def test_size_disagreement_rejected(self):
        data = copy.deepcopy(DOCUMENT);data['partitions'][1]['size']='820429312'
        with self.assertRaises(ValueError):module.layout(TEXT,data)

    def test_duplicate_partition_rejected(self):
        data = copy.deepcopy(DOCUMENT);data['partitions'].append(copy.deepcopy(data['partitions'][1]))
        with self.assertRaises(ValueError):module.layout(TEXT,data)

    def test_other_metadata_version_rejected(self):
        with self.assertRaises(ValueError):module.layout(TEXT.replace('10.0','10.2'),DOCUMENT)

    def test_changed_reference_rejected(self):
        with self.assertRaises(ValueError):module.prepare(TEXT.encode(),json.dumps(DOCUMENT).encode(),b'#!/bin/sh\nexit 0\n')

if __name__=='__main__':unittest.main()
