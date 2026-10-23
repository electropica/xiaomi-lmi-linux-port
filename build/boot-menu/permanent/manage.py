#!/usr/bin/env python3
"""Pinned dualboot operator tool. Default is offline plan; never touches userdata."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import struct
import subprocess
import sys

MENU_SHA = 'be9841c76cbe34d0c72606c47877f99582aee224144744349a9e78d15cfd0a94'
MENU_BYTES = 81051648
RESCUE_SHA = '75bb65facbd4146d4a1e668039ef52433ef90c2b6bdb07f2c59980caf3191374'
RESCUE_BYTES = 54652928
HERE = Path(__file__).resolve().parent
RECEIPT = HERE / 'private-state' / 'dual-extent' / 'validation.json'
RECORDS = HERE / 'private-state' / 'dual-extent'
ENTRIES = ('mobian-default', 'lineageos', 'fastboot', 'recovery')


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def pinned(path, digest, length):
    data = path.read_bytes()
    if len(data) != length or hashlib.sha256(data).hexdigest() != digest:
        raise RuntimeError('Pinned image mismatch: ' + path.name)
    if data[:8] != b'ANDROID!':
        raise RuntimeError('Invalid Android boot header.')
    return data


def host_preflight(downloads):
    menu = downloads / 'lmi-menu-outer-dual-extent-20261023.img'
    rescue = downloads / 'mobian-lmi-dualboot-boot-20261021.img'
    fastboot = downloads / 'platform-tools' / 'fastboot.exe'
    raw = pinned(menu, MENU_SHA, MENU_BYTES)
    pinned(rescue, RESCUE_SHA, RESCUE_BYTES)
    if struct.unpack_from('<II', raw, 40) != (1, 536871337):
        raise RuntimeError('Unexpected menu boot-header version/OS identity.')
    if struct.unpack_from('<I', raw, 16)[0] != 55054349:
        raise RuntimeError('Unexpected outer ramdisk size.')
    if not fastboot.is_file():
        raise RuntimeError('Native Windows fastboot.exe missing.')
    return menu, rescue, fastboot


def command(args, timeout=30):
    p = subprocess.run([str(a) for a in args], capture_output=True,
                       text=True, timeout=timeout)
    if p.returncode:
        raise RuntimeError('Fastboot command failed:\n' + p.stdout + p.stderr)
    return p.stdout + p.stderr


def fastboot_preflight(fastboot, run=command):
    rows = [line.split() for line in run([fastboot, 'devices']).splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) < 2 or rows[0][1] != 'fastboot':
        raise RuntimeError('Exactly one Fastboot device required; no write performed.')
    base = [fastboot, '-s', rows[0][0]]
    product = run(base + ['getvar', 'product'])
    if not any(line.strip() == 'product: lmi' for line in product.splitlines()):
        raise RuntimeError('Product lmi not confirmed; no write performed.')
    for name, expected in [('boot', 134217728), ('mobian', 17179869184)]:
        text = run(base + ['getvar', 'partition-size:' + name])
        prefix = 'partition-size:' + name + ':'
        lines = [line.strip() for line in text.splitlines() if line.strip().startswith(prefix)]
        if len(lines) != 1 or int(lines[0][len(prefix):].strip(), 16) != expected:
            raise RuntimeError('Unexpected ' + name + ' size; no write performed.')
    return base


def load_receipt(path=RECEIPT):
    if not path.exists():
        return {'schema': 1, 'menu_sha256': MENU_SHA, 'entries': {}}
    value = json.loads(path.read_text(encoding='utf-8'))
    if value.get('schema') != 1 or value.get('menu_sha256') != MENU_SHA:
        raise RuntimeError('Validation receipt belongs to another candidate.')
    return value


def save_receipt(value):
    RECORDS.mkdir(parents=True, exist_ok=True)
    temporary = RECEIPT.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(RECEIPT)


def require_qualified(value):
    proof = value.get('mobian_proof') or {}
    if (proof.get('menu_sha256') != MENU_SHA or not proof.get('direct_marker')
            or not proof.get('dedicated_root_confirmed')):
        raise RuntimeError('Direct Mobian runtime proof missing. Installation refused.')
    missing = [name for name in ENTRIES if not value.get('entries', {}).get(name, {}).get('passed')]
    if missing:
        raise RuntimeError('Unvalidated menu outcomes: ' + ', '.join(missing))


def install(downloads, value, run=command):
    # Qualification is checked BEFORE any device command, even a read.
    require_qualified(value)
    menu, rescue, fastboot = host_preflight(downloads)
    base = fastboot_preflight(fastboot, run)
    # Only boot is written. Do not reboot after a failed flash or retry it.
    output = run(base + ['flash', 'boot', menu], timeout=180)
    RECORDS.mkdir(parents=True, exist_ok=True)
    record = {'utc': stamp(), 'menu_sha256': MENU_SHA,
              'partition': 'boot', 'flash_output': output,
              'readback_verified': False, 'automatic_reboot': False,
              'rescue_sha256': RESCUE_SHA}
    filename = 'install-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json'
    (RECORDS / filename).write_text(json.dumps(record, indent=2), encoding='utf-8')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', default='plan',
                        choices=['plan', 'check-fastboot', 'record-outcome', 'install'])
    parser.add_argument('--downloads', type=Path, default=Path.home() / 'Downloads')
    parser.add_argument('--entry', choices=ENTRIES)
    parser.add_argument('--evidence', help='operator observation, after an actual temporary trial')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    menu, rescue, fastboot = host_preflight(args.downloads)
    receipt = load_receipt()
    if args.action == 'plan':
        print('HOST_IMAGES_VERIFIED. No phone contact.')
        print('Pending outcomes:', ', '.join(name for name in ENTRIES
              if not receipt.get('entries', {}).get(name, {}).get('passed')) or 'none')
        print('After qualification only: fastboot flash boot', menu)
        print('Then manual reboot: fastboot reboot')
        print('Rescue RAM boot: fastboot boot', rescue)
        print('Rescue persistent boot: fastboot flash boot', rescue)
        print('No filesystem, userdata, recovery, super or GPT operation is part of this plan.')
        return 0
    if not args.execute:
        raise RuntimeError('Explicit --execute required; nothing performed.')
    if args.action == 'check-fastboot':
        fastboot_preflight(fastboot)
        print('FASTBOOT_PRODUCT_AND_PARTITION_SIZES_VERIFIED. No write.')
    elif args.action == 'record-outcome':
        if not args.entry or not args.evidence:
            raise RuntimeError('Entry and actual operator evidence required.')
        if not receipt.get('temporary_launch'):
            raise RuntimeError('No matching temporary launch recorded; outcome refused.')
        receipt.setdefault('entries', {})[args.entry] = {
            'passed': True, 'utc': stamp(), 'evidence': args.evidence,
            'type': 'operator-confirmed', 'candidate_sha256': MENU_SHA}
        save_receipt(receipt)
        print('OUTCOME_RECORDED. This does not itself qualify hardware or perform a flash.')
    else:
        print(install(args.downloads, receipt))
        print('BOOT_FLASH_COMPLETED. Not read-back verified. Reboot manually, then verify runtime and boot readback.')


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print('STOP:', str(exc), file=sys.stderr)
        raise SystemExit(1)
