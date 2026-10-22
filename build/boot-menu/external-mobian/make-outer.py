#!/usr/bin/env python3
"""Package only the pinned Mobian boot components; no firmware compilation."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,struct,zlib

def make(recipe,inputs):
    spec=importlib.util.spec_from_file_location('extract',recipe/'extract-payloads.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    raw=(inputs/'mobian.img').read_bytes()
    expected=json.loads((recipe/'sources.lock.json').read_text())['os_images']['mobian']
    assert hashlib.sha256(raw).hexdigest()==expected
    parts=module.extract(raw)
    entries=[('mobian/'+name,parts['cmdline.txt'][:-1]+b'\0' if name=='cmdline' else parts[name])
             for name in ['kernel','initrd','dtb','cmdline']]
    entries.append(('mobian/identity',b'lmi-outer-v1\0'))
    data=bytearray(4096);report={}
    for i,(name,payload) in enumerate(entries):
        data.extend(b'\0'*(-len(data)%4096));offset=len(data);data.extend(payload)
        struct.pack_into('<32sQQII',data,32+i*56,name.encode(),offset,len(payload),zlib.crc32(payload),0)
        report[name]={'offset':offset,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()}
    struct.pack_into('<8sIIQ',data,0,b'LMIBNDL1',1,5,len(data))
    assert len(data)<=64*1024*1024
    return bytes(data),{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                        'crc32':zlib.crc32(data),'source_boot_sha256':expected,'components':report}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('recipe',type=Path);ap.add_argument('inputs',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();data,record=make(a.recipe,a.inputs)
    a.output.mkdir(exist_ok=True)
    (a.output/'lmi-outer-mobian.bin').write_bytes(data)
    (a.output/'lmi-outer-mobian.json').write_text(json.dumps(record,indent=2)+'\n')
    (a.output/'outer-lock.h').write_text('/* Generated from the pinned Mobian boot image. */\n#define LMI_OUTER_BYTES '+str(len(data))+'u\n#define LMI_OUTER_CRC32 0x%08Xu\n'%record['crc32'])
    print('PINNED_OUTER_MOBIAN_ASSETS_PREPARED',len(data),record['sha256'])
