#!/usr/bin/env python3
"""Verify exact v1 kernel preservation, ramdisk replacement and boot-id digest."""
from pathlib import Path
import hashlib,importlib.util,struct
here=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('pack',here/'pack-outer.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
header=bytearray(4096);header[:8]=b'ANDROID!'
for off,value in [(8,19),(16,1),(36,4096),(40,1)]:struct.pack_into('<I',header,off,value)
kernel=b'k'*19
raw=bytes(header)+kernel+b'\0'*(4096-19)+b'\n'+b'\0'*4095
outer=b'LMIBNDL1'+b'\0'*4093
result=m.pack(raw,outer)
assert result[4096:8192]==raw[4096:8192]
assert struct.unpack_from('<I',result,16)[0]==len(outer)
assert result[8192:8192+len(outer)]==outer
h=hashlib.sha1()
for part in [kernel,outer,b'',b'']:h.update(part);h.update(struct.pack('<I',len(part)))
assert result[576:608]==h.digest()+b'\0'*12
small_header=bytearray(header[:2048]);struct.pack_into('<I',small_header,36,2048)
small_raw=bytes(small_header)+kernel+b'\0'*(2048-19)+b'\n'+b'\0'*2047
small_result=m.pack(small_raw,outer)
assert small_result[2048:4096]==small_raw[2048:4096]
assert small_result[4096:4096+len(outer)]==outer
for changed in [raw[:-1],b'bad'+raw[3:]]:
    try:m.pack(changed,outer)
    except AssertionError:pass
    else:raise AssertionError('Malformed source accepted')
print('OUTER_BOOT_PACK_KERNEL_UNCHANGED_RAMDISK_ID_AND_TRUNCATION_PASS')
