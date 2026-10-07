#!/usr/bin/env python3
"""Check M1's staged app-file closure without an image, packages or device."""
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    repo = Path(__file__).resolve().parents[3]
    files = repo / 'userspace/apps/files'
    builder = (repo / 'userspace/phosh/scripts/build-m1-phosh.sh').read_text()
    installer = Path(__file__).with_name('install.sh').read_text()
    required = set(re.findall(r'"\$apps_files/([A-Za-z0-9_.-]+)"', installer))
    if not required:
        raise SystemExit('No installer app-file dependencies found; review parser scope')
    stages = []
    for line in builder.splitlines():
        match = re.match(r'\s*install -m (0?[0-7]{3}) (.+) "\$tree/run/lmi-app-files/"\s*$', line)
        if not match:
            continue
        sources = re.findall(r'"\$apps_dir/files/([A-Za-z0-9_.-]+)"', match.group(2))
        reconstructed = ' '.join('"$apps_dir/files/' + name + '"' for name in sources)
        if not sources or reconstructed != match.group(2):
            raise SystemExit('Unsupported staging expression; review parser scope')
        stages.extend((name, int(match.group(1), 8)) for name in sources)
    names = [name for name, mode in stages]
    if len(names) != len(set(names)):
        raise SystemExit('Duplicate staged app files')
    missing = sorted(required - set(names))
    if missing:
        raise SystemExit('Missing from M1 app staging: ' + ', '.join(missing))
    with tempfile.TemporaryDirectory(prefix='lmi-app-staging-check-') as tmp:
        destination = Path(tmp)
        for name, mode in stages:
            source = files / name
            if not source.is_file() or source.is_symlink():
                raise SystemExit('Missing or linked app source: ' + name)
            subprocess.run(['install', '-m', format(mode, '04o'), str(source), str(destination / name)], check=True, timeout=5)
            staged = destination / name
            assert staged.read_bytes() == source.read_bytes(), name
            assert staged.stat().st_mode & 0o777 == mode, name
    print(f'PASS: {len(required)} installer dependencies staged; content and modes match')
    print('No rootfs build, package install, launcher execution or phone access')


if __name__ == '__main__':
    main()
