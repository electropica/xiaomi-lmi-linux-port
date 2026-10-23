#!/usr/bin/env python3
"""Build only a diagnostic Image using the qualified source/config/toolchain.

Default: bounded offline preflight. --execute must be run by the operator.
No boot repack, flash, mounts, package installation or deletion.
"""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
import stat
import subprocess
import tarfile
import tempfile

REV='a5b3099017ae581aae8bf597b2f9c8c765026af1'
ARCHIVE_SHA='9e3bde7cde952682225a0375444bd3c1d33d99ddb80fa17b6a3abf3957f36c94'
CONFIG_SHA='c6da6e71cc7418f36997325ff5d72693d9861945cc4999b6be9661a150451e78'
PATCHES=[
 ('kernel/patches/0001-mobian-add-boot-safe-QCA6390-UART-support-and-restor.patch','d193cfbaad83811703f5db5990eaa52358e1828af581e09c702f4efa10aec782'),
 ('kernel/patches/0002-esoc-preserve-crash-state-on-late-run-notification.patch','c94fe70ae385e1f74fb56566b9743d4b5df23b6fc42aeabecbdbee9c3a2004aa'),
 ('kernel/diagnostics/audio/patches/0001-lmi-wcd938x-rx-soundwire-diagnostic.patch','2d5c2188356b0708ebf88b6a2694b216b4ccb62e6e8ab74124a53ea96d3b6e79'),
 ('kernel/patches/audio/0001-lmi-wcd938x-reset-gpio-mux.patch','1d1859556bb05c207b70225ecccc922c9338eff485f729012abc41ba75fbfef7'),
 ('kernel/patches/diagnostics/lmi-dsi-powerdown-notifier-unvalidated.patch','2f6aa840ac77e3c46e5399b9bc3877471382ad6ae156c92980e83a20fff3b1c0'),
 ('kernel/patches/diagnostics/lmi-rpmh-vote-observer-unvalidated.patch','ea19e7e6aa5d4d8915e1fbab5ce00addf3a49df02c6b7cc104c395b2f49581ab'),
 ('kernel/patches/diagnostics/lmi-fg-profile-phandle-unvalidated.patch','79663689d83c846b04b44a9eb8ebcf87bacd17104b208574012aaee6741813b0')]

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def require_hash(p,expected):
 if not p.is_file() or digest(p)!=expected:raise SystemExit('Missing or mismatched input: '+str(p))

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--execute',action='store_true')
 parser.add_argument('--jobs',type=int,default=4)
 parser.add_argument('--config',type=Path,help='Explicit retained config; exact qualified hash is enforced')
 args=parser.parse_args()
 if not 1<=args.jobs<=16:raise SystemExit('jobs must be between1 and16')
 repo=Path(__file__).resolve().parents[3]
 # Set explicitly for private recipe checks outside the repository.
 if os.environ.get('LMI_FG_REPO'):repo=Path(os.environ['LMI_FG_REPO']).resolve()
 home=Path('/home/linuxagent')
 archive=home/f'dv43-pmbootstrap-work/cache_distfiles/linux-xiaomi-lmi-{REV}.tar.gz'
 chroot=home/'dv43-pmbootstrap-work/chroot_native'
 config=args.config or repo/'kernel/diagnostics/audio/state-power-rpmh-votes-reviewed/power-debugfs.config'
 require_hash(archive,ARCHIVE_SHA);require_hash(config,CONFIG_SHA)
 for rel,sha in PATCHES:require_hash(repo/rel,sha)
 for tool in ('clang','llvm-ar','llvm-nm','llvm-objcopy','llvm-objdump'):
  if not (chroot/'usr/lib/llvm22/bin'/tool).is_file():raise SystemExit('Missing native tool: '+tool)
 if not (chroot/'usr/bin/gcc').is_file():raise SystemExit('Missing native host gcc')
 if not (chroot/'usr/bin/ld.lld').is_file():raise SystemExit('Missing native linker')
 prefix='android_kernel_xiaomi_sm8250-'+REV+'/'
 targets=set()
 for rel,_ in PATCHES:
  for line in (repo/rel).read_text().splitlines():
   if line.startswith('--- a/'):targets.add(line[6:])
 with tarfile.open(archive,'r:gz') as tf,tempfile.TemporaryDirectory(prefix='lmi-fg-patch-preflight-') as tmp:
  staging=Path(tmp)
  for rel in targets:
   if rel.startswith('/') or '..' in Path(rel).parts:raise SystemExit('Unsafe patch path')
   member=tf.getmember(prefix+rel)
   if not member.isfile() or member.size>8*1024*1024:raise SystemExit('Unexpected source member')
   p=staging/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tf.extractfile(member).read())
  for rel,_ in PATCHES:
   subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(repo/rel)],cwd=staging,check=True,stdout=subprocess.DEVNULL)
 print('PREFLIGHT_PASS: pinned archive/config, seven-patch sequence and native tool files',flush=True)
 if not args.execute:return
 if os.geteuid()!=0:raise SystemExit('Run --execute with sudo; no build started')
 version=subprocess.check_output(['chroot',str(chroot),'/usr/lib/llvm22/bin/clang','--version'],text=True)
 if 'Alpine clang version 22.1.8' not in version:raise SystemExit('Native Clang version mismatch')
 lld=subprocess.check_output(['chroot',str(chroot),'/usr/bin/ld.lld','--version'],text=True)
 if 'LLD 22.1.8' not in lld:raise SystemExit('Native LLD version mismatch')
 if not stat.S_ISCHR((chroot/'dev/null').stat().st_mode):raise SystemExit('Native /dev/null is unavailable')
 if shutil.disk_usage(chroot/'home/pmos').free<12*1024**3:raise SystemExit('At least12GiB free is required before extracting/building')
 stage=Path(tempfile.mkdtemp(prefix='lmi-fg-lookup-',dir=chroot/'home/pmos'))
 (stage/'BUILD_STATUS').write_text('INCOMPLETE: preparation or build in progress\n')
 print('BUILD_STATE='+str(stage),flush=True)
 src=stage/'src';src.mkdir();out=stage/'out';out.mkdir();(out/'tmp').mkdir()
 guest='/'+str(stage.relative_to(chroot));guestsrc=guest+'/src';guestout=guest+'/out'
 with tarfile.open(archive,'r:gz') as tf:
  # Extract only the pinned archive under its expected single root.
  for member in tf.getmembers():
   if member.name.rstrip('/')!=prefix.rstrip('/') and not member.name.startswith(prefix):raise SystemExit('Unexpected archive root')
  tf.extractall(stage,filter='data')
 # Preserve the extracted tree in place; no second full source copy.
 extracted=stage/prefix.rstrip('/')
 src.rmdir();extracted.rename(src)
 for rel,_ in PATCHES:subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(repo/rel)],cwd=src,check=True)
 (src/'.scmversion').write_text('-ga5b3099017ae-dirty\n')
 (out/'.config').write_bytes(config.read_bytes())
 env=['chroot',str(chroot),'/usr/bin/env','PATH=/usr/lib/llvm22/bin:/usr/bin:/bin','LC_ALL=C','TMPDIR='+guestout+'/tmp']
 for flags in ('-m64','-static -m64'):
  subprocess.run(env+['/bin/sh','-c','cd "$1"; scripts/cc-can-link.sh clang '+flags,'sh',guestsrc],check=True)
 make=env+['make','-C',guestsrc,'O='+guestout,'ARCH=arm64','CROSS_COMPILE=aarch64-alpine-linux-musl-','LLVM=1','LLVM_IAS=1','HOSTCC=/usr/bin/gcc','HOSTCXX=/usr/bin/g++']
 subprocess.run(make+['olddefconfig'],check=True)
 require_hash(out/'.config',CONFIG_SHA)
 subprocess.run(make+['KBUILD_BUILD_VERSION=3','KBUILD_BUILD_USER=lmi-audio-diagnostic','KBUILD_BUILD_HOST=diagnostic','Image','-j'+str(args.jobs)],check=True)
 image=out/'arch/arm64/boot/Image'
 if not image.is_file() or image.stat().st_size==0:raise SystemExit('Missing Image')
 result={'image':str(image),'image_sha256':digest(image),'config_sha256':digest(out/'.config'),'archive_sha256':ARCHIVE_SHA,'patches':PATCHES,'kernel_only':True,'boot_image_repacked':False,'flashed':False}
 (stage/'BUILD_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
 (stage/'BUILD_STATUS').write_text('COMPLETE: kernel-only artifact, not for flashing\n')
 print('FG_PROFILE_KERNEL_BUILD_COMPLETE_NOT_FOR_FLASHING')
 print('IMAGE='+str(image));print('SHA256='+result['image_sha256']);print('RESULT='+str(stage/'BUILD_RESULT.json'))

if __name__=='__main__':main()
