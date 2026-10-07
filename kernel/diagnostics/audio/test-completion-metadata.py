#!/usr/bin/env python3
"""Test completion gates without invoking a builder, chroot or device.

Run as root to additionally exercise a private root-owned state against an
unprivileged reader. No sudo policy or interactive authentication is changed.
"""
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    wrapper = Path(__file__).with_name('build-audio-swr-reset-gpio-diagnostic-boot.sh')
    text = wrapper.read_text()
    functions = text[text.index('completion_valid() {'):text.index('cleanup() {')]
    command = functions + '\nset -Eeuo pipefail\nverify_inner_completion "$@"'
    count = 0
    with tempfile.TemporaryDirectory(prefix='lmi-completion-test-') as tmp:
        base = Path(tmp)
        base.chmod(0o755)
        state = base / 'private-state'
        state.mkdir(mode=0o700)
        status = state / 'STATUS'
        output = base / 'boot.img'
        output.write_bytes(b'fixture; not a boot image')
        output.chmod(0o600)

        def probe(mode='build', rc=0, expected=True, drop_privileges=None):
            nonlocal count
            result = subprocess.run(
                ['bash', '-c', command, '--', mode, str(rc), str(state), str(output)],
                capture_output=True, text=True, timeout=5,
                preexec_fn=drop_privileges,
            )
            assert (result.returncode == 0) == expected, result.stderr
            if expected:
                assert result.stdout.strip() == status.read_text().strip()
            count += 1

        status.write_text('COMPLETE\n')
        status.chmod(0o600)
        probe()
        probe(rc=1, expected=False)
        probe(mode='--check-only', expected=False)
        for value in ('RUNNING', 'INCOMPLETE exit=1', '', 'COMPLETE\nextra'):
            status.write_text(value + '\n')
            probe(expected=False)
        status.write_text('CHECK_ONLY_PASS\n')
        probe(mode='--check-only')
        probe(expected=False)
        status.write_text('COMPLETE\n')
        output.write_bytes(b'')
        probe(expected=False)
        output.unlink()
        probe(expected=False)
        target = base / 'target.img'
        target.write_bytes(b'fixture')
        output.symlink_to(target)
        probe(expected=False)
        output.unlink()
        output.write_bytes(b'fixture')
        status.unlink()
        probe(expected=False)
        status.symlink_to(target)
        probe(expected=False)
        status.unlink()
        status.write_text('COMPLETE\n')
        status.chmod(0o600)
        if os.geteuid() == 0:
            owner = wrapper.stat()
            # A repository owned by root does not provide an unprivileged UID.
            uid, gid = (owner.st_uid, owner.st_gid) if owner.st_uid else (65534, 65534)

            def drop():
                os.setgroups([])
                os.setgid(gid)
                os.setuid(uid)

            probe(expected=False, drop_privileges=drop)
            probe()
            assert state.stat().st_mode & 0o777 == 0o700
            assert status.stat().st_mode & 0o777 == 0o600
            print('Private root state: unprivileged read rejected; privileged verification passed')
        else:
            print('Root/non-root boundary test skipped: run explicitly as root to include it')
    print(f'PASS: {count} completion cases; no builder or hardware action')


if __name__ == '__main__':
    main()
