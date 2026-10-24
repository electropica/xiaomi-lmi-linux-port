#!/usr/bin/env python3
"""Operator-only incremental package build. Default preflight, no phone access."""
from pathlib import Path
import argparse,fcntl,hashlib,io,json,os,shutil,subprocess,sys,tarfile,tempfile

ROOT=Path('/home/linuxagent/phosh-gauge-wake-build/rootfs')
TASK=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def verify(manifest):
 assert sha(TASK/'drawer-interface.patch')==manifest['patch_sha256']
 for spec in manifest['sources']:
  tree=ROOT/'build'/spec['tree'];assert tree.is_dir() and not tree.is_symlink()
  digest=sha(tree/spec['file']);assert digest in (spec['before'],spec['after'])
  head=(tree/'debian/changelog').read_text().splitlines()[0]
  expected=spec['new'] if digest==spec['after'] else spec['old']
  assert head==spec['package']+' ('+expected+') UNRELEASED; urgency=medium','Source/changelog state mismatch'
  for pkg,arch in ((spec['package'],'arm64'),(spec['package']+'-common','all')):
   rollback=ROOT/'build'/f'{pkg}_{spec.get("rollback", spec["old"])}_{arch}.deb'
   assert rollback.is_file(), 'Rollback package missing'
   assert subprocess.check_output(['dpkg-deb','-f',str(rollback),'Version'],text=True).strip()==spec.get('rollback', spec['old'])
   assert subprocess.check_output(['dpkg-deb','-f',str(rollback),'Architecture'],text=True).strip()==arch
 for rel,digest in manifest['preserve_home8'].items():
  assert not Path(rel).is_absolute() and '..' not in Path(rel).parts
  assert sha(ROOT/'build/phosh-0.46.0'/rel)==digest,rel
 for rel,digest in manifest.get('preserve_extra',{}).items():
  assert not Path(rel).is_absolute() and '..' not in Path(rel).parts
  assert sha(ROOT/'build'/rel)==digest,rel

def patched_sources(manifest,tmp):
 for spec in manifest['sources']:
  target=tmp/spec['file'];target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(ROOT/'build'/spec['tree']/spec['file'],target)
 # All inputs must be either entirely old or entirely new for patch staging.
 states=[sha(tmp/s['file'])==s['after'] for s in manifest['sources']]
 assert all(states) or not any(states),'Partial source preparation; inspect before retry'
 if all(states):
  # Reconstruct the pinned baseline before replaying even on an incremental rerun.
  subprocess.run(['patch','--batch','--fuzz=0','-R','-p1','-i',str(TASK/'drawer-interface.patch')],cwd=tmp,check=True)
 for spec in manifest['sources']:assert sha(tmp/spec['file'])==spec['before']
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(TASK/'drawer-interface.patch')],cwd=tmp,check=True)
 for spec in manifest['sources']:assert sha(tmp/spec['file'])==spec['after']

def payload_identity(package,binary=None):
 raw=subprocess.check_output(['dpkg-deb','--fsys-tarfile',str(package)])
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:
  members=tf.getmembers()
  entries=sorted((m.name,m.type.decode('ascii'),m.linkname) for m in members)
  data=None
  if binary:
   match=[m for m in members if m.name.lstrip('./')==binary]
   assert len(match)==1 and match[0].isfile(),'Expected package executable missing'
   data=tf.extractfile(match[0]).read()
 return entries,data

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
    subprocess.run(['chroot',str(ROOT),'/usr/bin/env','DEBIAN_FRONTEND=noninteractive','DEBFULLNAME=Local lmi','DEBEMAIL=local@example.invalid','/bin/sh','-c','cd "$1" && dch --newversion "$2" --distribution UNRELEASED "Place running previews inside the applications page; keep home drag geometry independent of preview visibility."','sh',guest,spec['new']],check=True)
   assert (tree/'debian/changelog').read_text().splitlines()[0]==spec['package']+' ('+spec['new']+') UNRELEASED; urgency=medium'
   subprocess.run(['chroot',str(ROOT),'chown','builder:builder',guest+'/'+spec['file'],guest+'/debian/changelog'],check=True)
   stamp=tree/'debian/debhelper-build-stamp';assert not stamp.is_symlink()
   if stamp.exists():assert stamp.is_file();stamp.unlink()
  verify(manifest)
  for spec in {s['tree']:s for s in manifest['sources']}.values():
   subprocess.run(['chroot',str(ROOT),'/bin/bash','-c',
    'set -euo pipefail; export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin; cd "$1"; runuser -u builder -- env DEBIAN_FRONTEND=noninteractive DEB_BUILD_OPTIONS=parallel=2 dpkg-buildpackage -b -nc -us -uc -j2',
    'bash','/build/'+spec['tree']],check=True)
 verify(manifest)
 packages=[]
 for spec in {s['tree']:s for s in manifest['sources']}.values():
  for pkg,arch in ((spec['package'],'arm64'),(spec['package']+'-common','all')):
   p=ROOT/'build'/f'{pkg}_{spec["new"]}_{arch}.deb';assert p.is_file()
   actual=subprocess.check_output(['dpkg-deb','-f',str(p),'Version'],text=True).strip()
   assert actual==spec['new']
   assert subprocess.check_output(['dpkg-deb','-f',str(p),'Architecture'],text=True).strip()==arch
   old=ROOT/'build'/f'{pkg}_{spec.get("rollback", spec["old"])}_{arch}.deb'
   binary={'phosh':'usr/libexec/phosh','gnome-settings-daemon':'usr/libexec/gsd-power'}.get(pkg)
   entries,newbytes=payload_identity(p,binary);oldentries,oldbytes=payload_identity(old,binary)
   assert entries==oldentries,'Package file/type/link list changed: '+pkg
   record={'path':str(p),'sha256':sha(p),'version':actual,'architecture':arch,
           'rollback_sha256':sha(old),'file_list_unchanged':True}
   if binary:
    assert newbytes!=oldbytes and b'445 esr-delta' in newbytes,'Missing compiled ESR policy'
    record.update(binary_path=binary,binary_sha256=hashlib.sha256(newbytes).hexdigest(),
                  rollback_binary_sha256=hashlib.sha256(oldbytes).hexdigest())
   packages.append(record)
 (ROOT/'build/lmi-drawer-interface4-build-result.json').write_text(json.dumps({'packages':packages,'identity':manifest,'phone_contact':False},indent=2)+'\n')
 print(json.dumps(packages,indent=2));print('DRAWER_INTERFACE_PACKAGES_BUILT\nNo phone installation, kernel or image build performed.')

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
 print('DRAWER_INTERFACE_PREFLIGHT_PASS: current quiet sources, home8, rollback packages and patch',flush=True)
 if not args.execute:return
 assert os.geteuid()==0,'Run --execute with sudo'
 locks=[]
 for name in ('lmi-gsd-quiet-build.lock','lmi-phosh-gauge-build.lock'):
  f=open('/run/'+name,'a')
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise SystemExit('Another package build holds '+name)
  locks.append(f)
 subprocess.run(['unshare','--mount','--fork','--propagation','private',sys.executable,str(Path(__file__).resolve()),'--execute','--inside'],check=True)

if __name__=='__main__':main()
