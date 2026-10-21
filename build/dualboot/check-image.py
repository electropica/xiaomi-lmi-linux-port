#!/usr/bin/env python3
"""Validate the two filesystem identities consumed by the pinned boot."""
import struct,sys,uuid,zlib
from pathlib import Path
p=Path(sys.argv[1])
with p.open('rb') as f:
    f.seek(4096);h=f.read(4096)
    assert h[:8]==b'EFI PART'
    size=struct.unpack_from('<I',h,12)[0];temp=bytearray(h[:size]);crc=struct.unpack_from('<I',temp,16)[0];temp[16:20]=b'\0'*4
    assert zlib.crc32(temp)&0xffffffff==crc
    lba,count,entry_size,crc=struct.unpack_from('<QIII',h,72)
    assert count*entry_size<=1024*1024
    f.seek(lba*4096);t=f.read(count*entry_size)
    assert zlib.crc32(t)&0xffffffff==crc
    expected=['7bd723c2-51d6-4015-b28b-2b38191bf765','dba94dfe-0fb9-4f95-970e-22949f4e69dc']
    for i,want in enumerate(expected):
        start,end=struct.unpack_from('<QQ',t,i*entry_size+32)
        assert start<=end and (end+1)*4096<=p.stat().st_size
        f.seek(start*4096+1024);sb=f.read(1024)
        assert sb[56:58]==b'\x53\xef'
        assert str(uuid.UUID(bytes=sb[104:120]))==want
print('IMAGE_FILESYSTEM_IDENTITIES_MATCH_PINNED_BOOT')
