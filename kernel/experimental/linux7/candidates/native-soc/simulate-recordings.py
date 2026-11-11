#!/usr/bin/env python3
"""Compare recorded MSOC with the reconstructed driver's native mapping.

This is a model, not an execution of the driver. Recorded capacity and MSOC
are sampled separately; their apparent mismatch need not be simultaneous.
"""
import csv
import re
import sys
from pathlib import Path


def native(raw):
    if raw == 0:
        return 0
    if raw == 255:
        return 100
    return ((raw - 1) * 98 + 253 // 2) // 253 + 1


def rows(path):
    if path.suffix == ".csv":
        with path.open(encoding="utf-8", newline="") as source:
            for row in csv.DictReader(source):
                if row.get("status") == "Discharging":
                    try:
                        yield row["stamp"], int(row["capacity"]), int(row["msoc"], 16)
                    except (KeyError, ValueError):
                        continue
    else:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.startswith("SAMPLE ") or "status=Discharging" not in line:
                continue
            fields = dict(re.findall(r"(\w+)=(\S+)", line))
            try:
                yield fields["wall"], int(fields["capacity"]), int(fields["FG_MSOC"])
            except (KeyError, ValueError):
                continue


def main():
    for name in sys.argv[1:]:
        samples = list(rows(Path(name)))
        if not samples:
            raise SystemExit(f"no discharge samples: {name}")
        differences = [(t, shown, raw, native(raw)) for t, shown, raw in samples
                       if shown != native(raw)]
        print(f"{Path(name).name}: {len(samples)} samples; "
              f"{len(differences)} sampled differences from native model")
        for t, shown, raw, modeled in differences[:5]:
            print(f"  {t}: shown={shown}% raw={raw} native_model={modeled}%")
    print("Release-boundary model: raw=240 -> native", native(240),
          "%; raw=239 -> native", native(239), "%")
    assert [native(x) for x in (0, 239, 240, 248, 254, 255)] == [0, 93, 94, 97, 99, 100]
    assert all(native(n) <= native(n + 1) for n in range(255))
    print("MODEL_BOUNDARIES_PASS")


if __name__ == "__main__":
    main()
