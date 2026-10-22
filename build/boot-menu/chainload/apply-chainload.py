#!/usr/bin/env python3
"""Apply/restore only hash-qualified changes in the disposable build tree."""
from pathlib import Path
import argparse,hashlib,json,subprocess,importlib.util
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--restore-only',action='store_true');ap.add_argument('--dual',action='store_true');a=ap.parse_args()
 base=a.source/'GPLDrivers/Library/SimpleInit';here=Path(__file__).resolve().parent
 def repo_for(info):
  if info.get('edk2_core'):return a.source/'Common/edk2'
  return a.source if info.get('edk2') else base
 if a.restore_only:
  if not a.manifest.exists():return
  record=json.loads(a.manifest.read_text())
  # Refuse all restoration if any reviewed output was changed afterwards.
  for path,info in record.items():
   f=repo_for(info)/path
   assert f.is_file() and sha(f.read_bytes())==info['after'], 'Unreviewed source edit: '+path
  for path,info in record.items():
   repo=repo_for(info)
   f=repo/path
   if info['new_file']:f.unlink()
   else:
    raw=subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+path])
    assert sha(raw)==info['upstream'];f.write_bytes(raw)
  a.manifest.unlink();return
 assert not a.manifest.exists(),'Restore previous qualified patch first'
 edits={};new_files={}
 spec=importlib.util.spec_from_file_location('diag',here/'patch-diagnostic.py')
 diag=importlib.util.module_from_spec(spec);spec.loader.exec_module(diag)
 for path in ['src/main/uefimain.c','src/gui/interface/core/bootmenu.c','src/boot/linux.c','src/linux-boot/aboot.c']:
  f=base/path;old=f.read_text();original=subprocess.check_output(['git','-C',str(base),'show','HEAD:'+path])
  if path.endswith('uefimain.c'):
   assert 'LMI_TEMPORARY_MENU_SMOKE_V1' in old and 'boot.configs.android' not in old
   new=old.replace('\tlogger_init();','''\tconfd_set_integer("boot.configs.android.mode", BOOT_LINUX);
\tconfd_set_string("boot.configs.android.desc", "LineageOS (experimental)");
\tconfd_set_boolean("boot.configs.android.show", true);
\tconfd_set_boolean("boot.configs.android.enabled", true);
\tlogger_init();''',1)
   if a.dual:
    new=new.replace('"boot.configs.mobian.mode", BOOT_REBOOT','"boot.configs.mobian.mode", BOOT_LINUX').replace('Mobian (restart installed OS)','Mobian (experimental direct boot)')
  elif path.endswith('bootmenu.c'):
   assert old.count('{"mobian","fastboot","recovery",NULL}')==1
   new=old.replace('{"mobian","fastboot","recovery",NULL}','{"mobian","android","fastboot","recovery",NULL}')
  elif path=='src/boot/linux.c':
   assert old==original.decode().replace('\r\n','\n')
   oldline='\tif(linux_boot_prepare(lb)!=0)'
   assert old.count(oldline)==1
   new=old.replace('int run_boot_linux(boot_config*boot){','extern int linux_boot_lmi_bundle(linux_boot*lb,const char*ident);\n\nint run_boot_linux(boot_config*boot){')
   new=new.replace(oldline,'''\tif(linux_boot_lmi_bundle(lb,boot->ident)!=0)
\t\tEDONE(tlog_error("verified lmi RAM bundle unavailable"));
'''+oldline)
   new=diag.patch_entry(new)
  else:
   assert old==original.decode().replace('\r\n','\n')
   new=old+'\n/* LMI_LINEAGE_RAM_HANDOFF_V1 */\n#include "lmi-boot-diagnostic.h"\n#include "lmi-bundle-loader.h"\n#include "lmi-android-fstab.h"\n'
  edits[path]=(new.encode(),{'after':sha(new.encode()),'upstream':sha(original),'new_file':False})
 path='src/linux-boot/linux.c';original=subprocess.check_output(['git','-C',str(base),'show','HEAD:'+path])
 assert (base/path).read_bytes()==original
 raw=diag.patch_prepare(original.decode().replace('\r\n','\n')).encode()
 edits[path]=(raw,{'after':sha(raw),'upstream':sha(original),'new_file':False})
 spec=importlib.util.spec_from_file_location('dtbopatch',here/'patch-dtbo.py')
 dtbopatch=importlib.util.module_from_spec(spec);spec.loader.exec_module(dtbopatch)
 path='src/linux-boot/dtbo.c';original=subprocess.check_output(['git','-C',str(base),'show','HEAD:'+path])
 assert (base/path).read_bytes()==original
 raw=dtbopatch.patch(original.decode().replace('\r\n','\n')).encode()
 edits[path]=(raw,{'after':sha(raw),'upstream':sha(original),'new_file':False})
 for name in ['bundle-format.h','lmi-bundle-loader.h','lmi-boot-diagnostic.h','lmi-android-fstab.h','variant-args.h','lmi-console-fit.h','lmi-console-zoom.h']:
  path='src/linux-boot/'+name;assert not (base/path).exists()
  raw=(here/name).read_bytes();edits[path]=(raw,{'after':sha(raw),'new_file':True})
 path='src/loggerd/client.c';original=subprocess.check_output(['git','-C',str(base),'show','HEAD:'+path]);assert (base/path).read_bytes()==original
 old=original.decode().replace('\r\n','\n')
 assert old.count('static char print_buff[16384];')==1
 new=old.replace('static char print_buff[16384];','#include "../linux-boot/lmi-console-fit.h"\nstatic char print_buff[16384];')
 needle='\t\tAsciiPrint("%a",print_buff);\n\t\tAsciiPrint("\\n");';assert new.count(needle)==1
 new=new.replace(needle,'\t\tlmi_fit_console_line(print_buff);')
 edits[path]=(new.encode(),{'after':sha(new.encode()),'upstream':sha(original),'new_file':False})
 path='src/linux-boot/SimpleInitBootLinux.inf'
 f=base/path;old=f.read_text();original=subprocess.check_output(['git','-C',str(base),'show','HEAD:'+path]);assert old==original.decode().replace('\r\n','\n')
 assert old.count('[LibraryClasses]\n')==1
 new=old.replace('[LibraryClasses]\n','[LibraryClasses]\n  DxeServicesLib\n')
 edits[path]=(new.encode(),{'after':sha(new.encode()),'upstream':sha(original),'new_file':False})
 # Fit the Android-only assets inside the upstream's existing 32-MiB FD
 # reservation. Do not edit the working lmi memory map.
 for path in ['configs/devices/lmi.conf','Platform/Qualcomm/sm8250/sm8250.fdf','Platform/Xiaomi/sm8250/lmi.fdf.inc']:
  old=(a.source/path).read_text();original=subprocess.check_output(['git','-C',str(a.source),'show','HEAD:'+path]);assert old==original.decode().replace('\r\n','\n')
  if path.endswith('lmi.conf'):
   new=old+'\n# Compact Android-only candidate: retain the original lmi FD reservation.\nFD_SIZE=0x02000000\n'
  elif path.endswith('sm8250.fdf'):
   assert old.count('NumBlocks     = 0x700\n')==1 and old.count('0x00000000|0x00700000')==1
   new=old.replace('NumBlocks     = 0x700\n','NumBlocks     = 0x2000\n').replace('0x00000000|0x00700000','0x00000000|0x02000000')
  elif path.endswith('lmi.fdf.inc'):
   new=old+'''\n// Verified OS components, loaded with GetSectionFromAnyFv, never from disk.
FILE FREEFORM = 4f9fd886-1b54-4e6c-9df8-2c6466521227 {
    SECTION RAW = /output/lmi-ram-assets.bin
    SECTION UI = "lmi verified OS assets"
}
'''
  edits[path]=(new.encode(),{'after':sha(new.encode()),'upstream':sha(original),'new_file':False,'edk2':True})
 if a.dual:
  # Reserve the additional 32 MiB from the immediately adjacent ordinary RAM.
  # All other regions remain identical; never overlap FD with allocator RAM.
  for path in ['configs/devices/lmi.conf','Platform/Qualcomm/sm8250/sm8250.fdf']:
   raw,info=edits[path];new=raw.decode()
   if path.endswith('lmi.conf'):new=new.replace('FD_SIZE=0x02000000','FD_SIZE=0x04000000')
   else:new=new.replace('NumBlocks     = 0x2000','NumBlocks     = 0x4000').replace('0x00000000|0x02000000','0x00000000|0x04000000')
   info['after']=sha(new.encode());edits[path]=(new.encode(),info)
  path='Platform/Xiaomi/sm8250/Library/lmi/PlatformMemoryMapLib/PlatformMemoryMapLib.c'
  original=subprocess.check_output(['git','-C',str(a.source),'show','HEAD:'+path]);assert (a.source/path).read_bytes()==original
  old=original.decode();assert old.count('0xCE000000, 0x02000000')==1 and old.count('0xD0000000,0x130000000')==1
  new=old.replace('0xCE000000, 0x02000000','0xCE000000, 0x04000000').replace('0xD0000000,0x130000000','0xD2000000,0x12E000000')
  edits[path]=(new.encode(),{'after':sha(new.encode()),'upstream':sha(original),'new_file':False,'edk2':True})
 # The compressed FV now exceeds 16 MiB: pinned PrePi lacks FILE_HEADER2.
 spec=importlib.util.spec_from_file_location('prepi',here/'patch-prepi.py')
 prepi=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepi)
 original=subprocess.check_output(['git','-C',str(a.source/'Common/edk2'),'show','HEAD:'+prepi.PATH])
 assert (a.source/'Common/edk2'/prepi.PATH).read_bytes()==original
 raw=prepi.patch(original)
 edits[prepi.PATH]=(raw,{'after':sha(raw),'upstream':sha(original),'new_file':False,'edk2_core':True})
 # Validate all inputs before mutating any source.
 for path,(raw,info) in edits.items():(repo_for(info)/path).write_bytes(raw)
 a.manifest.write_text(json.dumps({p:i for p,(_,i) in edits.items()},indent=2))
 print('EXPERIMENTAL_LINEAGE_SOURCE_PREPARED')
if __name__=='__main__':main()
