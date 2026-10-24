#!/usr/bin/python3
"""Operator-run Phoc thumbnail backport. Default validates only; no phone I/O."""
from pathlib import Path
import argparse,fcntl,hashlib,io,json,os,subprocess,tarfile

ROOT=Path('/home/linuxagent/phosh-gauge-wake-build/rootfs')
TREE=ROOT/'build/phoc-lmi-shell-dnd1'
BEFORE='a29cacf8cdb1000a39f8d3768b4e482fe4ff00575f7b0d82822e628afb27fa58'
AFTER='01f63468e5da660bad34874fb626913ca2ea482c2a4672899e814301c699198d'
CURSOR='cf6a54c4cd77fe74e69e350f9b0836810917a1f020531004505c995b8f90b892'
OLD='0.46.0-1+lmishelldnd1'
NEW=OLD+'+thumblinear1'
ROLLBACK='e862d58b20aa274b01184e89e0b3d25048de951fb70f161235854fe4fe970ac6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate():
 assert sha(TREE/'src/cursor.c')==CURSOR,'Preserve qualified shell DnD'
 h=sha(TREE/'src/render.c');assert h in (BEFORE,AFTER)
 v=(TREE/'debian/changelog').read_text().splitlines()[0]
 assert v.startswith('phoc ('+(OLD if h==BEFORE else NEW)+') '),'Source/changelog mismatch'
 rollback=ROOT/'build'/('phoc_'+OLD+'_arm64.deb')
 assert sha(rollback)==ROLLBACK
 return h,rollback
def payload(p):
 raw=subprocess.check_output(['dpkg-deb','--fsys-tarfile',str(p)])
 with tarfile.open(fileobj=io.BytesIO(raw)) as t:
  entries=sorted((x.name,x.type.decode(),x.linkname) for x in t.getmembers())
 return entries

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--inside',action='store_true',help=argparse.SUPPRESS);a=ap.parse_args()
 h,rollback=validate()
 s=(TREE/'src/render.c').read_text()
 if h==BEFORE:
  old='wlr_drm_format_set_add (&fmt_set, DRM_FORMAT_ARGB8888, DRM_FORMAT_MOD_INVALID);'
  assert s.count(old)==1
  s=s.replace(old,old.replace('MOD_INVALID','MOD_LINEAR'))
 assert hashlib.sha256(s.encode()).hexdigest()==AFTER
 print('THUMBNAIL_LINEAR_PREFLIGHT_PASS',flush=True)
 if not a.execute:return
 assert os.geteuid()==0,'Use sudo for --execute'
 if not a.inside:
  lock=open('/run/lmi-phosh-gauge-build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  subprocess.run(['unshare','--mount','--fork','--propagation','private','python3',str(Path(__file__).resolve()),'--execute','--inside'],check=True);return
 assert os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt')
 repo=Path('/home/linuxagent/xiaomi-lmi-linux-port')
 subprocess.run(['python3',str(repo/'userspace/camera/snapshot-bundle/prepare-chroot.py'),str(ROOT)],check=True)
 subprocess.run(['mount','-t','tmpfs','-o','mode=1777,nosuid,nodev,size=256m','tmpfs',str(ROOT/'dev/shm')],check=True)
 assert subprocess.check_output(['chroot',str(ROOT),'dpkg','--print-architecture'],text=True).strip()=='arm64'
 if h==BEFORE:
  (TREE/'src/render.c').write_text(s)
  subprocess.run(['chroot',str(ROOT),'/bin/bash','-c','cd /build/phoc-lmi-shell-dnd1 && DEBFULLNAME="Local lmi" DEBEMAIL=local@example.invalid dch --newversion "$1" --distribution UNRELEASED "Backport linear thumbnail buffers; preserve shell drag and drop."','bash',NEW],check=True)
 validate()
 subprocess.run(['chroot',str(ROOT),'chown','builder:builder','/build/phoc-lmi-shell-dnd1/src/render.c','/build/phoc-lmi-shell-dnd1/debian/changelog'],check=True)
 stamp=TREE/'debian/debhelper-build-stamp';assert not stamp.is_symlink();stamp.unlink(missing_ok=True)
 subprocess.run(['chroot',str(ROOT),'/bin/bash','-c','set -euo pipefail; export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin; cd /build/phoc-lmi-shell-dnd1; runuser -u builder -- env DEBIAN_FRONTEND=noninteractive DEB_BUILD_OPTIONS=parallel=2 dpkg-buildpackage -b -nc -us -uc -j2'],check=True)
 validate()
 p=ROOT/'build'/('phoc_'+NEW+'_arm64.deb')
 for field,value in [('Package','phoc'),('Version',NEW),('Architecture','arm64')]:assert subprocess.check_output(['dpkg-deb','-f',str(p),field],text=True).strip()==value
 assert payload(p)==payload(rollback),'Unexpected package file/type/link changes'
 result={'path':str(p),'sha256':sha(p),'version':NEW,'source_after':AFTER,'cursor_preserved':CURSOR,'rollback_path':str(rollback),'rollback_sha256':ROLLBACK,'upstream_commit':'a19515c8ed4abea0e9a5dab324466a88370a3a50','phone_contact':False}
 (ROOT/'build/lmi-thumbnail-linear-build-result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2));print('PHOC_THUMBNAIL_LINEAR_PACKAGE_BUILT\nNo phone installation, kernel or image build performed.')
if __name__=='__main__':main()
