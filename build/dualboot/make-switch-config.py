#!/usr/bin/env python3
"""Create a locked private controller configuration after artifact transfer."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--mobian-boot',type=Path,required=True)
p.add_argument('--android-boot',type=Path,required=True)
p.add_argument('--platform-tools',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
assert not a.output.exists(),'Refusing existing configuration'
images={}
for name,file in [('android',a.android_boot),('mobian',a.mobian_boot)]:
    with file.open('rb') as f:
        assert f.read(8)==b'ANDROID!',name
        f.seek(0);digest=hashlib.file_digest(f,'sha256').hexdigest()
    images[name]={'path':str(file.resolve()),'sha256':digest}
for tool in ('adb.exe','fastboot.exe'):assert (a.platform_tools/tool).is_file(),tool
config={'dualboot_installation_validated':False,'images':images,
 'adb':str((a.platform_tools/'adb.exe').resolve()),
 'fastboot':str((a.platform_tools/'fastboot.exe').resolve()),
 'wsl_ssh_key':'/home/linuxagent/.ssh/id_ed25519_codex_lmi'}
with a.output.open('x',encoding='utf-8') as f:json.dump(config,f,indent=2)
print('CONFIG_CREATED_LOCKED: validate installation before enabling execution')
