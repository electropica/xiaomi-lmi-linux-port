#!/usr/bin/env python3
"""Export the historical Android-working recipe; build only with --build."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

BASELINE = '78e8328dfb09bbbce109bd0a4accf8561d44af94'
REPO = Path('/home/linuxagent/xiaomi-lmi-linux-port')
DEST = Path('/home/linuxagent/lmi-reset-baseline-recipe')
digest = lambda b: hashlib.sha256(b).hexdigest()


def recipe_files():
    paths = subprocess.check_output(['git', '-C', str(REPO), 'ls-tree', '-r',
                                     '--name-only', BASELINE, '--',
                                     'build/boot-menu/'], text=True).splitlines()
    files = {}
    for path in paths:
        relative = str(Path(path).relative_to('build/boot-menu'))
        files[relative] = subprocess.check_output(['git', '-C', str(REPO),
                                                  'show', BASELINE + ':' + path])
    inner = files['build-inside.sh'].decode().replace('\r\n', '\n')
    old = 'bash build.sh --device lmi --toolchain CLANG38 --release RELEASE --outputdir /output'
    assert inner.count(old) == 1
    inner = inner.replace(old, 'python3 -B /recipe/reset-guard/run-guarded-build.py')
    files['build-inside.sh'] = inner.encode()
    for name in ['patch-reset.py', 'run-guarded-build.py']:
        files['reset-guard/' + name] = (Path(__file__).parent / name).read_bytes()
    return files


def prepare():
    files = recipe_files()
    if DEST.is_symlink():
        raise RuntimeError('Refusing symlink recipe directory')
    for relative, raw in files.items():
        target = DEST / relative
        if target.exists():
            if target.is_symlink() or target.read_bytes() != raw:
                raise RuntimeError('Existing snapshot differs: ' + relative)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(raw)
    expected = set(files) | {'reset-baseline-manifest.json'}
    actual = {str(p.relative_to(DEST)) for p in DEST.rglob('*') if p.is_file()}
    if actual - expected:
        raise RuntimeError('Unexpected files in snapshot')
    manifest = {'baseline_commit': BASELINE,
                'files': {name: digest(raw) for name, raw in sorted(files.items())},
                'firmware_built': False}
    (DEST / 'reset-baseline-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    subprocess.run(['bash', '-n', str(DEST / 'build.sh')], check=True)
    subprocess.run(['bash', '-n', str(DEST / 'build-inside.sh')], check=True)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()
    prepare()
    print('PINNED_32MIB_RECIPE_PREPARED_NO_PHONE_CONTACT', flush=True)
    if args.build:
        subprocess.run(['bash', str(DEST / 'build.sh'), '--build', '--with-lineage'], check=True)
        output = Path('/home/linuxagent/lmi-boot-menu-build/output')
        guard = json.loads((output / 'reset-guard-manifest.json').read_text())
        assert guard['restored'] and guard['builder_exit'] == 0
        image = output / 'boot-lmi-lineage-test.img'
        named = output / 'boot-lmi-lineage-resetguard1.img'
        shutil.copyfile(image, named)
        artifact = json.loads((output / 'lineage-artifact-manifest.json').read_text())
        assert digest(named.read_bytes()) == artifact['sha256']
        artifact.update({'candidate_variant': guard['variant'],
                         'baseline_commit': BASELINE,
                         'reset_source': guard, 'hardware_validated': False})
        (output / 'lineage-resetguard1-artifact-manifest.json').write_text(json.dumps(artifact, indent=2) + '\n')
        print('RESET_GUARD_BASELINE_BUILD_COMPLETE_NOT_FOR_FLASHING')
        print('IMAGE=' + str(named))
        print('SHA256=' + artifact['sha256'])
