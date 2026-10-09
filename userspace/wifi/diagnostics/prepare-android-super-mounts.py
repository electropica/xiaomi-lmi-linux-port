#!/usr/bin/env python3
"""Prepare a private mount-script variant from paired, read-only lpdump reports.

Does not access a phone, partition, image, mount or device-mapper interface.
Supports metadata 10.0 and one linear super extent per partition only. Other
layouts require review rather than guessing offsets. The generated script is
not automatically installed or added to an image builder.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

REFERENCE_SHA256 = '6e8fff8db44d120c13e321130b58c6b7e13c872a49782e8a07171ca03a76f5a9'
LEGACY = {'system': (1048576, 1144766464), 'vendor': (1146093568, 817250304)}

def bounded_read(path, limit):
    data = Path(path).read_bytes()
    if len(data) > limit:
        raise ValueError('Input exceeds the bounded report size')
    return data

def layout(text, document):
    if 'Metadata version: 10.0\n' not in text.replace('\r\n', '\n'):
        raise ValueError('Only reviewed metadata version 10.0 is supported')
    devices = document.get('block_devices', [])
    if document.get('enabled') is not True or len(devices) != 1 or devices[0].get('name') != 'super':
        raise ValueError('Expected a single enabled dynamic super device')
    super_size = int(devices[0]['size'])
    if not 0 < super_size < 2**42 or super_size % 512:
        raise ValueError('Invalid super size')
    block = re.search(r'Block device table:\s*-+\s*Partition name: super\s*First sector: (\d+)\s*Size: (\d+) bytes', text)
    if not block or int(block[2]) != super_size:
        raise ValueError('Text/JSON super metadata disagree')
    first_sector = int(block[1])
    parts = document.get('partitions', [])
    names = [p.get('name') for p in parts]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate JSON partition name')
    partition_table = text.split('Partition table:', 1)[1].split('Super partition layout:', 1)[0]
    entries = {}
    ranges = []
    for section in re.split(r'-{5,}', partition_table):
        name = re.search(r'^\s*Name: ([A-Za-z0-9_]+)\s*$', section, re.M)
        if not name:
            continue
        name = name[1]
        if name in entries:
            raise ValueError('Duplicate text partition name')
        if 'Attributes: readonly' not in section:
            raise ValueError('Partition is not declared readonly')
        extents = section.split('Extents:', 1)[1].strip().splitlines()
        if len(extents) != 1:
            raise ValueError('Multiple extents are unsupported; do not guess a loop offset')
        extent = re.fullmatch(r'\s*0 \.\. (\d+) linear super (\d+)\s*', extents[0])
        if not extent:
            raise ValueError('Expected one zero-based linear super extent')
        size = (int(extent[1]) + 1) * 512
        offset = int(extent[2]) * 512
        if offset < first_sector * 512 or size <= 0 or offset + size > super_size:
            raise ValueError('Extent outside super bounds')
        matches = [p for p in parts if p['name'] == name]
        if len(matches) != 1 or int(matches[0]['size']) != size or matches[0].get('is_dynamic') is not True:
            raise ValueError('Text/JSON partition metadata disagree')
        fs_size = int(matches[0].get('fs_size', size))
        if not 0 < fs_size <= size:
            raise ValueError('Filesystem exceeds its partition')
        entries[name] = {'offset': offset, 'size': size, 'fs_type': matches[0].get('fs_type')}
        ranges.append((offset, offset + size))
    if set(entries) != set(names):
        raise ValueError('Text/JSON partition sets disagree')
    ranges.sort()
    if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])):
        raise ValueError('Overlapping extents')
    if not all(n in entries and entries[n]['fs_type'] in ('ext4', 'erofs') for n in LEGACY):
        raise ValueError('Missing or unsupported system/vendor filesystem')
    return {'super_size': super_size, 'partitions': {n: entries[n] for n in LEGACY}}

def prepare(text_bytes, json_bytes, original):
    if hashlib.sha256(original).hexdigest() != REFERENCE_SHA256:
        raise ValueError('Historical mount script identity changed; review before generation')
    report = layout(text_bytes.decode('utf-8'), json.loads(json_bytes))
    script = original.decode('utf-8')
    for name, (old_offset, old_size) in LEGACY.items():
        old = 'mount_loop_ro "$super" "$' + name + '_mnt" ' + str(old_offset) + ' ' + str(old_size)
        if script.count(old) != 1:
            raise ValueError('Expected historical mount anchor not found exactly once')
        new = report['partitions'][name]
        replacement = 'mount_loop_ro "$super" "$' + name + '_mnt" ' + str(new['offset']) + ' ' + str(new['size'])
        script = script.replace(old, replacement, 1)
    report['reference_script_sha256'] = REFERENCE_SHA256
    report['lpdump_text_sha256'] = hashlib.sha256(text_bytes).hexdigest()
    report['lpdump_json_sha256'] = hashlib.sha256(json_bytes).hexdigest()
    report['candidate_script_sha256'] = hashlib.sha256(script.encode()).hexdigest()
    report['limits'] = ['Text-only candidate; no mount, mapping, flash or image build.',
                        'Re-read metadata after any Android OTA; this layout is not universal.',
                        'Android runtime/linker/vendor ABI and real Mobian startup remain unvalidated.']
    return script, report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lpdump-text', required=True, type=Path)
    parser.add_argument('--lpdump-json', required=True, type=Path)
    parser.add_argument('--reference-script', required=True, type=Path)
    parser.add_argument('--output-directory', required=True, type=Path)
    args = parser.parse_args()
    if args.output_directory.exists():
        parser.error('Refusing to overwrite an existing output directory')
    try:
        script, report = prepare(bounded_read(args.lpdump_text, 131072),
                                 bounded_read(args.lpdump_json, 131072),
                                 bounded_read(args.reference_script, 32768))
    except (ValueError, KeyError, IndexError, UnicodeError) as exc:
        parser.error(str(exc))
    args.output_directory.mkdir(parents=True, exist_ok=False)
    out = args.output_directory / 'lmi-android-wifi-mounts'
    out.write_bytes(script.encode('utf-8'))
    out.chmod(0o755)
    (args.output_directory / 'LAYOUT.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
