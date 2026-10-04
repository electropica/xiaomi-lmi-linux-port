#!/usr/bin/env python3
"""Read-only lmi camera backend inventory. Never starts or loads a camera HAL."""
import json
import os
import struct
from pathlib import Path


def elf_metadata(path):
    with path.open('rb') as f:
        header = f.read(64)
        if header[:6] != b'\x7fELF\x02\x01':
            raise ValueError('not a little-endian ELF64 object')
        phoff = struct.unpack_from('<Q', header, 32)[0]
        phentsize, phnum = struct.unpack_from('<HH', header, 54)
        if phentsize != 56 or phnum > 256:
            raise ValueError('unsupported program header table')
        f.seek(phoff)
        entries = [struct.unpack('<IIQQQQQQ', f.read(56)) for _ in range(phnum)]
        result = {'interpreter': None, 'needed': []}
        dynamic = None
        for kind, flags, offset, address, physical, filesz, memsz, align in entries:
            if kind == 3:
                f.seek(offset)
                result['interpreter'] = f.read(min(filesz, 4096)).split(b'\0', 1)[0].decode()
            if kind == 2:
                dynamic = (offset, filesz)
        if dynamic is None:
            return result
        f.seek(dynamic[0])
        tags = []
        for _ in range(min(dynamic[1] // 16, 4096)):
            tag, value = struct.unpack('<QQ', f.read(16))
            if tag == 0:
                break
            tags.append((tag, value))
        strings = next((v for t, v in tags if t == 5), None)
        string_size = next((v for t, v in tags if t == 10), 0)
        if strings is None or string_size > 262144:
            raise ValueError('missing or oversized dynamic string table')
        for kind, flags, offset, address, physical, filesz, memsz, align in entries:
            if kind == 1 and address <= strings < address + filesz:
                start = offset + strings - address
                if strings - address + string_size > filesz:
                    raise ValueError('string table exceeds file segment')
                f.seek(start)
                blob = f.read(string_size)
                result['needed'] = [blob[v:].split(b'\0', 1)[0].decode()
                                    for t, v in tags if t == 1]
                return result
        raise ValueError('unmapped dynamic string table')


def inspect():
    paths = [
        '/usr/share/megapixels/config/qcom,kona-mtp.ini',
        '/system/bin/linker64',
        '/vendor/lib64/hw/camera.qcom.so',
        '/vendor/bin/hw/android.hardware.camera.provider@2.4-service_64',
        '/system/bin/hwservicemanager', '/system/bin/servicemanager',
        '/dev/binder', '/dev/hwbinder', '/dev/vndbinder',
        '/dev/binderfs/binder', '/dev/binderfs/hwbinder',
        '/dev/binderfs/vndbinder', '/dev/ashmem',
        '/dev/__properties__', '/dev/socket/property_service',
    ]
    result = {'read_only': True, 'kernel': os.uname().release,
              'paths': {p: Path(p).exists() for p in paths},
              'video_nodes': {}, 'elf': {}}
    for path in sorted(Path('/sys/class/video4linux').glob('video*/name')):
        result['video_nodes'][path.parent.name] = path.read_text().strip()
    for name in paths[2:4]:
        path = Path(name)
        if path.is_file():
            try:
                result['elf'][name] = elf_metadata(path)
            except (OSError, ValueError, struct.error, UnicodeError) as error:
                result['elf'][name] = {'error': str(error)}
    return result


if __name__ == '__main__':
    print(json.dumps(inspect(), indent=2, sort_keys=True))
