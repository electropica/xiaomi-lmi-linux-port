"""Offline source/container tests; no firmware compilation, device or network."""
from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import tempfile
import subprocess

HERE=Path(__file__).resolve().parent
INPUT=Path('/home/linuxagent/lmi-boot-menu-build/inputs')
WORK=Path('/home/linuxagent/lmi-boot-menu-build/output')

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value

board=module('board',HERE/'board-overlay.py')
extract=module('extract',HERE.parent/'extract-payloads.py')
make=module('make',HERE/'make-outer.py')
pack=module('pack',HERE/'pack-outer.py')
raw=(INPUT/'mobian.img').read_bytes()
parts=extract.extract(raw)
dtbo=(INPUT/'android-dtbo.img').read_bytes()
merged,info=board.apply_board(parts['dtb'],dtbo)
assert hashlib.sha256(merged).hexdigest()=='340b7130748c722fd6a9ef8d9a0bbc79373baaf9fa22e5ccbc78610722fa43eb'
for bad_base,bad_dtbo in [(parts['dtb']+b'x',dtbo),(parts['dtb'],dtbo[:-1]),
                          (parts['dtb'],b'x'+dtbo[1:])]:
    try:board.apply_board(bad_base,bad_dtbo)
    except ValueError:pass
    else:raise AssertionError('Unknown base/overlay accepted')
with tempfile.TemporaryDirectory(prefix='lmi-board7-fixture-') as directory:
    path=Path(directory)/'merged.dtb';path.write_bytes(merged)
    for node in ['/soc/display_gpio_regulator_vci','/soc/gpio_keys/vol_up',
                 '/soc/xiaomi_touch']:
        subprocess.run(['fdtget','-p',str(path),node],check=True,capture_output=True)
data,record=make.make(HERE.parent,INPUT)
assert record['board_overlay']==info
assert record['components']['mobian/dtb']['sha256']==info['merged_dtb_sha256']
for name in ['kernel','initrd']:
    assert record['components']['mobian/'+name]['sha256']==hashlib.sha256(parts[name]).hexdigest()
command=parts['cmdline.txt'][:-1]+b'\0'
assert record['components']['mobian/cmdline']['sha256']==hashlib.sha256(command).hexdigest()
identity=record['components']['mobian/identity']
assert data[identity['offset']:identity['offset']+identity['bytes']]==b'lmi-outer-v2\0'
assert ' lmi_menu=outer-v2' in (HERE/'outer-loader.h').read_text()
old=(Path('/home/linuxagent/lmi-boot-menu-build/output')/'boot-lmi-lineage-resetguard1.img').read_bytes()
container=pack.pack(old,data)
page=struct.unpack_from('<I',old,36)[0]
size=struct.unpack_from('<I',old,8)[0]
assert container[page:page+size]==old[page:page+size]
result={'status':'PASS','firmware_compiled':False,'phone_contact':False,
        'board_overlay':info,'bundle_bytes':len(data),
        'bundle_sha256':hashlib.sha256(data).hexdigest(),
        'test_container_bytes':len(container),
        'test_container_is_new_firmware':False,
        'kernel_initrd_cmdline_unchanged':True,
        'unknown_or_corrupt_inputs_rejected':True,
        'expected_display_keys_touch_nodes_present':True,
        'outer_assets':record}
(WORK/'board7-host-check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('BOARD7_REAL_INPUT_OVERLAY_REJECTION_COMPONENT_PRESERVATION_AND_CONTAINER_PASS')
print('Bundle bytes',len(data),'test container bytes',len(container))
