#!/usr/bin/env python3
"""Execute output-path and immutable-reference controls without compiling or a phone."""
from pathlib import Path
import argparse,importlib.util,subprocess,sys,tempfile
sys.dont_write_bytecode=True

def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repository',type=Path,default=Path('/home/linuxagent/xiaomi-lmi-linux-port'));a=ap.parse_args()
 here=Path(__file__).resolve().parent;base=a.repository/'build/boot-menu/external-mobian'
 pack=load('reference_pack',base/'pack-outer.py');candidate=load('candidate',here/'build-menu.py');baseline=load('baseline',base/'build-external.py')
 with tempfile.TemporaryDirectory(prefix='lmi-output-guard-') as td:
  root=Path(td);reference=root/'boot-lmi-outer-dual-extent-test.img'
  pack.write_image(reference,b'qualified');pack.write_image(reference,b'qualified')
  try:pack.write_image(reference,b'diagnostic')
  except RuntimeError:pass
  else:raise AssertionError('Reference overwrite accepted')
  assert reference.read_bytes()==b'qualified'
  diagnostic=root/'boot-lmi-fg-dt-order-test.img';pack.write_image(diagnostic,b'one');pack.write_image(diagnostic,b'two');assert diagnostic.read_bytes()==b'two'
  link=root/'link.img';link.symlink_to(reference)
  try:pack.write_image(link,b'bad')
  except RuntimeError:pass
  else:raise AssertionError('Symlink accepted')
  assert reference.read_bytes()==b'qualified'
  files=candidate.diagnostic_files(baseline.files());shell=files['build.sh'].decode()
  assert 'mount --bind "$build_root/output/fg-dt-order-candidate" "$rootfs/output"' in shell
  assert 'mount --bind "$build_root/output" "$rootfs/output"' not in shell
  assert 'mount -o remount,bind,ro "$rootfs/qualified-output"' in shell
  assert 'tee "$build_root/output/fg-dt-order-candidate/build.log"' in shell
  assert "Path('/qualified-output/boot-lmi-outer-dual-extent-test.img')" in files['external-mobian/make-outer.py'].decode()
  assert "target=out/'boot-lmi-fg-dt-order-test.img'" in files['external-mobian/pack-outer.py'].decode()
  assert "out/'fg-dt-order-artifact-manifest.json'" in files['external-mobian/pack-outer.py'].decode()
  assert candidate.OUTPUT==candidate.OUTPUT_ROOT/'fg-dt-order-candidate' and candidate.LOCKED.parent==candidate.OUTPUT_ROOT
  p=root/'build.sh';p.write_text(shell);subprocess.run(['bash','-n',str(p)],check=True)
 print('PASS: actual packer reference/idempotence/candidate/symlink controls; isolated RW output, RO reference, log, manifest and shell syntax')
if __name__=='__main__':main()
