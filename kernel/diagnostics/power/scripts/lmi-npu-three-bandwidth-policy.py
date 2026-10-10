#!/usr/bin/env python3
"""Guarded, temporary isolation of three reviewed lmi NPU bandwidth clients.

This helper does not control NPU power, clocks or regulators. Apply must be
managed by a bounded trial unit with an independent ExecStopPost restoration.
"""
import argparse
import json
import os
import re
from pathlib import Path
import subprocess

BASELINES = {'soc:qcom,npu-npu-llcc-bw': '15258', 'soc:qcom,npu-llcc-ddr-bw': '10437', 'soc:qcom,npudsp-npu-ddr-bw': '10437'}
FIELDS = ('governor', 'min_freq', 'max_freq', 'cur_freq', 'available_governors')


def inspect(io):
    state = {name: io.read(name) for name in FIELDS}
    if state['governor'] != 'performance':
        raise RuntimeError('Original governor must be performance')
    if state['min_freq'] != '0' or state['max_freq'] != io.expected_max:
        raise RuntimeError('Bandwidth limits differ from reviewed baseline')
    if state['cur_freq'] != io.expected_max:
        raise RuntimeError('Original software target differs from baseline')
    if 'powersave' not in state['available_governors'].split():
        raise RuntimeError('powersave is unavailable')
    return state


def restore(io, original):
    if original.get('governor') != 'performance' or original.get('min_freq') != '0' or original.get('max_freq') != io.expected_max:
        raise RuntimeError('Unreviewed restoration state')
    if io.read('min_freq') != original['min_freq'] or io.read('max_freq') != original['max_freq']:
        raise RuntimeError('Limits changed externally; do not overwrite them')
    current = io.read('governor')
    if current not in ('powersave', original['governor']):
        raise RuntimeError('Governor changed externally; do not overwrite it')
    if current != original['governor']:
        io.write_governor(original['governor'])
    if io.read('governor') != original['governor'] or io.read('cur_freq') != original['cur_freq']:
        raise RuntimeError('Original governor/target restoration unconfirmed')


def apply(io, save):
    original = inspect(io)
    # Save and fsync before the first mutable operation. Failure means no write.
    save(original)
    try:
        io.write_governor('powersave')
        if io.read('governor') != 'powersave' or io.read('cur_freq') != '0':
            raise RuntimeError('Isolated client did not reach target zero')
    except BaseException:
        restore(io, original)
        raise
    return original


class SysfsNode:
    def __init__(self, name):
        if name not in BASELINES: raise RuntimeError('Unreviewed client')
        self.node = Path('/sys/class/devfreq') / name
        self.expected_max = BASELINES[name]
        self.path = self.node.resolve(strict=True)
        if not str(self.path).startswith('/sys/devices/'):
            raise RuntimeError('Unexpected devfreq device path')

    def read(self, name):
        if name not in FIELDS:
            raise RuntimeError('Unreviewed attribute')
        return (self.path / name).read_text().strip()

    def write_governor(self, value):
        if value not in ('performance', 'powersave') or self.node.resolve(strict=True) != self.path:
            raise RuntimeError('Unexpected governor or changed device binding')
        (self.path / 'governor').write_text(value + '\n')


def state_path(value):
    p = Path(value)
    if not p.is_absolute() or p.parent.resolve() != Path('/var/tmp') or not re.fullmatch(r'lmi-npu-bandwidth-[A-Za-z0-9_.-]+\.json', p.name):
        raise ValueError('Use a private /var/tmp/lmi-npu-bandwidth-*.json state')
    return p


def verify_managed_settings(active, runtime_us, hooks, expected):
    if active != 'active' or type(runtime_us) is not int or not 0 < runtime_us <= 900_000_000:
        raise RuntimeError('Trial unit is not active and bounded to fifteen minutes')
    # Typed D-Bus argv preserves argument boundaries; no substring matching.
    if len(hooks) != 1 or len(hooks[0]) != 10:
        raise RuntimeError('Exactly one typed restoration hook is required')
    hook = hooks[0]
    if hook[0] != '/usr/bin/python3' or hook[1] != expected or hook[2] is not False:
        raise RuntimeError('ExecStopPost executable/argv or failure handling mismatch')


def dbus_value(command, expected_type):
    raw = subprocess.check_output(['busctl', '--json=short', *command], text=True, timeout=5)
    result = json.loads(raw)
    if result.get('type') != expected_type or 'data' not in result:
        raise RuntimeError('Unexpected typed systemd property response')
    return result['data']


def verify_managed_unit(name, state):
    response = dbus_value(['call', 'org.freedesktop.systemd1', '/org/freedesktop/systemd1', 'org.freedesktop.systemd1.Manager', 'GetUnit', 's', name], 'o')
    if len(response) != 1 or not isinstance(response[0], str):
        raise RuntimeError('Unexpected trial unit identity')
    path = response[0]
    prefix = ['get-property', 'org.freedesktop.systemd1', path]
    active = dbus_value([*prefix, 'org.freedesktop.systemd1.Unit', 'ActiveState'], 's')
    runtime = dbus_value([*prefix, 'org.freedesktop.systemd1.Service', 'RuntimeMaxUSec'], 't')
    hooks = dbus_value([*prefix, 'org.freedesktop.systemd1.Service', 'ExecStopPost'], 'a(sasbttttuii)')
    expected = ['/usr/bin/python3', str(Path(__file__).resolve()), 'restore', '--state', str(state)]
    verify_managed_settings(active, runtime, hooks, expected)


def ensure_quiet():
    if Path('/sys/class/power_supply/usb/online').read_text().strip() != '1':
        raise RuntimeError('Apply while USB is connected')
    device = Path('/dev/msm_npu')
    if device.exists():
        p = subprocess.run(['fuser', str(device)], capture_output=True, timeout=5)
        if p.returncode != 1:
            raise RuntimeError('NPU device is in use or quiescence check failed')


def load_original(p, device):
    if not p.exists():
        raise RuntimeError('Restoration state missing; no restoration success claimed')
    if p.is_symlink() or not p.is_file() or p.stat().st_uid != 0:
        raise RuntimeError('Unexpected private state ownership/type')
    state = json.loads(p.read_text())
    if state.get('version') != 1 or state.get('device') != str(device):
        raise RuntimeError('Restoration device/state mismatch')
    return state['original']


def restore_all(nodes, originals):
    failures=[]
    for name,io in nodes.items():
        try: restore(io,originals[name])
        except BaseException as exc: failures.append(name+': '+str(exc))
    if failures: raise RuntimeError('Restoration failures: '+'; '.join(failures))


def apply_all(nodes, save):
    originals={name:inspect(io) for name,io in nodes.items()}
    save(originals)
    try:
        for io in nodes.values():
            io.write_governor('powersave')
            if io.read('governor')!='powersave' or io.read('cur_freq')!='0':
                raise RuntimeError('Client target did not reach zero')
    except BaseException:
        restore_all(nodes,originals)
        raise
    return originals


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('preflight','apply','restore'))
    parser.add_argument('--state');parser.add_argument('--managed-unit')
    args=parser.parse_args()
    if os.geteuid()!=0:raise SystemExit('Run on phone as root')
    nodes={name:SysfsNode(name) for name in BASELINES}
    if args.mode=='preflight':
        ensure_quiet();print(json.dumps({n:inspect(io) for n,io in nodes.items()}));return
    if not args.state:parser.error('--state required')
    p=state_path(args.state)
    if args.mode=='restore':
        if not p.exists() or p.is_symlink() or not p.is_file() or p.stat().st_uid!=0:
            raise RuntimeError('Private recovery state missing or invalid')
        saved=json.loads(p.read_text())
        expected={n:str(io.path) for n,io in nodes.items()}
        if saved.get('version')!=2 or saved.get('devices')!=expected or set(saved.get('originals',{}))!=set(nodes):
            raise RuntimeError('Recovery device set mismatch')
        restore_all(nodes,saved['originals']);print('ALL_ORIGINAL_GOVERNORS_AND_TARGETS_RESTORED');return
    ensure_quiet()
    if not args.managed_unit or not re.fullmatch(r'lmi-npu-bandwidth-trial[A-Za-z0-9_-]+\.service',args.managed_unit):
        parser.error('Bounded managed trial unit required')
    verify_managed_unit(args.managed_unit,p)
    def save(originals):
        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as f:
            json.dump({'version':2,'devices':{n:str(io.path) for n,io in nodes.items()},'originals':originals},f)
            f.flush();os.fsync(f.fileno())
        directory=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    apply_all(nodes,save);print('ALL_THREE_NPU_SOFTWARE_TARGETS_ZERO')


if __name__=='__main__':main()
