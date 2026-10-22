#!/bin/bash
# Runs only inside the dedicated Debian bookworm rootfs. No phone tools.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1
cd /source
if [[ -d edk2-msm/.git ]]; then
  python3 /recipe/chainload/apply-chainload.py /source/edk2-msm --manifest /output/chainload-source-manifest.json --restore-only
fi
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
assert not git('-C','edk2-msm/Common/edk2','diff','--name-only'), 'Unexpected EDK2 core edits after restoration'
PY
python3 /recipe/apply-menu.py /source/edk2-msm > /output/patch-manifest.json
if [[ ${LMI_MENU_LINEAGE:-0} == 1 ]]; then
  dual_args=();if [[ ${LMI_MENU_DUAL:-0} == 1 ]]; then dual_args=(--dual);fi
  python3 /recipe/chainload/make-bundle.py --inputs /inputs --output /output/lmi-ram-assets.bin "${dual_args[@]}"
  python3 /recipe/chainload/apply-chainload.py /source/edk2-msm --manifest /output/chainload-source-manifest.json "${dual_args[@]}"
fi
cd /source/edk2-msm
# No --boot, --installer-zip, --clean or automatic device operations.
bash build.sh --device lmi --toolchain CLANG38 --release RELEASE --outputdir /output
if [[ ${LMI_MENU_LINEAGE:-0} == 1 ]]; then
  python3 - <<'PY'
from pathlib import Path
import importlib.util,hashlib,json,os
p=Path('/recipe/chainload/match-android-os-version.py')
s=importlib.util.spec_from_file_location('os_context',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
raw=Path('/output/boot-lmi.img').read_bytes()
data,record=m.adjust(raw,Path('/inputs/android.img').read_bytes(),hashlib.sha256(raw).hexdigest())
Path('/output/boot-lmi-dual-test.img' if os.environ.get('LMI_MENU_DUAL')=='1' else '/output/boot-lmi-lineage-test.img').write_bytes(data)
Path('/output/boot-os-version-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
PY
fi
python3 - <<'PY'
from pathlib import Path
import hashlib,json,struct,subprocess,os
lineage=os.environ.get('LMI_MENU_LINEAGE')=='1'
dual=os.environ.get('LMI_MENU_DUAL')=='1'
p=Path('/output/boot-lmi-dual-test.img' if dual else '/output/boot-lmi-lineage-test.img' if lineage else '/output/boot-lmi.img');raw=p.read_bytes()
assert raw[:8]==b'ANDROID!' and 0<len(raw)<=134217728
assert struct.unpack_from('<I',raw,40)[0]==1
result={'phase':'experimental-lineage-ram-handoff' if lineage else 'temporary-menu-smoke-not-dualboot','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'no_phone_contact':True,'compiler':subprocess.check_output(['clang','--version'],text=True).splitlines()[0],'python':subprocess.check_output(['python3','--version'],text=True).strip()}
if lineage:
 result['candidate_variant']='android-only-original-memory-map-32MiB-FD-prepi-ffs3-fstab1-osversion1'
 context=json.loads(Path('/output/boot-os-version-manifest.json').read_text())
 assert context['output_sha256']==result['sha256'] and context['new']['packed']==struct.unpack_from('<I',raw,44)[0]
 result['boot_header_os_version']=context['new']
 result['boot_header_matches_pinned_android']=True
if dual:
 result['phase']='experimental-dual-direct-ram-handoff'
 result['candidate_variant']='dual-direct-64MiB-FD-prepi-ffs3-fstab1-osversion1-consolefit1-marker2'
 result['hardware_validated']=False
Path('/output/dual-artifact-manifest.json' if dual else '/output/lineage-artifact-manifest.json' if lineage else '/output/artifact-manifest.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
PY
if [[ ${LMI_MENU_DUAL:-0} == 1 ]]; then
  echo DUAL_DIRECT_RAM_HANDOFF_BUILD_COMPLETE_NOT_FOR_FLASHING
elif [[ ${LMI_MENU_LINEAGE:-0} == 1 ]]; then
  echo LINEAGE_RAM_HANDOFF_BUILD_COMPLETE_NOT_FOR_FLASHING
else
  echo MENU_SMOKE_BUILD_COMPLETE_NOT_FOR_FLASHING
fi
