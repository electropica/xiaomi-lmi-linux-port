#!/usr/bin/env python3
"""Read-only runtime proof after the operator's temporary/permanent menu boot."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import manage

REMOTE = r'''
import hashlib,json,os,pathlib
phase = __PHASE__
root_stat=os.stat('/')
device=pathlib.Path(os.path.realpath('/sys/dev/block/%d:%d' % (os.major(root_stat.st_dev),os.minor(root_stat.st_dev))))
parent=device.parent if (device/'partition').exists() else device
backing=pathlib.Path('/sys/class/block')/parent.name/'loop/backing_file'
def text(p):
    try:return pathlib.Path(p).read_text().strip()
    except OSError:return None
out={'kernel':os.uname().release,'cmdline':text('/proc/cmdline'),
     'boot_id':text('/proc/sys/kernel/random/boot_id'),
     'root_block':device.name,'root_loop_backing':text(backing),
     'mobian_partition_sectors':text('/sys/class/block/sda35/size'),
     'root_mount':[s for s in pathlib.Path('/proc/mounts').read_text().splitlines() if s.split()[1]=='/']}
if phase=='installed':
    left=80654336;digest=hashlib.sha256()
    with open('/dev/disk/by-partlabel/boot','rb') as source:
        while left:
            block=source.read(min(left,1048576))
            if not block:raise RuntimeError('Short boot partition read')
            digest.update(block);left-=len(block)
    out['installed_boot_prefix_sha256']=digest.hexdigest()
print(json.dumps(out))
'''


def validate_runtime(value, installed=False):
    cmdline = value.get('cmdline') or ''
    if 'lmi_menu=outer-v1' not in cmdline.split():
        raise RuntimeError('Direct menu marker absent; may be an ordinary reboot fallback.')
    if not value.get('root_block', '').startswith('loop'):
        raise RuntimeError('Unexpected root block device.')
    backing = value.get('root_loop_backing') or ''
    if backing not in ('/dev/sda35', '/dev/block/sda35'):
        raise RuntimeError('Dedicated Mobian root backing not confirmed: ' + backing)
    if int(value.get('mobian_partition_sectors') or '0') * 512 != 17179869184:
        raise RuntimeError('Dedicated Mobian partition size mismatch.')
    if installed and value.get('installed_boot_prefix_sha256') != manage.MENU_SHA:
        raise RuntimeError('Installed boot readback does not match the pinned menu.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['temporary', 'installed'], default='temporary')
    parser.add_argument('--launch-record', type=Path,
                        default=Path.home() / 'Documents/ChatGPT/Mobian/work/outer-menu-launch-20261022-private.json')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    manage.host_preflight(Path.home() / 'Downloads')
    if not args.execute:
        print('PLAN_ONLY: read cmdline, root backing, partition size; installed phase also reads boot prefix. No phone contact.')
        return
    launch_path = args.launch_record
    if args.phase == 'temporary':
        launch = json.loads(launch_path.read_text())
        if launch.get('sha256') != manage.MENU_SHA or launch.get('no_flash') is not True:
            raise RuntimeError('Matching temporary launch receipt missing.')
    else:
        launch = None
        manage.require_qualified(manage.load_receipt())
    script = REMOTE.replace('__PHASE__', repr(args.phase))
    ssh = ['wsl.exe', '-d', 'Ubuntu', '-u', 'linuxagent', '--', 'ssh',
           '-i', '/home/linuxagent/.ssh/id_ed25519_codex_lmi',
           '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
           'root@172.16.42.1', 'python3', '-']
    result = subprocess.run(ssh, input=script, text=True, capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError('Read-only SSH runtime check failed; no retry or device change.')
    value = json.loads(result.stdout)
    manage.RECORDS.mkdir(parents=True, exist_ok=True)
    evidence = manage.RECORDS / ('runtime-' + args.phase + '.json')
    evidence.write_text(json.dumps(value, indent=2), encoding='utf-8')
    validate_runtime(value, installed=args.phase == 'installed')
    receipt = manage.load_receipt()
    receipt['mobian_proof'] = {
        'menu_sha256': manage.MENU_SHA, 'direct_marker': True,
        'dedicated_root_confirmed': True, 'utc': manage.stamp(),
        'raw_evidence_file': evidence.name,
        'raw_evidence_sha256': hashlib.sha256(evidence.read_bytes()).hexdigest()}
    if launch is not None:
        receipt['temporary_launch'] = launch
    else:
        receipt['installed_readback_verified'] = True
        receipt['installed_runtime_utc'] = manage.stamp()
    manage.save_receipt(receipt)
    print('DIRECT_MOBIAN_ROOT_CONFIRMED' if launch is not None else 'PERMANENT_MENU_BOOT_AND_DIRECT_ROOT_READBACK_CONFIRMED')
    print('Interface/menu outcomes still require actual operator confirmation.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print('STOP:', str(exc), file=sys.stderr)
        raise SystemExit(1)
