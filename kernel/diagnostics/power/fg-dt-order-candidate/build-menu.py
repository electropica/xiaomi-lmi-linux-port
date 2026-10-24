#!/usr/bin/env python3
"""Prepare/check an isolated diagnostic menu recipe; operator --build compiles.
Never flashes, contacts a phone, replaces the qualified menu or starts a test.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,os,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
BASE=Path('/home/linuxagent/xiaomi-lmi-linux-port/build/boot-menu/external-mobian')
OUTPUT_ROOT=Path('/home/linuxagent/lmi-boot-menu-build/output')
OUTPUT=OUTPUT_ROOT/'fg-dt-order-candidate'
LOCKED=OUTPUT_ROOT/'boot-lmi-outer-dual-extent-test.img'
INPUTS=Path('/home/linuxagent/lmi-boot-menu-build/inputs')

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def diagnostic_files(contents):
 contents=dict(contents)
 make=contents['external-mobian/make-outer.py'].decode()
 assert make.count('def make(recipe,inputs):')==1
 make=make.replace('def make(recipe,inputs):','def make(recipe,inputs,qualified_menu=None):')
 marker='    entries=[(\'mobian/\'+name,parts[\'cmdline.txt\'][:-1]+b\'\\0\' if name==\'cmdline\' else parts[name])'
 assert make.count(marker)==1
 insertion='''    # Diagnostic only: start from the qualified menu DTB, not a fresh
    # overlay result whose automatically assigned phandles may differ.
    fg_spec=importlib.util.spec_from_file_location('fg_order',Path(__file__).with_name('reorder-dtb.py'))
    fg_module=importlib.util.module_from_spec(fg_spec);fg_spec.loader.exec_module(fg_module)
    qualified=fg_module.extract_menu((qualified_menu or Path('/qualified-output/boot-lmi-outer-dual-extent-test.img')).read_bytes())
    parts['dtb'],fg_info=fg_module.transform(qualified['mobian/dtb'])
    board_info['recomputed_overlay_dtb_used']=False
    board_info['recomputed_overlay_dtb_sha256']=board_info['merged_dtb_sha256']
    board_info['merged_dtb_sha256']=fg_info['output_sha256']
    board_info['fg_dt_order_diagnostic']=fg_info
'''
 make=make.replace(marker,insertion+marker)
 contents['external-mobian/make-outer.py']=make.encode()
 contents['external-mobian/reorder-dtb.py']=(HERE/'reorder-dtb.py').read_bytes()
 # All diagnostic outputs, including logs and raw firmware, use a child
 # directory. The qualified parent is separately mounted read-only.
 shell=contents['build.sh'].decode()
 before='mkdir -p "$build_root/source" "$build_root/output"'
 assert shell.count(before)==1
 shell=shell.replace(before,before+' "$build_root/output/fg-dt-order-candidate"')
 before='mount --bind "$build_root/output" "$rootfs/output"'
 assert shell.count(before)==1
 shell=shell.replace(before,'mkdir -p "$rootfs/qualified-output"\nmount --bind "$build_root/output" "$rootfs/qualified-output"\nmount -o remount,bind,ro "$rootfs/qualified-output"\nmount --bind "$build_root/output/fg-dt-order-candidate" "$rootfs/output"')
 before='tee "$build_root/output/build.log"';assert shell.count(before)==1
 shell=shell.replace(before,'tee "$build_root/output/fg-dt-order-candidate/build.log"')
 contents['build.sh']=shell.encode()

 pack=contents['external-mobian/pack-outer.py'].decode()
 marker="target=out/'boot-lmi-outer-dual-extent-test.img'";assert pack.count(marker)==1
 pack=pack.replace(marker,"target=out/'boot-lmi-fg-dt-order-test.img'")
 pack=pack.replace("'candidate_variant':'historical-32MiB-outer-board7-dual-extent-resetguard1'","'candidate_variant':'fg-profile-container-order-diagnostic'")
 pack=pack.replace("'outer-dual-extent-artifact-manifest.json'","'fg-dt-order-artifact-manifest.json'")
 pack=pack.replace('OUTER_DUAL_EXTENT_MENU_BUILD_COMPLETE_NOT_FOR_FLASHING','FG_DT_ORDER_MENU_BUILD_COMPLETE_NOT_FOR_FLASHING')
 contents['external-mobian/pack-outer.py']=pack.encode()
 for name in ('external-mobian/make-outer.py','external-mobian/pack-outer.py'):compile(contents[name],name,'exec')
 return contents

def prepare():
 # Root is needed for the retained input files. Trust only this exact checkout
 # for this process and its children; do not modify global Git configuration.
 if os.geteuid()==0:
  count=int(os.environ.get('GIT_CONFIG_COUNT','0'))
  os.environ['GIT_CONFIG_KEY_'+str(count)]='safe.directory'
  os.environ['GIT_CONFIG_VALUE_'+str(count)]=str(BASE.parents[2])
  os.environ['GIT_CONFIG_COUNT']=str(count+1)
 pins=json.loads((HERE/'upstream-pins.json').read_text())
 for name,digest in pins.items():assert hashlib.sha256((BASE/name).read_bytes()).hexdigest()==digest,'Upstream recipe changed: '+name
 order=load('fg_order',HERE/'reorder-dtb.py');old=order.extract_menu(LOCKED.read_bytes())
 baseline=load('fg_menu_baseline',BASE/'build-external.py');contents=baseline.files()
 contents=diagnostic_files(contents)
 baseline.files=lambda:contents
 stage=baseline.prepare()
 maker=load('fg_menu_maker',stage/'external-mobian/make-outer.py')
 outer,record=maker.make(stage,INPUTS,LOCKED)
 for name,digest in order.PARTS.items():
  if name!='mobian/dtb':assert record['components'][name]['sha256']==digest,'Unexpected component change: '+name
 assert record['components']['mobian/dtb']['sha256']=='12088ff3ebf5f22952e63f9699b20708e7ccae6ac311ccc079cb23ff1a6f96c1'
 report={'recipe':str(stage),'qualified_menu_preserved_sha256':order.MENU_SHA,'candidate_dtb':record['board_overlay']['fg_dt_order_diagnostic'],'other_components_unchanged':True,'outer_bytes':len(outer),'outer_crc32':record['crc32'],'firmware_built_in_this_invocation':False,'hardware_validated':False,'existing_candidate':((OUTPUT/'boot-lmi-fg-dt-order-test.img').exists())}
 print(json.dumps(report,indent=2));return stage

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--build',action='store_true');a=ap.parse_args();stage=prepare()
 print('FG_DT_ORDER_MENU_PREFLIGHT_PASS_NO_PHONE_CONTACT',flush=True)
 if a.build:
  subprocess.run(['bash',str(stage/'build.sh'),'--build','--with-lineage'],check=True)
  subprocess.run(['python3','-B',str(stage/'external-mobian/pack-outer.py'),str(OUTPUT)],check=True)
if __name__=='__main__':main()
