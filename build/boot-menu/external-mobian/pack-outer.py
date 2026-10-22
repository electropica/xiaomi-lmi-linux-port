#!/usr/bin/env python3
"""Attach the pinned Mobian component bundle as the menu's Android-v1 ramdisk."""
import argparse,hashlib,json,struct
from pathlib import Path

def pack(raw,outer):
    assert raw[:8]==b'ANDROID!' and len(raw)>=2048
    u32=lambda n:struct.unpack_from('<I',raw,n)[0]
    page=u32(36);kernel_size=u32(8);ramdisk_size=u32(16)
    assert u32(40)==1 and page in (2048,4096) and u32(24)==0 and u32(1632)==0
    aligned=lambda n:(n+page-1)//page*page
    assert len(raw)==page+aligned(kernel_size)+aligned(ramdisk_size)
    assert kernel_size and outer[:8]==b'LMIBNDL1' and 4096<=len(outer)<=64*1024*1024
    header=bytearray(raw[:page]);struct.pack_into('<I',header,16,len(outer))
    kernel=raw[page:page+kernel_size]
    digest=hashlib.sha1()
    for blob in [kernel,outer,b'',b'']:
        digest.update(blob);digest.update(struct.pack('<I',len(blob)))
    header[576:608]=digest.digest()+b'\0'*12
    result=bytes(header)+raw[page:page+aligned(kernel_size)]+outer+b'\0'*(-len(outer)%page)
    assert len(result)<=134217728
    assert result[page:page+kernel_size]==kernel
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args()
    out=a.output;raw=(out/'boot-lmi-lineage-test.img').read_bytes()
    record=json.loads((out/'lineage-artifact-manifest.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==record['sha256']
    outer=(out/'lmi-outer-mobian.bin').read_bytes()
    info=json.loads((out/'lmi-outer-mobian.json').read_text())
    assert hashlib.sha256(outer).hexdigest()==info['sha256']
    image=pack(raw,outer);target=out/'boot-lmi-outer-mobian-test.img';target.write_bytes(image)
    record.update({'sha256':hashlib.sha256(image).hexdigest(),'bytes':len(image),
                   'candidate_variant':'historical-32MiB-outer-mobian-resetguard1',
                   'outer_assets':info,'hardware_validated':False,'temporary_boot_only':True,
                   'reset_guard':json.loads((out/'reset-guard-manifest.json').read_text()),
                   'outer_source_manifest':json.loads((out/'outer-source-manifest.json').read_text())})
    assert record['reset_guard']['restored'] and record['reset_guard']['builder_exit']==0
    (out/'outer-mobian-artifact-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print('OUTER_MOBIAN_MENU_BUILD_COMPLETE_NOT_FOR_FLASHING')
    print('IMAGE='+str(target));print('SHA256='+record['sha256'])
