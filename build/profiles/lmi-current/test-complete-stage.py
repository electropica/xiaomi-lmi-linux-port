#!/usr/bin/env python3
"""Staging tests only: tiny metadata/ELF fixtures are never installable camera binaries."""
import hashlib,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
repo=Path(__file__).resolve().parents[3];stable=Path(sys.argv.pop(1))
sys.path.insert(0,str(repo/'userspace/camera/snapshot-bundle'))
from importlib.machinery import SourceFileLoader
checker=SourceFileLoader('bundle_check',str(repo/'userspace/camera/snapshot-bundle/check-bundle.py')).load_module()
class CompleteTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.inputs=self.root/'inputs';shutil.copytree(stable,self.inputs)
  for name,arch in [('phosh','arm64'),('phosh-common','all')]:
   tree=self.root/name;(tree/'DEBIAN').mkdir(parents=True)
   version='0.46.0-3+deb13u1+lmigaugewake3+homedrag2'
   (tree/'DEBIAN/control').write_text(f'Package: {name}\nVersion: {version}\nArchitecture: {arch}\nMaintainer: Test <test@example.invalid>\nDescription: metadata-only preflight fixture\n')
   subprocess.run(['dpkg-deb','--build',str(tree),str(self.inputs/f'{name}_{version}_{arch}.deb')],check=True,capture_output=True)
  names=[line.split('  ',1)[1] for line in (stable/'SHA256SUMS').read_text().splitlines()]
  names=[n.replace('lmigaugewake3_','lmigaugewake3+homedrag2_') for n in names]
  (self.inputs/'SHA256SUMS').write_text(''.join(hashlib.sha256((self.inputs/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in names))
  self.bundle=self.root/'bundle';self.bundle.mkdir()
  for name in checker.NAMES:
   p=self.bundle/name
   if name in checker.BINARIES:
    data=bytearray(64);data[:6]=b'\x7fELF\x02\x01';data[18:20]=(183).to_bytes(2,'little');p.write_bytes(data)
   elif name=='org.gnome.Snapshot.desktop':p.write_text('Exec=/usr/local/bin/lmi-snapshot\n')
   elif name=='install.sh':p.write_text('#!/bin/bash\nexit 0\n')
   elif name.endswith('.py') or name=='lmi-snapshot':p.write_text('pass\n')
   else:p.write_text('fixture\n')
  self.manifest()
  self.dest=self.root/'staged'
 def tearDown(self):self.temp.cleanup()
 def manifest(self):
  (self.bundle/'SHA256SUMS').write_text(''.join(hashlib.sha256((self.bundle/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in sorted(checker.NAMES)))
 def run_stage(self):
  env=os.environ.copy();env.update(M1_COMPLETE_LMI_PROFILE='1',M1_COMPLETE_CAMERA_BUNDLE=str(self.bundle))
  return subprocess.run(['python3',str(repo/'build/profiles/lmi-current/stage.py'),'--inputs',str(self.inputs),'--destination',str(self.dest)],env=env,capture_output=True,text=True)
 def test_complete_pair_and_camera_copied(self):
  result=self.run_stage();self.assertEqual(result.returncode,0,result.stderr)
  self.assertTrue((self.dest/'COMPLETE_PROFILE').is_file())
  self.assertEqual((self.dest/'camera/SHA256SUMS').read_bytes(),(self.bundle/'SHA256SUMS').read_bytes())
  self.assertTrue((self.dest/'inputs/phosh_0.46.0-3+deb13u1+lmigaugewake3+homedrag2_arm64.deb').is_file())
 def test_camera_tampering_prevents_staging(self):
  (self.bundle/'lmi-snapshot').write_text('changed')
  self.assertNotEqual(self.run_stage().returncode,0);self.assertFalse(self.dest.exists())
 def test_wrong_binary_architecture_prevents_staging(self):
  (self.bundle/'snapshot-focus').write_bytes(b'not an ARM executable');self.manifest()
  self.assertNotEqual(self.run_stage().returncode,0);self.assertFalse(self.dest.exists())
 def test_missing_native_pair_prevents_staging(self):
  next(self.inputs.glob('phosh-common_*homedrag2*')).unlink()
  self.assertNotEqual(self.run_stage().returncode,0);self.assertFalse(self.dest.exists())
 def test_manifest_path_traversal_prevents_staging(self):
  with (self.bundle/'SHA256SUMS').open('a') as f:f.write('0'*64+'  ../outside\n')
  self.assertNotEqual(self.run_stage().returncode,0);self.assertFalse(self.dest.exists())
unittest.main()
