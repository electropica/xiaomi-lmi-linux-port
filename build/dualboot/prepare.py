#!/usr/bin/env python3
"""Produce a boot artifact and a text-only migration plan; never access a device."""
import argparse,gzip,hashlib,json,struct
from pathlib import Path

BOOT_SHA='a89ae4d9529dcef55d3969eb6b5a75c2617d9ef0e2e1f568c5f619eb1adf5c50'
FUNCTIONS_SHA='cd5aa98e2118e6788578adcf95a7c3abb62a90f20768c289bd2ae77ba24d55ad'
GIB=1024**3
def sha(b):return hashlib.sha256(b).hexdigest()
def align(n,p):return (n+p-1)//p*p

def cpio_replace(data,name,replacement):
    pos=0;out=bytearray();found=0
    while pos<len(data):
        h=bytearray(data[pos:pos+110])
        if h[:6]!=b'070701':raise ValueError('Only reviewed newc archive supported')
        vals=[int(h[i:i+8],16) for i in range(6,110,8)]
        ns=pos+110;start=align(ns+vals[11],4)
        filename=data[ns:ns+vals[11]-1].decode()
        content=data[start:start+vals[6]]
        if len(content)!=vals[6]:raise ValueError('Truncated cpio')
        if filename.lstrip('./')==name:
            found+=1
            if sha(content)!=FUNCTIONS_SHA:raise ValueError('Unreviewed init functions')
            text=content.decode();begin=text.index('mount_subpartitions() {\n')
            end=text.index('\n# Rewrite /dev/dm-X paths',begin)
            content=(text[:begin]+replacement.rstrip()+'\n'+text[end:]).encode()
        h[54:62]=f'{len(content):08x}'.encode()
        out.extend(h);out.extend(data[ns:ns+vals[11]])
        out.extend(b'\0'*(-len(out)%4));out.extend(content);out.extend(b'\0'*(-len(out)%4))
        pos=align(start+vals[6],4)
        if filename=='TRAILER!!!':break
    if found!=1:raise ValueError('Expected exactly one init_functions.sh')
    return bytes(out)+b'\0'*(-len(out)%512)

def boot_parts(data):
    if data[:8]!=b'ANDROID!':raise ValueError('Bad boot magic')
    a=struct.unpack_from('<10I',data,8);ks,rs,ss,page,version=a[0],a[2],a[4],a[7],a[8]
    if version!=2 or page!=4096:raise ValueError('Only reviewed v2 / 4096 boot supported')
    ds,do,hs,ts,ta=struct.unpack_from('<IQIIQ',data,1632)
    if hs!=1660:raise ValueError('Unexpected header size')
    parts=[];off=page
    for n in (ks,rs,ss,ds,ts):
        parts.append(data[off:off+n]);off+=align(n,page)
    if any(len(p)!=n for p,n in zip(parts,(ks,rs,ss,ds,ts))):raise ValueError('Truncated boot')
    if ds and do!=page+align(ks,page)+align(rs,page)+align(ss,page):raise ValueError('Bad dtbo offset')
    if data[off:].strip(b'\0'):raise ValueError('Unknown signed footer/tail')
    return page,parts

def repack(data,replacement):
    if sha(data)!=BOOT_SHA:raise ValueError('Wrong RPMh boot')
    page,parts=boot_parts(data);old=list(parts)
    parts[1]=gzip.compress(cpio_replace(gzip.decompress(parts[1]),'init_functions.sh',replacement),mtime=0)
    header=bytearray(data[:page]);struct.pack_into('<I',header,16,len(parts[1]))
    if parts[3]:struct.pack_into('<Q',header,1636,page+sum(align(len(p),page) for p in parts[:3]))
    ident=hashlib.sha1()
    for p in parts:ident.update(p);ident.update(struct.pack('<I',len(p)))
    header[576:608]=ident.digest()+b'\0'*12
    result=bytes(header)+b''.join(p+b'\0'*(-len(p)%page) for p in parts)
    _,check=boot_parts(result)
    if any(check[i]!=old[i] for i in (0,2,3,4)):raise ValueError('Kernel/DTB/other segment changed')
    return result,{'kernel_sha256':sha(parts[0]),'dtb_sha256':sha(parts[4]),'boot_sha256':sha(result),'base_boot_sha256':sha(data)}

def layout_plan(d):
    if d['sector_bytes']!=4096 or d['entry_count']!=64:raise ValueError('Unexpected GPT geometry')
    entries=d['entries'];u=[p for p in entries if p['label']=='userdata']
    if len(u)!=1 or u[0]['number']!=34:raise ValueError('Unexpected userdata')
    u=u[0]
    if u['end_lba']!=d['last_usable_lba'] or any(p['end_lba']>u['end_lba'] for p in entries):raise ValueError('userdata not last')
    if any(p['number']==35 or p['label']=='mobian' for p in entries):raise ValueError('Target already exists')
    # 1 MiB alignment, 16 GiB dedicated container, trailing alignment gap retained.
    start=(u['end_lba']+1-16*GIB//4096)//256*256
    end=start+16*GIB//4096-1
    if start<=u['start_lba'] or end>d['last_usable_lba']:raise ValueError('No space')
    return {'status':'DESIGN_ONLY_NOT_INSTALL_AUTHORIZATION','sector_bytes':4096,
      'preserve_other_partitions':True,'userdata':{'number':34,'start_lba':u['start_lba'],'old_end_lba':u['end_lba'],'new_end_lba':start-1,'reformat_required':True},
      'mobian':{'number':35,'label':'mobian','start_lba':start,'end_lba':end,'bytes':16*GIB},
      'android_boot':'normal default boot partition','mobian_boot':'PC fastboot boot, no recovery replacement',
      'hardware_validation':'PENDING; fresh GPT and recovery tool qualification required before migration'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--boot',type=Path,required=True);ap.add_argument('--layout',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if a.output.exists():raise SystemExit('Refusing existing output')
    result,info=repack(a.boot.read_bytes(),Path(__file__).with_name('mount-dualboot.sh').read_text())
    plan=layout_plan(json.loads(a.layout.read_text()))
    a.output.mkdir(parents=True)
    (a.output/'mobian-dualboot-boot.img').write_bytes(result)
    (a.output/'layout-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    (a.output/'boot-manifest.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info))
if __name__=='__main__':main()
