#!/usr/bin/env python3
"""Prepare a menu recipe for a new linux7 bundle.

The project's menu recipe is pinned: `build.sh` checks the sha256 of every
recipe file against `RECIPE_RESULT.json`, and
`external-mobian/make-outer.py` checks the sha256 of the RAM bundle it
embeds. A new linux7 candidate therefore needs a new recipe directory with
three pinned values changed, and a regenerated manifest.

This tool performs that change and refuses to touch anything else:

  * copies the reference recipe to a new directory,
  * rewrites the three pinned paths (recipe name, bundle directory, output
    directory),
  * pins the sha256 of the produced bundle in `external-mobian/make-outer.py`,
  * regenerates `RECIPE_RESULT.json` from the files of the new recipe.

It never runs the firmware build and never contacts a handset.

Usage:
  python3 prepare-menu-recipe.py --reference <recipe dir> \\
                                 --name display1 \\
                                 --bundle <bundle dir> \\
                                 --output <new recipe dir> [--verify-only]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

EXCLUDED_DIRS = {"__pycache__"}
EXCLUDED_NAMES = {"RECIPE_RESULT.json"}


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.name in EXCLUDED_NAMES:
            continue
        if path.suffix == ".pyc":
            continue
        yield path


def record_files(root: Path) -> dict[str, str]:
    out = {}
    for path in iter_files(root):
        rel = path.relative_to(root).as_posix()
        out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", type=Path, required=True)
    ap.add_argument("--name", help="new recipe name, e.g. display1")
    ap.add_argument("--bundle", type=Path, help="bundle directory the recipe must embed")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--verify-only", action="store_true",
                    help="only check that the reference manifest matches its files")
    args = ap.parse_args()

    reference = args.reference.resolve()
    if not (reference / "build.sh").is_file():
        raise SystemExit(f"not a recipe directory: {reference}")

    if args.verify_only:
        committed = json.loads((reference / "RECIPE_RESULT.json").read_text())
        recomputed = record_files(reference)
        if committed.get("files") != recomputed:
            missing = set(committed.get("files", {})) - set(recomputed)
            extra = set(recomputed) - set(committed.get("files", {}))
            differing = [k for k in set(recomputed) & set(committed.get("files", {}))
                         if recomputed[k] != committed["files"][k]]
            print("files only in the manifest:", sorted(missing)[:10])
            print("files only on disk      :", sorted(extra)[:10])
            print("files with a new hash   :", sorted(differing)[:10])
            raise SystemExit("the manifest rule does not reproduce the committed record")
        print("MANIFEST_RULE_REPRODUCED", len(recomputed), "files")
        return 0

    if not args.bundle:
        raise SystemExit("--bundle is required")
    if not args.name:
        raise SystemExit("--name is required")
    bundle = args.bundle.resolve()
    bundle_bin = bundle / "lmi-outer-linux7.bin"
    bundle_record = bundle / "BUNDLE_RESULT.json"
    for path in (bundle_bin, bundle_record):
        if not path.is_file():
            raise SystemExit(f"missing bundle input: {path}")
    bundle_sha = hashlib.sha256(bundle_bin.read_bytes()).hexdigest()
    declared = json.loads(bundle_record.read_text()).get("sha256")
    if declared != bundle_sha:
        raise SystemExit(f"bundle record disagrees with the bundle: {declared} != {bundle_sha}")

    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"output exists, refusing to overwrite: {output}")
    shutil.copytree(reference, output, symlinks=False)

    build_sh = output / "build.sh"
    text = build_sh.read_text()
    text, n1 = re.subn(r'recipe-\w+(?=["/])', f'recipe-{args.name}', text, count=1)
    text, n2 = re.subn(r'codex-linux7-bundle-\w+', bundle.parent.name, text)
    text, n3 = re.subn(r'firmware-output-\w+', f'firmware-output-{args.name}', text)
    if n1 == 0 or n2 == 0 or n3 == 0:
        raise SystemExit(f"could not rewrite the pinned paths ({n1}, {n2}, {n3})")
    build_sh.write_text(text)

    make_outer = output / "external-mobian/make-outer.py"
    text = make_outer.read_text()
    text, n4 = re.subn(r"sha256\(data\)\.hexdigest\(\)=='[0-9a-f]{64}'",
                        f"sha256(data).hexdigest()=='{bundle_sha}'", text)
    if n4 != 1:
        raise SystemExit(f"could not pin the bundle hash in make-outer.py ({n4})")
    make_outer.write_text(text)

    manifest = {
        "bundle_sha256": bundle_sha,
        "files": record_files(output),
    }
    (output / "RECIPE_RESULT.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print("RECIPE_PREPARED", output)
    print("  bundle     ", bundle, bundle_sha)
    print("  files      ", len(manifest["files"]))
    print("  build with ", f"sudo bash {output}/build.sh --build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
