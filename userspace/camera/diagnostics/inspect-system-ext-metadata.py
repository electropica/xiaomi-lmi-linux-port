#!/usr/bin/env python3
"""Read-only primary LP metadata inspection; never maps or writes partitions."""
import hashlib, json, re, struct
from pathlib import Path

def checked_checksum(blob, checksum_start):
    expected = blob[checksum_start:checksum_start+32]
    mutable = bytearray(blob)
    mutable[checksum_start:checksum_start+32] = bytes(32)
    if hashlib.sha256(mutable).digest() != expected:
        raise ValueError('metadata checksum mismatch')

with Path('/dev/block/by-name/super').open('rb', buffering=0) as f:
    f.seek(4096)
    geometry = f.read(4096)
    magic, size = struct.unpack_from('<II', geometry)
    if magic != 0x616c4467 or not 52 <= size <= 4096:
        raise ValueError('unsupported LP geometry')
    checked_checksum(geometry[:size], 8)
    maximum, slots, logical_block = struct.unpack_from('<III', geometry, 40)
    if not 128 <= maximum <= 16*1024*1024 or not 1 <= slots <= 8:
        raise ValueError('invalid metadata bounds')
    cmdline = Path('/proc/cmdline').read_text()
    suffix = re.search(r'(?:^|\s)androidboot.slot_suffix=(_[ab])(?:\s|$)', cmdline)
    results = {'read_only': True, 'boot_slot_suffix': suffix.group(1) if suffix else None,
               'geometry_checksum': 'valid', 'slots': []}
    for slot in range(slots):
        f.seek(12288 + maximum*slot)
        blob = f.read(maximum)
        header_magic, major, minor, header_size = struct.unpack_from('<IHHI', blob)
        if header_magic != 0x414c5030:
            results['slots'].append({'slot':slot, 'header':'absent'})
            continue
        if major != 10 or minor > 2 or not 128 <= header_size <= maximum:
            raise ValueError('unsupported LP metadata version/header')
        checked_checksum(blob[:header_size], 12)
        tables_size = struct.unpack_from('<I', blob, 44)[0]
        if tables_size > maximum-header_size:
            raise ValueError('invalid table bounds')
        tables = blob[header_size:header_size+tables_size]
        if hashlib.sha256(tables).digest() != blob[48:80]:
            raise ValueError('table checksum mismatch')
        po, pn, ps = struct.unpack_from('<III', blob, 80)
        eo, en, es = struct.unpack_from('<III', blob, 92)
        bo, bn, bs = struct.unpack_from('<III', blob, 116)
        if ps != 52 or es != 24 or bs != 64:
            raise ValueError('unsupported table entry sizes')
        for offset, count, entry_size in [(po,pn,ps),(eo,en,es),(bo,bn,bs)]:
            if offset+count*entry_size > len(tables):
                raise ValueError('table exceeds bounds')
        devices = []
        for n in range(bn):
            entry = tables[bo+n*bs:bo+(n+1)*bs]
            devices.append(entry[24:60].split(b'\0',1)[0].decode('ascii'))
        partitions = []
        for n in range(pn):
            entry = tables[po+n*ps:po+(n+1)*ps]
            name = entry[:36].split(b'\0',1)[0].decode('ascii')
            if name not in ('system_ext','system_ext_a','system_ext_b'):
                continue
            attributes, first, count, group = struct.unpack_from('<IIII',entry,36)
            if first+count > en:
                raise ValueError('invalid extent range')
            extents=[]
            for index in range(first, first+count):
                sectors, target_type, sector, source = struct.unpack_from('<QIQI',tables,eo+index*es)
                if source >= len(devices):
                    raise ValueError('invalid extent source')
                extents.append({'sectors':sectors,'type':target_type,'sector':sector,'source':devices[source]})
            partitions.append({'name':name,'bytes':512*sum(e['sectors'] for e in extents),'extents':extents})
        results['slots'].append({'slot':slot,'checksums':'valid','system_ext':partitions})
print(json.dumps(results,indent=2))
