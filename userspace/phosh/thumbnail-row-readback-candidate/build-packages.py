#!/usr/bin/python3
"""Operator-run thumbnail-only row-readback candidate; default validates only."""
from pathlib import Path
import argparse,fcntl,hashlib,io,json,os,subprocess,tarfile,tempfile
ROOT=Path('/home/linuxagent/phosh-gauge-wake-build/rootfs')
TREE=ROOT/'build/phoc-lmi-shell-dnd1'
HERE=Path(__file__).resolve().parent
BEFORE='01f63468e5da660bad34874fb626913ca2ea482c2a4672899e814301c699198d'
AFTER='9910e7165e1cb94b5be2986efef7d85b3967f414ff9095f59221a8a856264b0c'
CURSOR='cf6a54c4cd77fe74e69e350f9b0836810917a1f020531004505c995b8f90b892'
OLD='0.46.0-1+lmishelldnd1+thumblinear1'
NEW=OLD+'+thumbrows1'
ROLLBACK='cfb248dd31a256e1a46c7a17742f479424ac01d9d5b16943ad4fb8bc1614fccf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate():
 assert sha(TREE/'src/cursor.c')==CURSOR,'Preserve qualified shell DnD'
 h=sha(TREE/'src/render.c');assert h in (BEFORE,AFTER),'Unexpected renderer source'
 assert (TREE/'debian/changelog').read_text().splitlines()[0].startswith('phoc ('+(OLD if h==BEFORE else NEW)+') '),'Source/changelog mismatch'
 p=ROOT/'build'/('phoc_'+OLD+'_arm64.deb');assert sha(p)==ROLLBACK
 return h,p

def prepare(h):
 if h==AFTER:return (TREE/'src/render.c').read_text()
 with tempfile.TemporaryDirectory(prefix='lmi-thumb-rows-check-') as tmp:
  p=Path(tmp);(p/'src').mkdir();(p/'src/render.c').write_bytes((TREE/'src/render.c').read_bytes())
  subprocess.run(['patch','--batch','--fuzz=0','-p1'],cwd=p,input=(HERE/'row-readback.patch').read_bytes(),check=True,capture_output=True)
  s=(p/'src/render.c').read_text();assert hashlib.sha256(s.encode()).hexdigest()==AFTER
 return s

def payload(p):
 raw=subprocess.check_output(['dpkg-deb','--fsys-tarfile',str(p)])
 with tarfile.open(fileobj=io.BytesIO(raw)) as t:return sorted((x.name,x.type.decode(),x.linkname) for x in t.getmembers())
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--inside',action='store_true',help=argparse.SUPPRESS);a=ap.parse_args()
 h,rollback=validate();s=prepare(h)
 print('THUMBNAIL_ROW_PREFLIGHT_PASS',flush=True)
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
  subprocess.run(['chroot',str(ROOT),'/bin/bash','-c','cd /build/phoc-lmi-shell-dnd1 && DEBFULLNAME="Local lmi" DEBEMAIL=local@example.invalid dch --newversion "$1" --distribution UNRELEASED "Use row readback for GLES ARGB thumbnails; preserve shell drag and drop."','bash',NEW],check=True)
 validate()
 subprocess.run(['chroot',str(ROOT),'chown','builder:builder','/build/phoc-lmi-shell-dnd1/src/render.c','/build/phoc-lmi-shell-dnd1/debian/changelog'],check=True)
 stamp=TREE/'debian/debhelper-build-stamp';assert not stamp.is_symlink();stamp.unlink(missing_ok=True)
 subprocess.run(['chroot',str(ROOT),'/bin/bash','-c','set -euo pipefail; export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin; cd /build/phoc-lmi-shell-dnd1; runuser -u builder -- env DEBIAN_FRONTEND=noninteractive DEB_BUILD_OPTIONS=parallel=2 dpkg-buildpackage -b -nc -us -uc -j2'],check=True)
 validate();p=ROOT/'build'/('phoc_'+NEW+'_arm64.deb')
 for field,value in [('Package','phoc'),('Version',NEW),('Architecture','arm64')]:assert subprocess.check_output(['dpkg-deb','-f',str(p),field],text=True).strip()==value
 assert payload(p)==payload(rollback),'Unexpected package file/type/link changes'
 result={'path':str(p),'sha256':sha(p),'version':NEW,'source_after':AFTER,'cursor_preserved':CURSOR,'rollback_path':str(rollback),'rollback_sha256':ROLLBACK,'phone_contact':False,'hardware_fix_verified':False}
 (ROOT/'build/lmi-thumbnail-row-build-result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2));print('PHOC_THUMBNAIL_ROW_PACKAGE_BUILT\nNo phone installation, kernel or image build performed.')
if __name__=='__main__':main()
