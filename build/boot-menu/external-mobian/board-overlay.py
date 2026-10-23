#!/usr/bin/env python3
"""Apply the exact, already-pinned Xiaomi lmi board7 overlay to Mobian's base."""
from pathlib import Path
import hashlib
import struct
import subprocess
import tempfile

BASE_SHA = '74edf0671376aa58df50897766500d04840af13d4bf27d0f78598ab7343d02f9'
DTBO_SHA = '45f0989700c68afcd817a6a4569ba67225cf128e3eedd35a658bad384632eec4'
BOARD_SHA = '019bd837d01396d86dcecc65a39c6591fc0ceeb6aa5ef98cc7374cc6248c7466'
BOARD_INDEX = 7


def apply_board(base, dtbo):
    if hashlib.sha256(base).hexdigest() != BASE_SHA:
        raise ValueError('Unknown Mobian base DTB; refusing board overlay')
    if len(dtbo) != 33554432 or hashlib.sha256(dtbo).hexdigest() != DTBO_SHA:
        raise ValueError('Unknown Xiaomi DTBO partition input')
    magic,total,header,entry_size,count,offset,page,version = struct.unpack_from('>8I',dtbo)
    if (magic != 0xd7b7ab1e or header != 32 or entry_size != 32
            or not BOARD_INDEX < count <= 128 or offset < header
            or offset + count*entry_size > total or total > len(dtbo)):
        raise ValueError('Unexpected DTBO table layout')
    size,start = struct.unpack_from('>II',dtbo,offset+BOARD_INDEX*entry_size)
    if start < offset+count*entry_size or not 0 < size <= 2*1024*1024 or start+size > total:
        raise ValueError('Malformed board overlay entry')
    board=dtbo[start:start+size]
    if hashlib.sha256(board).hexdigest()!=BOARD_SHA:
        raise ValueError('Unexpected board7 bytes')
    with tempfile.TemporaryDirectory(prefix='lmi-board7-') as directory:
        root=Path(directory)
        (root/'base.dtb').write_bytes(base)
        (root/'board.dtbo').write_bytes(board)
        subprocess.run(['fdtoverlay','-i',str(root/'base.dtb'),'-o',str(root/'result.dtb'),
                        str(root/'board.dtbo')],check=True,timeout=60)
        result=(root/'result.dtb').read_bytes()
    if (len(result)<40 or len(result)>2*1024*1024
            or result[:4]!=bytes.fromhex('d00dfeed')
            or struct.unpack_from('>I',result,4)[0]!=len(result)):
        raise ValueError('Malformed merged Mobian DTB')
    return result,{'board_index':BOARD_INDEX,'base_dtb_sha256':BASE_SHA,
                  'dtbo_partition_sha256':DTBO_SHA,'board_sha256':BOARD_SHA,
                  'merged_dtb_sha256':hashlib.sha256(result).hexdigest(),
                  'merged_dtb_bytes':len(result),'applied_offline':True,
                  'runtime_dump_used_as_boot_input':False}
