#!/usr/bin/env python3
"""Default: scratch preflight. --execute: operator-only Phosh/GSD build, no phone."""
from pathlib import Path
import argparse
import fcntl
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from email.utils import formatdate

ROOT = Path('/home/linuxagent/phosh-gauge-wake-build/rootfs')
TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def header(spec, version):
    return f'{spec["package"]} ({version}) UNRELEASED; urgency=medium'


def verify_inputs(m):
    assert sha(TASK / 'irq-name.patch') == m['patch_sha256']
    assert sha(TASK / 'test-policy.c') == m['test_source_sha256']
    for item in m['reverse_ui']:
        assert sha(REPO / item['patch']) == item['sha256']
    states = []
    for s in m['files']:
        p = ROOT / 'build' / s['tree'] / s['file']
        assert p.is_file() and not p.is_symlink()
        digest = sha(p)
        assert digest in (s['input'], s['output']), str(p)
        states.append(digest == s['output'])
    assert all(states) or not any(states), 'Partial source preparation; inspect before retry'
    prepared = all(states)
    for s in m['packages']:
        tree = ROOT / 'build' / s['tree']
        h = (tree / 'debian/changelog').read_text(encoding='utf-8').splitlines()[0]
        assert h == header(s, s['new'] if prepared else s['input_version']), h
        for pkg, arch in [(s['package'], 'arm64'), (s['package'] + '-common', 'all')]:
            p = ROOT / 'build' / f'{pkg}_{s["rollback"]}_{arch}.deb'
            assert sha(p) == m['rollback_sha256'][p.name], str(p)
            for field, value in [('Version', s['rollback']), ('Architecture', arch)]:
                assert subprocess.check_output(['dpkg-deb', '-f', str(p), field], text=True).strip() == value
    for relative, digest in m['preserve'].items():
        assert sha(ROOT / 'build' / relative) == digest, relative
    return prepared


def stage(m, dest, prepared):
    for s in m['files']:
        target = dest / s['file']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'build' / s['tree'] / s['file'], target)
    if prepared:
        subprocess.run(['patch', '--batch', '--fuzz=0', '-R', '-p1', '-i', str(TASK / 'irq-name.patch')], cwd=dest, check=True)
    else:
        for item in m['reverse_ui']:
            subprocess.run(['patch', '--batch', '--fuzz=0', '-R', '-p1', '-i', str(REPO / item['patch'])], cwd=dest, check=True)
    for s in m['files']:
        assert sha(dest / s['file']) == s['accepted'], 'Accepted UI/policy baseline mismatch: ' + s['file']
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(TASK / 'irq-name.patch')], cwd=dest, check=True)
    for s in m['files']:
        assert sha(dest / s['file']) == s['output'], s['file']
    blocks = []
    for rel in ['src/screen-saver-manager.c', 'plugins/power/gsd-power-manager.c']:
        source = (dest / rel).read_text(encoding='utf-8')
        anchor = 'static gboolean\nlmi_quiet_reason_allowed (const char *reason)'
        start = source.index('static gboolean\nlmi_resume_reason_has_name')
        end = source.index('\nstatic gboolean\n', source.index(anchor) + len(anchor))
        blocks.append(source[start:end])
    assert blocks[0] == blocks[1]
    assert blocks[0] in (TASK / 'test-policy.c').read_text(encoding='utf-8'), 'Test harness differs from staged policy'


def payload(p, binary):
    data = subprocess.check_output(['dpkg-deb', '--fsys-tarfile', str(p)])
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as tf:
        members = tf.getmembers()
        listing = sorted((x.name, x.type.decode('ascii'), x.linkname) for x in members)
        if binary is None:
            return listing, None
        match = [x for x in members if x.name.lstrip('./') == binary]
        assert len(match) == 1 and match[0].isfile()
        return listing, tf.extractfile(match[0]).read()


def build(m):
    assert os.geteuid() == 0
    assert os.readlink('/proc/self/ns/mnt') != os.readlink('/proc/1/ns/mnt')
    subprocess.run(['python3', str(REPO / 'userspace/camera/snapshot-bundle/prepare-chroot.py'), str(ROOT)], check=True)
    (ROOT / 'dev/shm').mkdir(exist_ok=True)
    if subprocess.run(['mountpoint', '-q', str(ROOT / 'dev/shm')]).returncode:
        subprocess.run(['mount', '-t', 'tmpfs', '-o', 'mode=1777,nosuid,nodev,size=256m', 'tmpfs', str(ROOT / 'dev/shm')], check=True)
    assert subprocess.check_output(['chroot', str(ROOT), 'dpkg', '--print-architecture'], text=True).strip() == 'arm64'
    prepared = verify_inputs(m)
    with tempfile.TemporaryDirectory(prefix='lmi-irq-build-') as td:
        staged = Path(td)
        stage(m, staged, prepared)
        for s in m['files']:
            target = ROOT / 'build' / s['tree'] / s['file']
            shutil.copyfile(staged / s['file'], target)
            subprocess.run(['chroot', str(ROOT), 'chown', 'builder:builder', '/build/' + s['tree'] + '/' + s['file']], check=True)
        for s in m['packages']:
            tree = ROOT / 'build' / s['tree']
            p = tree / 'debian/changelog'
            if p.read_text(encoding='utf-8').splitlines()[0] != header(s, s['new']):
                entry = (header(s, s['new']) + '\n\n  * Match complete gauge event names independently of Linux IRQ numbering;\n'
                         '    retain the qualified drawerscroll1 UI and existing quiet guards.\n\n'
                         ' -- Local lmi <local@example.invalid>  ' + formatdate(localtime=False, usegmt=False) + '\n\n')
                p.write_text(entry + p.read_text(encoding='utf-8'), encoding='utf-8')
            subprocess.run(['chroot', str(ROOT), 'chown', 'builder:builder', '/build/' + s['tree'] + '/debian/changelog'], check=True)
            stamp = tree / 'debian/debhelper-build-stamp'
            assert not stamp.is_symlink()
            if stamp.exists():
                assert stamp.is_file()
                stamp.unlink()
        assert verify_inputs(m)
        for s in m['packages']:
            subprocess.run(['chroot', str(ROOT), '/bin/bash', '-c',
                            'set -euo pipefail; export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin; cd "$1"; '
                            'runuser -u builder -- env DEBIAN_FRONTEND=noninteractive DEB_BUILD_OPTIONS=parallel=2 dpkg-buildpackage -b -nc -us -uc -j2',
                            'bash', '/build/' + s['tree']], check=True)
    assert verify_inputs(m)
    packages = []
    for s in m['packages']:
        for pkg, arch in [(s['package'], 'arm64'), (s['package'] + '-common', 'all')]:
            p = ROOT / 'build' / f'{pkg}_{s["new"]}_{arch}.deb'
            old = ROOT / 'build' / f'{pkg}_{s["rollback"]}_{arch}.deb'
            for field, value in [('Version', s['new']), ('Architecture', arch)]:
                assert subprocess.check_output(['dpkg-deb', '-f', str(p), field], text=True).strip() == value
            binary = {'phosh': 'usr/libexec/phosh', 'gnome-settings-daemon': 'usr/libexec/gsd-power'}.get(pkg)
            listing, content = payload(p, binary)
            oldlisting, oldcontent = payload(old, binary)
            assert listing == oldlisting, 'Package file/type/link list changed'
            record = {'path': str(p), 'sha256': sha(p), 'version': s['new'], 'architecture': arch,
                      'rollback_path': str(old), 'rollback_sha256': sha(old), 'file_list_unchanged': True}
            if binary:
                assert content != oldcontent
                assert all(x.encode() in content for x in ['msoc-delta', 'msoc-high', 'esr-delta'])
                assert not any(x.encode() in content for x in ['438 msoc-delta', '441 msoc-high', '445 esr-delta'])
                record.update(binary_path=binary, binary_sha256=hashlib.sha256(content).hexdigest(),
                              rollback_binary_sha256=hashlib.sha256(oldcontent).hexdigest())
            packages.append(record)
    result = {'packages': packages, 'identity': m, 'phone_contact': False, 'hardware_validated': False}
    (ROOT / 'build/lmi-irqnames1-build-result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('IRQ_NAME_PACKAGES_BUILT\nNo phone installation, kernel or image build performed.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--inside', action='store_true', help=argparse.SUPPRESS)
    args = ap.parse_args()
    m = json.loads((TASK / 'identity.json').read_text(encoding='utf-8'))
    prepared = verify_inputs(m)
    assert shutil.disk_usage(ROOT).free > 2 * 1024**3
    assert Path('/proc/sys/fs/binfmt_misc/qemu-aarch64').is_file()
    with tempfile.TemporaryDirectory(prefix='lmi-irq-preflight-') as td:
        stage(m, Path(td), prepared)
    print('IRQ_NAME_PREFLIGHT_PASS: accepted UI reconstructed, policy patch and rollback packages verified', flush=True)
    if not args.execute:
        return
    assert os.geteuid() == 0, 'Run --execute with sudo'
    if args.inside:
        build(m)
        return
    locks = []
    for name in ['lmi-gsd-quiet-build.lock', 'lmi-phosh-gauge-build.lock']:
        f = open('/run/' + name, 'a')
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(f)
    subprocess.run(['unshare', '--mount', '--fork', '--propagation', 'private', sys.executable,
                    str(Path(__file__).resolve()), '--execute', '--inside'], check=True)


if __name__ == '__main__':
    main()
