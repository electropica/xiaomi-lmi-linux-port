#!/usr/bin/env python3
"""Operator-independent preflight tests using already-built private inputs.

Usage: python3 test-stage.py INPUTS_DIRECTORY. No image build or chroot.
"""
import hashlib, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
source=Path(sys.argv.pop(1)).resolve()
stage=Path(__file__).with_name('stage.py')

class StageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.inputs=self.root/'inputs'
        shutil.copytree(source,self.inputs)
        self.dest=self.root/'stage'
    def tearDown(self): self.tmp.cleanup()
    def run_stage(self):
        return subprocess.run([sys.executable,str(stage),'--inputs',str(self.inputs),'--destination',str(self.dest)],capture_output=True,text=True)
    def test_real_inputs_and_asset_copy(self):
        result=self.run_stage()
        self.assertEqual(result.returncode,0,result.stderr)
        for name in ['tfa98xx.cnt','upower_1.90.9-1+lmi1_arm64.deb']:
            self.assertEqual((self.dest/'inputs'/name).read_bytes(),(source/name).read_bytes())
        self.assertTrue((self.dest/'apps/lmi-flashlight.py').is_file())
        self.assertTrue((self.dest/'audio/91-lmi-microphone.conf').is_file())
        self.assertTrue((self.dest/'power/lmi-cpu-idle.service').is_file())
        for name, subdir in [('lmi-npu-suspend','scripts'), ('lmi-npu-suspend-hook','files'), ('90-lmi-npu-suspend.conf','files')]:
            self.assertEqual((self.dest/'power'/name).read_bytes(),
                             (stage.resolve().parents[3]/'userspace/power'/subdir/name).read_bytes())
        self.assertTrue((self.dest/'time-seed/usr/local/libexec/lmi-time-seed').is_file())
        self.assertTrue((self.dest/'time-seed/etc/systemd/system/lmi-time-seed-save.timer').is_file())
        self.assertTrue((self.dest/'initialize-time-seed.sh').is_file())
    def test_missing_package_fails_before_staging(self):
        next(self.inputs.glob('upower_*.deb')).unlink()
        self.assertNotEqual(self.run_stage().returncode,0)
        self.assertFalse(self.dest.exists())
    def test_corrupt_firmware_fails_before_staging(self):
        (self.inputs/'tfa98xx.cnt').write_bytes(b'invalid')
        self.assertNotEqual(self.run_stage().returncode,0)
        self.assertFalse(self.dest.exists())
    def test_manifest_mismatch_fails_before_staging(self):
        f=self.inputs/'SHA256SUMS'
        f.write_text(f.read_text().replace('  upower_', '  wrong_'))
        self.assertNotEqual(self.run_stage().returncode,0)
        self.assertFalse(self.dest.exists())
    def test_existing_destination_preserved(self):
        self.dest.mkdir()
        marker=self.dest/'KEEP'
        marker.write_text('keep')
        self.assertNotEqual(self.run_stage().returncode,0)
        self.assertEqual(marker.read_text(),'keep')
    def test_symlink_package_refused(self):
        f=next(self.inputs.glob('upower_*.deb'))
        f.unlink()
        f.symlink_to(source/f.name)
        self.assertNotEqual(self.run_stage().returncode,0)
        self.assertFalse(self.dest.exists())

unittest.main()
