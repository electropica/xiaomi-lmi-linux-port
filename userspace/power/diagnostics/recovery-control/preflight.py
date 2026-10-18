#!/usr/bin/env python3
"""Native Windows ADB recovery inspection. Never reboot, flash or alter policy."""
import argparse
import datetime
import json
import pathlib
import shlex
import subprocess


def decode(raw):
    if len(raw) > 65536:
        raise ValueError('Oversized preflight response')
    result = {}
    for line in raw.decode('ascii').splitlines():
        key, value = line.split('\t', 1)
        if key in result or not key or len(key) > 200:
            raise ValueError('Duplicate/invalid preflight key')
        result[key] = bytes.fromhex(value).decode('utf-8').strip()
    required = ['kernel', 'boot_id', 'supply:usb:online', 'power_state']
    if any(key not in result for key in required):
        raise ValueError('Incomplete preflight response')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', type=pathlib.Path, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; preserve previous evidence')
    adb = args.adb.resolve(strict=True)
    devices = subprocess.run([str(adb), 'devices'], capture_output=True,
                             check=True, timeout=12).stdout.decode('utf-8')
    attached = [line.split() for line in devices.splitlines()[1:] if line.strip()]
    if len(attached) != 1 or attached[0][1] not in ('recovery', 'device'):
        raise RuntimeError('Exactly one available recovery device is required')
    serial = attached[0][0]
    source = pathlib.Path(__file__).with_suffix('.sh').read_bytes().replace(b'\r\n', b'\n')
    response = subprocess.run([str(adb), '-s', serial, 'shell', '-T', 'sh', '-c',
                               shlex.quote(source.decode('utf-8'))],
                              capture_output=True, timeout=35)
    if response.returncode:
        raise RuntimeError(response.stderr.decode('utf-8', errors='replace'))
    values = decode(response.stdout)
    report = {
        'host_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'values': values,
        'limits': 'Read-only recovery preflight. No suspension or battery measurement performed.'
    }
    with args.output.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    print(json.dumps({key: values[key] for key in
                      ['kernel', 'supply:usb:online', 'power_state', 'mem_sleep']},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
