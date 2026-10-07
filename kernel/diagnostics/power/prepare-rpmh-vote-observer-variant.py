#!/usr/bin/env python3
"""Prepare an unvalidated read-only RPMh observer; never build or boot."""
import argparse,hashlib,subprocess
from pathlib import Path

PATCH_SHA='ea19e7e6aa5d4d8915e1fbab5ce00addf3a49df02c6b7cc104c395b2f49581ab'
EXTRA=[('P5="$ROOT/patches/lmi-dsi-powerdown-notifier-unvalidated.patch"', 'P5="$ROOT/patches/lmi-dsi-powerdown-notifier-unvalidated.patch"\nP6="$ROOT/patches/lmi-rpmh-vote-observer-unvalidated.patch"\nEXPECTED_VOTES=ea19e7e6aa5d4d8915e1fbab5ce00addf3a49df02c6b7cc104c395b2f49581ab'), ('sha_is "$EXPECTED_TOUCH" "$P5"', 'sha_is "$EXPECTED_TOUCH" "$P5"\n\tsha_is "$EXPECTED_VOTES" "$P6"'), ('python3 - "$ARCHIVE" "$SRC" "$P1" "$P2" "$P" "$P4" "$P5"', 'python3 - "$ARCHIVE" "$SRC" "$P1" "$P2" "$P" "$P4" "$P5" "$P6"'), ('for patchfile in "$P1" "$P2" "$P" "$P4" "$P5"; do', 'for patchfile in "$P1" "$P2" "$P" "$P4" "$P5" "$P6"; do'), ('(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P5")\n', '(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P5")\n\t\t(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P6")\n'), ('\npatch --batch --fuzz=0 -p1 -d "$STATE/src" <"$P5" >"$STATE/patch-touch-notifier.log" 2>&1 || die \'touch notifier patch failed; see patch-touch-notifier.log\'', '\npatch --batch --fuzz=0 -p1 -d "$STATE/src" <"$P5" >"$STATE/patch-touch-notifier.log" 2>&1 || die \'touch notifier patch failed; see patch-touch-notifier.log\'\npatch --batch --fuzz=0 -p1 -d "$STATE/src" <"$P6" >"$STATE/patch-rpmh-votes.log" 2>&1 || die \'RPMh observer patch failed; see patch-rpmh-votes.log\'')]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-directory',required=True)
    args=p.parse_args()
    root=Path(__file__).resolve().parents[3]
    here=Path(__file__).resolve().parent
    patch=root/'kernel/patches/diagnostics/lmi-rpmh-vote-observer-unvalidated.patch'
    data=patch.read_bytes()
    if hashlib.sha256(data).hexdigest()!=PATCH_SHA:
        raise SystemExit('Observer patch identity mismatch')
    subprocess.run(['python3',str(here/'prepare-touch-notifier-variant.py'),
                    '--output-directory',args.output_directory],check=True)
    out=Path(args.output_directory).absolute()
    wrapper=out/'build-audio-swr-reset-gpio-diagnostic-boot.sh'
    text=wrapper.read_text()
    anchor='for old, new in repls:'
    if text.count(anchor)!=1:raise SystemExit('Unexpected wrapper derivation anchor')
    text=text.replace(anchor,'repls += '+repr(EXTRA)+'\n'+anchor,1)
    name='D-repro-01-power-touch-notifier-diagnostic-boot.img'
    if text.count(name)!=2:raise SystemExit('Unexpected output name count')
    wrapper.write_text(text.replace(name,'D-repro-01-power-rpmh-votes-diagnostic-boot.img'))
    (out/'patches/lmi-rpmh-vote-observer-unvalidated.patch').write_bytes(data)
    subprocess.run(['bash','-n',str(wrapper)],check=True)
    names=[line.split('  ',1)[1] for line in (out/'SHA256SUMS').read_text().splitlines()]
    names.append('patches/lmi-rpmh-vote-observer-unvalidated.patch')
    (out/'SHA256SUMS').write_text(''.join(hashlib.sha256((out/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in names))
    print('PREPARED_ONLY='+str(out))
    print('UNVALIDATED_RPMH_OBSERVER; no build or hardware action')

if __name__=='__main__':main()
