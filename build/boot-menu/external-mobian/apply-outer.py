#!/usr/bin/env python3
"""Bounded additive patch over the exact historical Android-working recipe."""
from pathlib import Path
import argparse,hashlib,json,subprocess
sha=lambda raw:hashlib.sha256(raw).hexdigest()
PEI='Silicon/Qualcomm/QcomPkg/Library/MemoryInitPeiLib/MemoryInitPeiLib.c'
PEI_SHA='6e11bffaefb25a38e7a83463c85b096e1c051fb5228f5d278cb04e8e5af5f5a2'

def patchset(source,recipe,output):
    base=source/'GPLDrivers/Library/SimpleInit';here=recipe/'external-mobian';edits={}
    def edit(path,change,root=base):
        target=root/path;raw=target.read_bytes()
        text=raw.decode().replace('\r\n','\n');new=change(text).encode()
        assert new!=raw,path
        edits[str(target.relative_to(source))]=(raw,new)
    def replace(text,old,new):
        assert text.count(old)==1,old
        return text.replace(old,new)
    edit('src/main/uefimain.c',lambda t:replace(replace(t,'"boot.configs.mobian.mode", BOOT_REBOOT','"boot.configs.mobian.mode", BOOT_LINUX'),'Mobian (restart installed OS)','Mobian (direct boot)'))
    def entry(t):
        t=replace(t,'extern int linux_boot_lmi_bundle(', 'extern int linux_boot_lmi_external(')
        return replace(t,'if(linux_boot_lmi_bundle(lb,boot->ident)!=0)','if(linux_boot_lmi_external(lb,boot->ident)!=0)')
    edit('src/boot/linux.c',entry)
    edit('src/linux-boot/aboot.c',lambda t:t+'\n#include "outer-loader.h"\n#include "lmi-kernel-extent.h"\n')
    def prepare(t):
        t=replace(t,'extern void lmi_boot_stage(const char*stage);','extern void lmi_boot_stage(const char*stage);\nextern int linux_boot_lmi_kernel_extent(linux_boot*lb);')
        return replace(t,'\tif(linux_boot_select_fdt(lb)!=0)',
                       '\tif((!strcmp(lb->config->tag,"mobian")||!strcmp(lb->config->tag,"android"))&&linux_boot_lmi_kernel_extent(lb)!=0)\n\t\treturn trlog_error(-1,"Pinned kernel runtime extent reservation failed");\n\tif(linux_boot_select_fdt(lb)!=0)')
    edit('src/linux-boot/linux.c',prepare)
    def fstab(t):
        return replace(t,'    if(!lb||!lb->config||strcmp(lb->config->tag,"android")||!lb->dtb.address)return -1;',
                       '    if(!lb||!lb->config||!lb->dtb.address)return -1;\n    if(!strcmp(lb->config->tag,"mobian"))return 0;\n    if(strcmp(lb->config->tag,"android"))return -1;')
    edit('src/linux-boot/lmi-android-fstab.h',fstab)
    raw=(source/PEI).read_bytes();assert sha(raw)==PEI_SHA
    def pei(t):
        # Include only after AddHob is declared, before MemoryPeim.
        t=replace(t,'/*++',' #include "outer-pei.h"\n\n/*++')
        t=replace(t,'  ASSERT(Fdt != NULL);','  ASSERT(Fdt != NULL);\n  if(Fdt)LmiFindOuter(Fdt,UefiMemoryBase,UefiMemorySize);')
        return replace(t,'      AddHob(MemoryDescriptorEx);','      LmiAddProtectedHob(MemoryDescriptorEx);')
    edit(PEI,pei,source)
    for folder,names in [(base/'src/linux-boot',['outer-loader.h','outer-range.h']),
                         ((source/PEI).parent,['outer-pei.h','outer-range.h'])]:
        for name in names:
            target=folder/name;assert not target.exists(),target
            edits[str(target.relative_to(source))]=(None,(here/name).read_bytes())
    for name,raw in [('outer-lock.h',(output/'outer-lock.h').read_bytes()),
                     ('lmi-kernel-extent.h',(here/'lmi-kernel-extent.h').read_bytes())]:
        target=base/'src/linux-boot'/name;assert not target.exists()
        edits[str(target.relative_to(source))]=(None,raw)
    return edits

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('recipe',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--restore',action='store_true')
    a=ap.parse_args();manifest=a.output/'outer-source-manifest.json'
    if a.restore:
        if manifest.exists():
            record=json.loads(manifest.read_text())
            for name,info in record.items():assert sha((a.source/name).read_bytes())==info['after'],name
            # Recover exact pre-overlay source from the snapshot kept outside Git.
            for name,info in record.items():
                target=a.source/name
                if info['before'] is None:target.unlink()
                else:
                    raw=(a.output/'outer-source-before'/name).read_bytes();assert sha(raw)==info['before'];target.write_bytes(raw)
            manifest.unlink()
    else:
        assert not manifest.exists(),'Restore the previous outer overlay first'
        edits=patchset(a.source,a.recipe,a.output)
        record={name:{'before':None if old is None else sha(old),'after':sha(new)} for name,(old,new) in edits.items()}
        for name,(old,new) in edits.items():
            if old is not None:
                saved=a.output/'outer-source-before'/name;saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(old)
        manifest.write_text(json.dumps(record,indent=2)+'\n')
        for name,(_,new) in edits.items():(a.source/name).write_bytes(new)
        print('EXTERNAL_MOBIAN_SOURCE_PREPARED',len(edits))
