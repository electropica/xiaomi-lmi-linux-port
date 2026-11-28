#!/usr/bin/env python3
"""Extract pinned boot-v2 components for a future RAM-backed menu asset volume.

No device access, boot-header conversion, DTB selection or DTBO change.
"""
import argparse, hashlib, json, struct
from pathlib import Path

def extract(raw):
    if len(raw)<1660 or raw[:8]!=b'ANDROID!':raise ValueError('Not a complete Android boot-v2 header')
    u32=lambda off:struct.unpack_from('<I',raw,off)[0]
    page=u32(36)
    if u32(40)!=2 or page<2048 or page>65536 or page&(page-1):raise ValueError('Unsupported boot version/page size')
    if u32(1644)!=1660:raise ValueError('Unexpected v2 header size')
    align=lambda n:(n+page-1)//page*page
    ksize,rsize,ssize=u32(8),u32(16),u32(24)
    recovery_size=u32(1632)
    recovery_offset=struct.unpack_from('<Q',raw,1636)[0]
    if not ksize or not rsize or not u32(1648):raise ValueError('Missing kernel/ramdisk/DTB')
    if ssize:raise ValueError('Second-stage payload is not qualified')
    start=page
    parts={}
    for name,size in [('kernel',ksize),('initrd',rsize)]:
        if start+size>len(raw):raise ValueError('Truncated '+name)
        parts[name]=raw[start:start+size];start+=align(size)
    if recovery_size:
        if recovery_offset!=start or start+recovery_size>len(raw):raise ValueError('Unexpected recovery DTBO layout')
        parts['recovery-dtbo']=raw[start:start+recovery_size]
        start+=align(recovery_size)
    dsize=u32(1648)
    if start+dsize>len(raw):raise ValueError('Truncated DTB')
    parts['dtb']=raw[start:start+dsize]
    # Keep original primary+extra command line in order; no new hardware flags.
    cmd=(raw[64:576].split(b'\0')[0]+raw[608:1632].split(b'\0')[0]).decode('ascii')
    parts['cmdline.txt']=(cmd+'\n').encode()
    return parts

def main():
    p=argparse.ArgumentParser();p.add_argument('--mobian',type=Path,required=True);p.add_argument('--android',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    lock=json.loads(Path(__file__).with_name('sources.lock.json').read_text())
    if a.output.exists():raise SystemExit('Refusing existing output')
    prepared={};report={'status':'components_only_no_chainload_validation','images':{}}
    for name,file in [('mobian',a.mobian),('android',a.android)]:
        raw=file.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest!=lock['os_images'][name]:raise SystemExit('Wrong '+name+' boot hash')
        prepared[name]=extract(raw)
        report['images'][name]={'source_sha256':digest,'components':{k:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in prepared[name].items()}}
    a.output.mkdir(parents=True)
    for name,parts in prepared.items():
        dest=a.output/name;dest.mkdir()
        for key,data in parts.items():(dest/key).write_bytes(data)
    (a.output/'manifest.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
