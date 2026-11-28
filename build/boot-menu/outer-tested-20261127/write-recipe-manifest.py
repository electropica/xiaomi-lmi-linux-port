#!/usr/bin/env python3
"""Regenerate or check the source manifest after explicitly reviewing edits."""
import hashlib,json,sys
from pathlib import Path
p=Path(__file__).resolve().parent
record=p/'RECIPE_RESULT.json'
files={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest()
       for f in sorted(p.rglob('*')) if f.is_file() and f!=record and '__pycache__' not in f.parts}
if sys.argv[1:]==['--write']:
    record.write_text(json.dumps({'files':files},indent=2)+'\n',encoding='utf-8')
elif not sys.argv[1:]:
    if json.loads(record.read_text())['files']!=files: raise SystemExit('Recipe files do not match manifest')
    print('MENU_RECIPE_MANIFEST_OK')
else:
    raise SystemExit('Use --write after review, or no arguments to verify')
