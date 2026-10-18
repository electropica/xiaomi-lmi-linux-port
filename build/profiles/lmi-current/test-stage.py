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
        for name in ['tfa98xx.cnt','upower_1.90.9-1+lmi1_arm64.deb','phosh_0.46.0-3+deb13u1+lmigaugewake3_arm64.deb','phosh-common_0.46.0-3+deb13u1+lmigaugewake3_all.deb','gnome-settings-daemon_48.1-1+lmiquietgauge3_arm64.deb','gnome-settings-daemon-common_48.1-1+lmiquietgauge3_all.deb']:
            self.assertEqual((self.dest/'inputs'/name).read_bytes(),(source/name).read_bytes())
        for name in ['phosh-quiet-resume.conf','gsd-quiet-resume.conf']:
            self.assertEqual((self.dest/'power'/name).read_bytes(),(stage.resolve().parents[3]/'kernel/diagnostics/power/userspace'/name).read_bytes())
        self.assertTrue((self.dest/'apps/lmi-flashlight.py').is_file())
        self.assertEqual((self.dest/'apps/install-chatty-safe.sh').read_bytes(),
                         (stage.resolve().parents[3]/'userspace/apps/files/install-chatty-safe.sh').read_bytes())
        installer=(self.dest/'profile/install.sh').read_text()
        self.assertIn('bash "$src/apps/install-chatty-safe.sh"',installer)
        self.assertNotIn('Exec=/usr/local/bin/lmi-chatty-safe %u|',installer)
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

    def test_missing_quiet_pair_fails_before_staging(self):
        (self.inputs/'phosh-common_0.46.0-3+deb13u1+lmigaugewake3_all.deb').unlink()
        self.assertNotEqual(self.run_stage().returncode,0)
        self.assertFalse(self.dest.exists())
    def test_manifest_symlink_refused(self):
        f=self.inputs/'SHA256SUMS'
        f.unlink();f.symlink_to(source/f.name)
        self.assertNotEqual(self.run_stage().returncode,0)
        self.assertFalse(self.dest.exists())
    def test_old_gsd_version_rejected_despite_matching_manifest(self):
        # Tiny metadata fixture: no actual GSD or ARM compilation.
        tree=self.root/'wrong-package';(tree/'DEBIAN').mkdir(parents=True)
        (tree/'DEBIAN/control').write_text('Package: gnome-settings-daemon\nVersion: 48.1-1+lmiquietgauge2\nArchitecture: arm64\nMaintainer: Test <test@example.invalid>\nDescription: staging rejection fixture\n')
        package=self.inputs/'gnome-settings-daemon_48.1-1+lmiquietgauge3_arm64.deb'
        subprocess.run(['dpkg-deb','--build',str(tree),str(package)],check=True,capture_output=True)
        manifest=self.inputs/'SHA256SUMS'
        lines=[]
        for line in manifest.read_text().splitlines():
            digest,name=line.split('  ',1)
            if name==package.name:digest=hashlib.sha256(package.read_bytes()).hexdigest()
            lines.append(digest+'  '+name)
        manifest.write_text('\n'.join(lines)+'\n')
        self.assertNotEqual(self.run_stage().returncode,0)
        self.assertFalse(self.dest.exists())

unittest.main()
