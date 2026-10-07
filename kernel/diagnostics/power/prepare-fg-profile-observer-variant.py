#!/usr/bin/env python3
"""Prepare a private FG profile observer; never build, boot or load a profile."""
import argparse
import hashlib
from pathlib import Path
import subprocess

PATCH_SHA = 'ec86f4cb13d7efe78f3dfcddbe6771c09373b24b2ab868d05e04f2261de80440'
EXTRA = [('P6="$ROOT/patches/lmi-rpmh-vote-observer-unvalidated.patch"', 'P6="$ROOT/patches/lmi-rpmh-vote-observer-unvalidated.patch"\nP7="$ROOT/patches/lmi-fg-profile-observer-unvalidated.patch"\nEXPECTED_FG_OBSERVER=ec86f4cb13d7efe78f3dfcddbe6771c09373b24b2ab868d05e04f2261de80440'), ('sha_is "$EXPECTED_VOTES" "$P6"', 'sha_is "$EXPECTED_VOTES" "$P6"\n\tsha_is "$EXPECTED_FG_OBSERVER" "$P7"'), ('python3 - "$ARCHIVE" "$SRC" "$P1" "$P2" "$P" "$P4" "$P5" "$P6"', 'python3 - "$ARCHIVE" "$SRC" "$P1" "$P2" "$P" "$P4" "$P5" "$P6" "$P7"'), ('for patchfile in "$P1" "$P2" "$P" "$P4" "$P5" "$P6"; do', 'for patchfile in "$P1" "$P2" "$P" "$P4" "$P5" "$P6" "$P7"; do'), ('(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P6")\n', '(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P6")\n\t\t(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P7")\n'), ('\npatch --batch --fuzz=0 -p1 -d "$STATE/src" <"$P6" >"$STATE/patch-rpmh-votes.log" 2>&1 || die \'RPMh observer patch failed; see patch-rpmh-votes.log\'', '\npatch --batch --fuzz=0 -p1 -d "$STATE/src" <"$P6" >"$STATE/patch-rpmh-votes.log" 2>&1 || die \'RPMh observer patch failed; see patch-rpmh-votes.log\'\npatch --batch --fuzz=0 -p1 -d "$STATE/src" <"$P7" >"$STATE/patch-fg-profile-observer.log" 2>&1 || die \'FG observer patch failed; see patch-fg-profile-observer.log\'')]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    here = Path(__file__).resolve().parent
    patch = root / 'kernel/patches/diagnostics/lmi-fg-profile-observer-unvalidated.patch'
    data = patch.read_bytes()
    if hashlib.sha256(data).hexdigest() != PATCH_SHA:
        raise SystemExit('Observer patch identity mismatch')
    subprocess.run(['python3', str(here / 'prepare-rpmh-vote-observer-variant.py'),
                    '--output-directory', args.output_directory], check=True, timeout=60)
    out = Path(args.output_directory).absolute()
    wrapper = out / 'build-audio-swr-reset-gpio-diagnostic-boot.sh'
    text = wrapper.read_text()
    anchor = 'for old, new in repls:'
    if text.count(anchor) != 1:
        raise SystemExit('Unexpected wrapper derivation anchor')
    text = text.replace(anchor, 'repls += ' + repr(EXTRA) + '\n' + anchor, 1)
    old_name = 'D-repro-01-power-rpmh-votes-diagnostic-boot.img'
    if text.count(old_name) != 2:
        raise SystemExit('Unexpected output-name anchors')
    wrapper.write_text(text.replace(old_name, 'D-repro-01-power-fg-profile-observer-diagnostic-boot.img'))
    (out / 'patches/lmi-fg-profile-observer-unvalidated.patch').write_bytes(data)
    subprocess.run(['bash', '-n', str(wrapper)], check=True, timeout=10)
    names = [line.split('  ', 1)[1] for line in (out / 'SHA256SUMS').read_text().splitlines()]
    names.append('patches/lmi-fg-profile-observer-unvalidated.patch')
    (out / 'SHA256SUMS').write_text(''.join(hashlib.sha256((out / n).read_bytes()).hexdigest() + '  ' + n + '\n' for n in names))
    print('PREPARED_ONLY=' + str(out))
    print('UNVALIDATED_FG_OBSERVER; lookup fix and retry candidate excluded; no hardware action')

if __name__ == '__main__':
    main()
