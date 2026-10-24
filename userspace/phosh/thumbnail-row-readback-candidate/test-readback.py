#!/usr/bin/python3
"""Native isolated C checks; not a Phoc or handset build."""
from pathlib import Path
import tempfile,subprocess,shutil
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='lmi-thumb-row-check-') as t:
 d=Path(t)
 for n in ['test-readback.c','thumbnail-readback-helper.inc']:shutil.copy2(here/n,d/n)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-O1','-g','-fsanitize=address,undefined','-o',str(d/'check'),str(d/'test-readback.c')],check=True)
 subprocess.run([str(d/'check')],check=True)
