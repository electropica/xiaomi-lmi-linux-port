#!/usr/bin/env python3
"""Prepare an unvalidated private notification candidate; never build or boot."""
import argparse,hashlib,subprocess
from pathlib import Path

def once(text,old,new):
    if text.count(old)!=1:raise SystemExit('Unexpected derivation anchor: '+old[:80])
    return text.replace(old,new,1)

PATCH_SHA='2f6aa840ac77e3c46e5399b9bc3877471382ad6ae156c92980e83a20fff3b1c0'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-directory',required=True)
    args=p.parse_args()
    root=Path(__file__).resolve().parents[3]
    here=Path(__file__).resolve().parent
    patch=root/'kernel/patches/diagnostics/lmi-dsi-powerdown-notifier-unvalidated.patch'
    data=patch.read_bytes()
    if hashlib.sha256(data).hexdigest()!=PATCH_SHA:raise SystemExit('Candidate patch identity mismatch')
    subprocess.run(['python3',str(here/'prepare-debugfs-variant.py'),'--output-directory',args.output_directory],check=True)
    out=Path(args.output_directory).absolute()
    wrapper=out/'build-audio-swr-reset-gpio-diagnostic-boot.sh'
    text=wrapper.read_text()
    extra=[
        ('SRC=${AUDIO_DIAG_SOURCE_DIR:-$ROOT/source-a5b3099017ae}',
         'P5="$ROOT/patches/lmi-dsi-powerdown-notifier-unvalidated.patch"\nEXPECTED_TOUCH='+PATCH_SHA+'\nSRC=${AUDIO_DIAG_SOURCE_DIR:-$ROOT/source-a5b3099017ae}'),
        ('sha_is "$EXPECTED_DIAG" "$P"','sha_is "$EXPECTED_DIAG" "$P"\n\tsha_is "$EXPECTED_TOUCH" "$P5"'),
        ('python3 - "$ARCHIVE" "$SRC" "$P1" "$P2" "$P" "$P4"',
         'python3 - "$ARCHIVE" "$SRC" "$P1" "$P2" "$P" "$P4" "$P5"'),
        ('for patchfile in "$P1" "$P2" "$P" "$P4"; do','for patchfile in "$P1" "$P2" "$P" "$P4" "$P5"; do'),
        ('(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P4")\n',
         '(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P4")\n\t\t(cd "$checkdir/tree" && TMPDIR="$checkdir/tmp" patch --batch --fuzz=0 -p1 <"$P5")\n'),
        ('\npatch --batch --fuzz=0 -p1 -d "$STATE/src" <"$P4" >"$STATE/patch-reset-gpio.log" 2>&1 || die \'reset GPIO patch failed; see patch-reset-gpio.log\'',
         '\npatch --batch --fuzz=0 -p1 -d "$STATE/src" <"$P4" >"$STATE/patch-reset-gpio.log" 2>&1 || die \'reset GPIO patch failed; see patch-reset-gpio.log\'\npatch --batch --fuzz=0 -p1 -d "$STATE/src" <"$P5" >"$STATE/patch-touch-notifier.log" 2>&1 || die \'touch notifier patch failed; see patch-touch-notifier.log\''),
    ]
    text=once(text,'for old, new in repls:', 'repls += '+repr(extra)+'\nfor old, new in repls:')
    name='D-repro-01-power-debugfs-reset-gpio-diagnostic-boot.img'
    if text.count(name)!=2:raise SystemExit('Unexpected output name count')
    text=text.replace(name,'D-repro-01-power-touch-notifier-diagnostic-boot.img')
    wrapper.write_text(text)
    (out/'patches/lmi-dsi-powerdown-notifier-unvalidated.patch').write_bytes(data)
    subprocess.run(['bash','-n',str(wrapper)],check=True)
    names=[line.split('  ',1)[1] for line in (out/'SHA256SUMS').read_text().splitlines()]
    names.append('patches/lmi-dsi-powerdown-notifier-unvalidated.patch')
    (out/'SHA256SUMS').write_text(''.join(hashlib.sha256((out/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in names))
    print('PREPARED_ONLY='+str(out))
    print('UNVALIDATED_TOUCH_NOTIFIER; no build or hardware action')

if __name__=='__main__':main()
