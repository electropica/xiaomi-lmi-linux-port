#!/usr/bin/env python3
"""Read one guarded diagnostic attribute; never load profiles or poll hardware."""
import argparse
import json
from pathlib import Path

FIELDS = {'candidate', 'integrity', 'prefix24_match', 'full416_match',
          'profile_status', 'force_load', 'multi_profile', 'batt_id_ohms'}
# The locked driver's integrity whitelist after stripping PROFILE_LOAD_BIT.
INTEGRITY_WHITELIST = {8, 2, 2 | 4, 4 | 8, 2 | 16, 2 | 4 | 16, 8 | 4 | 16}

def parse(text):
    raw = {}
    for token in text.split():
        name, separator, value = token.partition('=')
        if not separator or name not in FIELDS or name in raw:
            raise ValueError('Unexpected, duplicate or malformed observer field')
        raw[name] = value
    if set(raw) != FIELDS or raw['candidate'] != 'j11sun_4700mah':
        raise ValueError('Incomplete or unsupported observer output')
    result = {'candidate': raw.pop('candidate')}
    for name, value in raw.items():
        result[name] = int(value, 16 if name == 'integrity' else 10)
    for name in ('prefix24_match', 'full416_match', 'force_load', 'multi_profile'):
        if result[name] not in (0, 1):
            raise ValueError('Invalid boolean observer field')
    if not 0 <= result['integrity'] <= 255 or result['batt_id_ohms'] < 0:
        raise ValueError('Invalid integrity marker or battery ID')
    if result['full416_match'] and not result['prefix24_match']:
        raise ValueError('Full equality without prefix equality is inconsistent')
    marker = result['integrity']
    result['loaded_marker_set'] = bool(marker & 1)
    result['integrity_whitelisted'] = bool(marker & 1) and (marker & ~1) in INTEGRITY_WHITELIST
    if result['multi_profile']:
        result['reviewed_reload_rule'] = {'unavailable': 'Age-level state not captured for multi-profile mode'}
    else:
        result['reviewed_reload_rule'] = (
            not result['loaded_marker_set'] or
            not result['integrity_whitelisted'] or
            (not result['prefix24_match'] and bool(result['force_load']))
        )
    result['limits'] = [
        'One connected read, not an atomic whole-profile sample or a standby-current measurement.',
        'Reviewed reload rule is an interpretation; the diagnostic guard blocks the reload-required branch.',
        'Profile equality does not establish physical capacity, health or lower consumption.',
    ]
    return result

def read(path):
    with path.open('r') as stream:
        text = stream.read(4097)
    if len(text) > 4096:
        raise ValueError('Oversized observer output')
    return parse(text)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attribute', type=Path, default=Path('/sys/class/power_supply/bms/device/lmi_fg_profile'))
    args = parser.parse_args()
    try:
        result = read(args.attribute)
    except (OSError, ValueError) as error:
        result = {'unavailable': type(error).__name__, 'errno': getattr(error, 'errno', None), 'message': str(error)}
    print(json.dumps(result, indent=2))
    return int('unavailable' in result)

if __name__ == '__main__':
    raise SystemExit(main())
