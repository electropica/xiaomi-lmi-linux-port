#!/usr/bin/env python3
"""Check marker interpretation against locked source and local text fixtures."""
from pathlib import Path
import hashlib
import importlib.util
import re
import sys
import tempfile

spec = importlib.util.spec_from_file_location('reader', Path(__file__).with_name('read-fg-profile-observer.py'))
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)

def fixture(**changes):
    fields = dict(candidate='j11sun_4700mah', integrity='0x09', prefix24_match=1,
                  full416_match=1, profile_status=3, force_load=1,
                  multi_profile=0, batt_id_ohms=99800)
    fields.update(changes)
    return ' '.join(f'{name}={value}' for name,value in fields.items())+'\n'

def rejects(text):
    try:
        reader.parse(text)
    except ValueError:
        return
    raise AssertionError('Invalid fixture accepted')

def main():
    data = Path(sys.argv[1]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == '0f5676829cb2a40daa191a456998c700d744afe8346e07dd3c7af2a7e8685957'
    source = data.decode()
    defines = {name:1<<int(bit) for name,bit in re.findall(r'^#define\s+(\w+)\s+BIT\((\d+)\)',source,re.M)}
    array = re.search(r'u8 white_list_values\[\] = \{(.*?)\};',source,re.S).group(1)
    whitelist = set()
    for entry in array.split(','):
        if not entry.strip():
            continue
        value = 0
        for name in entry.split('|'):
            value |= defines[name.strip()]
        whitelist.add(value)
    assert reader.INTEGRITY_WHITELIST == whitelist
    for mask in whitelist:
        result=reader.parse(fixture(integrity=hex(mask|1)))
        assert result['integrity_whitelisted'] and result['reviewed_reload_rule'] is False
    for marker in (0,1,65):
        result=reader.parse(fixture(integrity=hex(marker)))
        assert not result['integrity_whitelisted'] and result['reviewed_reload_rule'] is True
    assert reader.parse(fixture(prefix24_match=0,full416_match=0))['reviewed_reload_rule'] is True
    assert reader.parse(fixture(prefix24_match=0,full416_match=0,force_load=0))['reviewed_reload_rule'] is False
    assert reader.parse(fixture(full416_match=0))['reviewed_reload_rule'] is False
    assert 'unavailable' in reader.parse(fixture(multi_profile=1))['reviewed_reload_rule']
    for text in ('',fixture()+'integrity=0x09',fixture()+'unknown=1',fixture(candidate='other'),
                 fixture(prefix24_match=2),fixture(prefix24_match=0,full416_match=1),
                 fixture(integrity='0x100'),fixture(batt_id_ohms=-1),fixture(force_load='broken')):
        rejects(text)
    with tempfile.TemporaryDirectory(prefix='lmi-fg-reader-check-') as tmp:
        path=Path(tmp)/'attribute'
        text=fixture()
        path.write_text(text+' '*(4096-len(text)))
        assert reader.read(path)['full416_match'] == 1
        path.write_text(text+' '*(4097-len(text)))
        try: reader.read(path)
        except ValueError: pass
        else: raise AssertionError('Oversized attribute accepted')
        path.unlink()
        try: reader.read(path)
        except FileNotFoundError: pass
        else: raise AssertionError('Missing attribute accepted')
    print('PASS: exact driver whitelist, reload-rule boundaries, invalid output and bounded/missing attribute')
    print('Local fixtures only; no device read, profile loading or kernel build')

if __name__=='__main__':
    main()
