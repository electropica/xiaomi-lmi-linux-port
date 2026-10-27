#!/usr/bin/env python3
"""Build the linux7 outer RAM bundle from a kit and a previous bundle.

The bundle is the LMIBNDL1 container that the menu firmware carries in RAM.
It holds the mobian and linux7 components that the bootloader hands off. This
tool replaces the four linux7 components with the ones produced by
kernel/experimental/linux7/build/build-linux7-kit.sh and keeps every other
component byte-identical.

Container contract (chainload/bundle-format.h):
  offset 0   : "LMIBNDL1", u32 version = 1, u32 rows, u64 total length
  offset 32  : rows of 56 bytes: name[32], u64 offset, u64 length, u32 crc32
  data       : each component at a 4096-aligned offset, crc32 of the stored
               bytes
  the parser accepts 5 or 9 rows and requires the total length to equal the
               file length

Storage encoding, measured on the accepted touch2 bundle:
  gzip : mobian/kernel, mobian/initrd, linux7/kernel, linux7/initrd
  raw  : mobian/dtb, mobian/cmdline, mobian/identity, linux7/dtb,
         linux7/cmdline

Usage:
  python3 build-linux7-bundle.py --base <bundle dir> --kit <kit dir> \
                                 --output <bundle dir> [--self-test]
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import struct
import sys
import zlib
from pathlib import Path

MAGIC = b"LMIBNDL1"
HEADER = 4096
ROW = 56
ALIGN = 4096

GZIP_COMPONENTS = {"mobian/kernel", "mobian/initrd", "linux7/kernel", "linux7/initrd"}

# The bundle carries the command line that the menu hands to the kernel. The
# kit carries the observer command line; the deployed candidate adds the
# initcall_debug token, which is what produced the 84-byte bundle entry of the
# accepted touch2 bundle.
CMDLINE_SUFFIX = b" initcall_debug"


def parse(data: bytes):
    if data[:8] != MAGIC:
        raise ValueError("not an LMIBNDL1 bundle")
    version, rows = struct.unpack_from("<II", data, 8)
    total = struct.unpack_from("<Q", data, 16)[0]
    if total != len(data):
        raise ValueError(f"declared length {total} != file length {len(data)}")
    entries = []
    for i in range(rows):
        r = 32 + i * ROW
        name = data[r:r + 32].split(b"\0")[0].decode()
        off, length = struct.unpack_from("<QQ", data, r + 32)
        crc = struct.unpack_from("<I", data, r + 48)[0]
        entries.append({"name": name, "offset": off, "length": length, "crc32": crc})
    return version, rows, entries


def decode(name: str, blob: bytes) -> bytes:
    if name in GZIP_COMPONENTS:
        return gzip.decompress(blob)
    return blob


def encode(name: str, payload: bytes) -> bytes:
    if name in GZIP_COMPONENTS:
        return gzip.compress(payload, compresslevel=9, mtime=0)
    return payload


def build(entries: list[dict], payloads: dict[str, bytes]) -> bytes:
    body = bytearray()
    for entry in entries:
        name = entry["name"]
        stored = encode(name, payloads[name])
        body.extend(b"\0" * (-len(body) % ALIGN))
        entry["offset"] = HEADER + len(body)
        body.extend(stored)
        entry["length"] = len(stored)
        entry["crc32"] = zlib.crc32(stored) & 0xFFFFFFFF

    out = bytearray(HEADER)
    struct.pack_into("<8sIIQ", out, 0, MAGIC, 1, len(entries), HEADER + len(body))
    for i, entry in enumerate(entries):
        r = 32 + i * ROW
        name = entry["name"].encode()
        if len(name) >= 32:
            raise ValueError(f"component name too long: {entry['name']}")
        out[r:r + len(name)] = name
        struct.pack_into("<QQI", out, r + 32, entry["offset"], entry["length"], entry["crc32"])
    out.extend(body)
    return bytes(out)


def manifest(data: bytes, entries: list[dict], payloads: dict[str, bytes],
             changed: list[str], hardware_tested: bool) -> dict:
    components = {}
    for entry in entries:
        name = entry["name"]
        stored = data[entry["offset"]:entry["offset"] + entry["length"]]
        decoded = decode(name, stored)
        components[name] = {
            "sha256": hashlib.sha256(stored).hexdigest(),
            "stored_bytes": len(stored),
            "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
        }
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "bundle_bytes": len(data),
        "crc32": zlib.crc32(data) & 0xFFFFFFFF,
        "changed_components": changed,
        "components": components,
        "hardware_tested": hardware_tested,
    }


def kit_components(kit: Path) -> dict[str, bytes]:
    image = next(kit.glob("Image"), None)
    if image is None:
        raise SystemExit(f"no Image in {kit}")
    dtb = next(kit.glob("*.dtb"), None)
    if dtb is None:
        raise SystemExit(f"no DTB in {kit}")
    initrd = kit / "initramfs-linux7.cpio.gz"
    cmdline = kit / "linux7-cmdline.bin"
    for path in (initrd, cmdline):
        if not path.is_file():
            raise SystemExit(f"missing {path}")
    raw_cmdline = cmdline.read_bytes().rstrip(b"\0")
    if not raw_cmdline.endswith(CMDLINE_SUFFIX):
        raw_cmdline += CMDLINE_SUFFIX
    return {
        "linux7/kernel": image.read_bytes(),
        "linux7/dtb": dtb.read_bytes(),
        "linux7/initrd": gzip.decompress(initrd.read_bytes()),
        "linux7/cmdline": raw_cmdline + b"\0",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True, help="previous bundle directory")
    ap.add_argument("--kit", type=Path, help="kit directory from build-linux7-kit.sh")
    ap.add_argument("--output", type=Path, help="new bundle directory")
    ap.add_argument("--self-test", action="store_true",
                    help="rebuild the base bundle from its own components and compare")
    args = ap.parse_args()

    base_bin = args.base / "lmi-outer-linux7.bin"
    if not base_bin.is_file():
        raise SystemExit(f"missing base bundle: {base_bin}")
    base = base_bin.read_bytes()
    version, rows, entries = parse(base)
    base_payloads = {
        entry["name"]: decode(entry["name"], base[entry["offset"]:entry["offset"] + entry["length"]])
        for entry in entries
    }

    if args.self_test:
        rebuilt = build([dict(e) for e in entries], base_payloads)
        version2, rows2, entries2 = parse(rebuilt)
        ok = True
        for entry in entries2:
            name = entry["name"]
            stored = rebuilt[entry["offset"]:entry["offset"] + entry["length"]]
            decoded = decode(name, stored)
            same = decoded == base_payloads[name]
            crc_ok = (zlib.crc32(stored) & 0xFFFFFFFF) == entry["crc32"]
            print(f"  {name:<16} decoded_identical={same} crc_ok={crc_ok}")
            ok = ok and same and crc_ok
        print("SELFTEST_" + ("OK" if ok else "FAILED"))
        print(f"  base sha256      {hashlib.sha256(base).hexdigest()}")
        print(f"  rebuilt sha256   {hashlib.sha256(rebuilt).hexdigest()}")
        print("  (a different sha256 is expected: the stored gzip streams are")
        print("   re-encoded, the decoded components are identical)")
        return 0 if ok else 1

    if not args.kit or not args.output:
        raise SystemExit("--kit and --output are required unless --self-test is used")

    new_payloads = dict(base_payloads)
    new_payloads.update(kit_components(args.kit))
    changed = sorted(name for name in new_payloads
                      if new_payloads[name] != base_payloads[name])

    data = build(entries, new_payloads)
    if len(data) >= 64 * 1024 * 1024:
        raise SystemExit("bundle exceeds the 64 MiB budget of the loader")

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "lmi-outer-linux7.bin").write_bytes(data)
    record = manifest(data, entries, new_payloads, changed, hardware_tested=False)
    (args.output / "BUNDLE_RESULT.json").write_text(json.dumps(record, indent=2) + "\n")

    # read back and verify
    reread = (args.output / "lmi-outer-linux7.bin").read_bytes()
    _, _, reread_entries = parse(reread)
    for entry in reread_entries:
        name = entry["name"]
        stored = reread[entry["offset"]:entry["offset"] + entry["length"]]
        if (zlib.crc32(stored) & 0xFFFFFFFF) != entry["crc32"]:
            raise SystemExit(f"crc mismatch for {name}")
        if decode(name, stored) != new_payloads[name]:
            raise SystemExit(f"content mismatch for {name}")
    print("BUNDLE_WRITTEN", args.output)
    print("  sha256", record["sha256"])
    print("  bytes ", record["bundle_bytes"])
    print("  changed components:", ", ".join(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
