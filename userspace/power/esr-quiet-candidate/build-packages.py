#!/usr/bin/env python3
"""Operator-only incremental package build. Default preflight, no phone access."""
from pathlib import Path
import argparse,fcntl,hashlib,json,os,shutil,subprocess,sys,tempfile

ROOT=Path('/home/linuxagent/phosh-gauge-wake-build/rootfs')
TASK=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def verify(manifest):
 assert sha(TASK/'esr-delta-accept.patch')==manifest['patch_sha256']
 for spec in manifest['sources']:
  tree=ROOT/'build'/spec['tree'];assert tree.is_dir() and not tree.is_symlink()
  assert sha(tree/spec['file']) in (spec['before'],spec['after'])
  head=(tree/'debian/changelog').read_text().splitlines()[0]
  assert head in [spec['package']+' ('+v+') UNRELEASED; urgency=medium' for v in (spec['old'],spec['new'])]
  for pkg,arch in ((spec['package'],'arm64'),(spec['package']+'-common','all')):
   assert (ROOT/'build'/f'{pkg}_{spec["old"]}_{arch}.deb').is_file(), 'Rollback package missing'
 for rel,digest in manifest['preserve_home8'].items():
  assert not Path(rel).is_absolute() and '..' not in Path(rel).parts
  assert sha(ROOT/'build/phosh-0.46.0'/rel)==digest,rel

def patched_sources(manifest,tmp):
 for spec in manifest['sources']:
  target=tmp/spec['file'];target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(ROOT/'build'/spec['tree']/spec['file'],target)
 # All inputs must be either entirely old or entirely new for patch staging.
 states=[sha(tmp/s['file'])==s['after'] for s in manifest['sources']]
 if not all(states):
  assert not any(states),'Partial source preparation; inspect before retry'
  subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(TASK/'esr-delta-accept.patch')],cwd=tmp,check=True)
 for spec in manifest['sources']:assert sha(tmp/spec['file'])==spec['after']

def build(manifest,repo):
 assert os.geteuid()==0
 assert os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt')
 subprocess.run(['python3',str(repo/'userspace/camera/snapshot-bundle/prepare-chroot.py'),str(ROOT)],check=True)
 (ROOT/'dev/shm').mkdir(exist_ok=True)
 subprocess.run(['mount','-t','tmpfs','-o','mode=1777,nosuid,nodev,size=256m','tmpfs',str(ROOT/'dev/shm')],check=True)
 assert subprocess.check_output(['chroot',str(ROOT),'dpkg','--print-architecture'],text=True).strip()=='arm64'
 with tempfile.TemporaryDirectory(prefix='lmi-esr-build-source-') as td:
  tmp=Path(td);patched_sources(manifest,tmp)
  for spec in manifest['sources']:
   tree=ROOT/'build'/spec['tree'];target=tree/spec['file']
   shutil.copyfile(tmp/spec['file'],target)
   guest='/build/'+spec['tree']
   if not (tree/'debian/changelog').read_text().startswith(spec['package']+' ('+spec['new']+')'):
    subprocess.run(['chroot',str(ROOT),'/usr/bin/env','DEBIAN_FRONTEND=noninteractive','DEBFULLNAME=Local lmi','DEBEMAIL=local@example.invalid','/bin/sh','-c','cd "$1" && dch --newversion "$2" --distribution UNRELEASED "Keep guarded esr-delta gauge resumes quiet; preserve home8 and fifteen-second grace."','sh',guest,spec['new']],check=True)
   subprocess.run(['chroot',str(ROOT),'chown','builder:builder',guest+'/'+spec['file'],guest+'/debian/changelog'],check=True)
   stamp=tree/'debian/debhelper-build-stamp';assert not stamp.is_symlink()
   if stamp.exists():assert stamp.is_file();stamp.unlink()
  verify(manifest)
  for spec in manifest['sources']:
   subprocess.run(['chroot',str(ROOT),'/bin/bash','-c',
    'set -euo pipefail; export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin; cd "$1"; runuser -u builder -- env DEBIAN_FRONTEND=noninteractive DEB_BUILD_OPTIONS=parallel=2 dpkg-buildpackage -b -nc -us -uc -j2',
    'bash','/build/'+spec['tree']],check=True)
 verify(manifest)
 packages=[]
 for spec in manifest['sources']:
  for pkg,arch in ((spec['package'],'arm64'),(spec['package']+'-common','all')):
   p=ROOT/'build'/f'{pkg}_{spec["new"]}_{arch}.deb';assert p.is_file()
   actual=subprocess.check_output(['dpkg-deb','-f',str(p),'Version'],text=True).strip()
   assert actual==spec['new'];packages.append({'path':str(p),'sha256':sha(p)})
 (ROOT/'build/lmi-esrquiet1-build-result.json').write_text(json.dumps({'packages':packages,'identity':manifest,'phone_contact':False},indent=2)+'\n')
 print(json.dumps(packages,indent=2));print('ESR_QUIET_PACKAGES_BUILT\nNo phone installation, kernel or image build performed.')

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--inside',action='store_true',help=argparse.SUPPRESS)
 args=ap.parse_args();manifest=json.loads((TASK/'identity.json').read_text())
 verify(manifest)
 repo=Path('/home/linuxagent/xiaomi-lmi-linux-port')
 assert (repo/'userspace/camera/snapshot-bundle/prepare-chroot.py').is_file()
 assert Path('/proc/sys/fs/binfmt_misc/qemu-aarch64').is_file()
 assert shutil.disk_usage(ROOT).free>=2*1024**3
 if args.inside:
  assert args.execute;build(manifest,repo);return
 with tempfile.TemporaryDirectory(prefix='lmi-esr-preflight-') as td:patched_sources(manifest,Path(td))
 print('ESR_PREFLIGHT_PASS: current quiet sources, home8, rollback packages and patch',flush=True)
 if not args.execute:return
 assert os.geteuid()==0,'Run --execute with sudo'
 locks=[]
 for name in ('lmi-gsd-quiet-build.lock','lmi-phosh-gauge-build.lock'):
  f=open('/run/'+name,'a');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 subprocess.run(['unshare','--mount','--fork','--propagation','private',sys.executable,str(Path(__file__).resolve()),'--execute','--inside'],check=True)

if __name__=='__main__':main()
