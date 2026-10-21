#!/bin/bash
# Runs only inside the dedicated Debian bookworm rootfs. No phone tools.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1
cd /source
python3 - <<'PY'
import json,subprocess
from pathlib import Path
c=json.loads(Path('/recipe/sources.lock.json').read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
if not Path('edk2-msm/.git').exists():
 subprocess.run(['git','init','edk2-msm'],check=True)
 subprocess.run(['git','-C','edk2-msm','remote','add','origin',c['repository']],check=True)
if not (Path('edk2-msm')/'.lmi-source-ready').exists():
 subprocess.run(['git','-C','edk2-msm','fetch','--depth','1','origin',c['revision']],check=True)
 subprocess.run(['git','-C','edk2-msm','checkout','--detach',c['revision']],check=True)
 subprocess.run(['git','-C','edk2-msm','submodule','update','--init','--recursive','--depth','1'],check=True)
 (Path('edk2-msm')/'.lmi-source-ready').touch()
assert git('-C','edk2-msm','rev-parse','HEAD')==c['revision']
for path,sha in c['submodules'].items():
 assert git('-C','edk2-msm/'+path,'rev-parse','HEAD')==sha,path
assert not git('-C','edk2-msm','diff','--name-only','--ignore-submodules=dirty'), 'Unexpected superproject changes'
# Reject pre-existing submodule edits except the intentional menu patches.
changed=git('-C','edk2-msm/GPLDrivers/Library/SimpleInit','diff','--name-only').splitlines()
assert set(changed)<= {'src/main/uefimain.c','src/confd/uefi.c','src/gui/interface/core/bootmenu.c'},changed
PY
python3 /recipe/apply-menu.py /source/edk2-msm > /output/patch-manifest.json
cd /source/edk2-msm
# No --boot, --installer-zip, --clean or automatic device operations.
bash build.sh --device lmi --toolchain CLANG38 --release RELEASE --outputdir /output
python3 - <<'PY'
from pathlib import Path
import hashlib,json,struct,subprocess
p=Path('/output/boot-lmi.img');raw=p.read_bytes()
assert raw[:8]==b'ANDROID!' and 0<len(raw)<=134217728
assert struct.unpack_from('<I',raw,40)[0]==1
result={'phase':'temporary-menu-smoke-not-dualboot','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'no_phone_contact':True,'compiler':subprocess.check_output(['clang','--version'],text=True).splitlines()[0],'python':subprocess.check_output(['python3','--version'],text=True).strip()}
Path('/output/artifact-manifest.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
PY
echo MENU_SMOKE_BUILD_COMPLETE_NOT_FOR_FLASHING
