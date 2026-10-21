#!/usr/bin/env python3
"""Match only the menu boot header OS version to pinned Android. No phone I/O."""
from pathlib import Path
import argparse,hashlib,json,struct
ANDROID_SHA='9d7dd4823860f7ad73c82542669620b2cee1ca466789958175be63bb77e85411'
def sha(b):return hashlib.sha256(b).hexdigest()
def describe(v):
    return {'packed':v,'version':[v>>25&127,v>>18&127,v>>11&127],'patch_year':2000+(v>>4&127),'patch_month':v&15}
def adjust(raw,android,expected):
    if sha(raw)!=expected:raise ValueError('Unexpected menu image hash')
    if sha(android)!=ANDROID_SHA:raise ValueError('Unexpected Android boot hash')
    if raw[:8]!=b'ANDROID!' or android[:8]!=b'ANDROID!':raise ValueError('Invalid boot magic')
    if struct.unpack_from('<I',raw,40)[0]!=1 or struct.unpack_from('<I',android,40)[0]!=2:raise ValueError('Unqualified boot-header versions')
    if raw[-64:-60]==b'AVBf':raise ValueError('Refuse a signed/AVB-footer image')
    old=struct.unpack_from('<I',raw,44)[0];new=struct.unpack_from('<I',android,44)[0]
    if not new:raise ValueError('Android OS version must be explicit')
    out=raw[:44]+android[44:48]+raw[48:]
    assert len(out)==len(raw) and out[:44]==raw[:44] and out[48:]==raw[48:]
    return out,{'input_sha256':sha(raw),'output_sha256':sha(out),'android_sha256':ANDROID_SHA,'bytes':len(out),'old':describe(old),'new':describe(new),'only_os_version_field_changed':True,'changed_offsets':[i for i in range(44,48) if raw[i]!=out[i]],'hardware_validation':False,'no_flash':True}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--image',type=Path,required=True);ap.add_argument('--android',type=Path,required=True);ap.add_argument('--expected-input-sha256',required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--manifest',type=Path,required=True);a=ap.parse_args()
    out,report=adjust(a.image.read_bytes(),a.android.read_bytes(),a.expected_input_sha256)
    if a.output.exists() or a.manifest.exists():raise SystemExit('Refuse existing output/manifest')
    with a.output.open('xb') as f:f.write(out)
    with a.manifest.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
