#!/usr/bin/env python3
"""Find the modular symbols that cap the built-in display chain.

Kconfig caps a tristate symbol at the value of the weakest selector: a
"m" selector caps a selected symbol at "m", and a "y" symbol that selects a
capped symbol is capped too. With no module payload in the initramfs, that
silently turns the whole display stack into modules and reproduces the same
white screen as the observer kernel.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CHAIN = {"DRM_EXEC", "DRM_GPUVM", "DRM_SCHED", "QCOM_UBWC_CONFIG", "QCOM_MDT_LOADER"}
CONFIG_RE = re.compile(r"^config\s+(\w+)")
SELECT_RE = re.compile(r"^\s+select\s+(\w+)")


def config_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if line.startswith("CONFIG_") and "=" in line:
            name, value = line.split("=", 1)
            values[name[len("CONFIG_"):]] = value.strip()
        elif line.startswith("# CONFIG_") and line.endswith(" is not set"):
            values[line[len("# CONFIG_"):-len(" is not set")]] = "n"
    return values


def main() -> int:
    root = Path(sys.argv[1])
    conf = Path(sys.argv[2])
    values = config_values(conf)

    offenders: dict[str, set[str]] = {target: set() for target in CHAIN}
    for kconfig in root.rglob("Kconfig*"):
        current = None
        try:
            lines = kconfig.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            match = CONFIG_RE.match(line)
            if match:
                current = match.group(1)
                continue
            match = SELECT_RE.match(line)
            if match and current:
                target = match.group(1)
                if target in CHAIN and values.get(current) == "m":
                    offenders[target].add(current)

    print("=== modular selectors capping the display chain ===")
    found = False
    for target, selectors in sorted(offenders.items()):
        for selector in sorted(selectors):
            found = True
            print(f"  {target} <- {selector} (=m)")
    if not found:
        print("  none")

    print()
    print("=== every selector of the chain, with its value ===")
    for target in sorted(CHAIN):
        for kconfig in root.rglob("Kconfig*"):
            try:
                lines = kconfig.read_text(errors="replace").splitlines()
            except OSError:
                continue
            current = None
            for line in lines:
                match = CONFIG_RE.match(line)
                if match:
                    current = match.group(1)
                    continue
                match = SELECT_RE.match(line)
                if match and current and match.group(1) == target:
                    value = values.get(current, "ABSENT")
                    mark = "  <-- caps" if value == "m" else ""
                    print(f"  {target:<18} <- {current:<34} ({value}){mark}")

    print()
    print("=== chain values ===")
    for name in sorted(CHAIN):
        print(f"  {name:<20} {values.get(name, 'ABSENT')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
