#!/usr/bin/env python3
"""Prepare proc/devpts only inside an operator-owned private mount namespace."""
import os,stat,subprocess,sys
from pathlib import Path
assert os.getuid()==0
assert os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt'), 'Private mount namespace required'
root=Path(sys.argv[1]);assert root.is_absolute() and root.is_dir() and not root.is_symlink()
root=root.resolve(strict=True)
for relative in ['proc','dev','dev/pts']:
    p=root/relative
    assert not p.is_symlink() and p.is_dir(),p
ptmx=root/'dev/ptmx';assert not ptmx.is_symlink() and stat.S_ISCHR(ptmx.stat().st_mode)
assert (os.major(ptmx.stat().st_rdev),os.minor(ptmx.stat().st_rdev))==(5,2)
def mounted(path,kind):
    found=subprocess.run(['findmnt','-rn','-M',str(path),'-o','FSTYPE'],capture_output=True,text=True)
    if found.returncode==0:
        assert found.stdout.strip()==kind,(path,found.stdout)
        return True
    assert found.returncode==1
    return False
if not mounted(root/'proc','proc'):
    subprocess.run(['mount','-t','proc','proc',str(root/'proc')],check=True)
if not mounted(root/'dev/pts','devpts'):
    subprocess.run(['mount','-t','devpts','-o','newinstance,ptmxmode=0666,mode=0620,gid=5','devpts',str(root/'dev/pts')],check=True)
if not mounted(ptmx,'devpts'):
    subprocess.run(['mount','--bind',str(root/'dev/pts/ptmx'),str(ptmx)],check=True)
subprocess.run(['chroot',str(root),'python3','-c','import os; fd=os.open("/dev/ptmx",os.O_RDWR|os.O_NOCTTY); os.close(fd); print("CAMERA_BUILD_CHROOT_PTY_OK")'],check=True)
