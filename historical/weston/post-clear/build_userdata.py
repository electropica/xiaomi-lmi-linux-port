#!/usr/bin/env python3
import hashlib
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
REFERENCE = BASE / "output/D-repro-01-userdata-rootfs-ssh-key-weston-control.img"
WORK = BASE / "weston-post-clear"
PAYLOAD = WORK / "payload-root"
CONFIG = WORK / "config"
OUT = BASE / "output/D-repro-01-userdata-rootfs-ssh-key-weston-post-clear-v2.img"
ROOTFS = WORK / "D-repro-01-weston-post-clear-v2-pmOS_root.ext4"
CMDS = WORK / "debugfs-inject.commands"
MANIFEST = WORK / "D-repro-01-weston-post-clear-v2-manifest.json"
MODETEST = BASE / "analysis/d114-modetest/extract/usr/bin/modetest"

SECTOR_SIZE = 4096
ROOT_START = 62464
ROOT_SECTORS = 301056


def run(argv, **kwargs):
    subprocess.run([str(x) for x in argv], check=True, **kwargs)


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe(path):
    value = str(path)
    if any(c.isspace() for c in value) or "'" in value or '"' in value:
        raise ValueError(f"debugfs-unsafe path: {value!r}")
    return value


def prepare_payload():
    if PAYLOAD.exists():
        shutil.rmtree(PAYLOAD)
    copies = {
        CONFIG / "weston.ini": PAYLOAD / "etc/weston-post-clear/weston.ini",
        CONFIG / "weston-post-clear-run": PAYLOAD / "usr/local/sbin/weston-post-clear-run",
        CONFIG / "weston-post-clear.initd": PAYLOAD / "etc/init.d/weston-post-clear",
        MODETEST: PAYLOAD / "usr/local/libexec/d114-modetest",
    }
    for source, destination in copies.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    for path in (
        PAYLOAD / "usr/local/sbin/weston-post-clear-run",
        PAYLOAD / "etc/init.d/weston-post-clear",
        PAYLOAD / "usr/local/libexec/d114-modetest",
    ):
        path.chmod(0o755)


def generate_commands():
    commands = []
    changes = []
    entries = sorted(PAYLOAD.rglob("*"), key=lambda p: (len(p.parts), str(p)))
    for source in entries:
        destination = "/" + source.relative_to(PAYLOAD).as_posix()
        info = source.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if source.is_dir():
            commands += [
                f"mkdir {safe(destination)}",
                f"set_inode_field {safe(destination)} uid 0",
                f"set_inode_field {safe(destination)} gid 0",
                f"set_inode_field {safe(destination)} mode 04{mode:04o}",
            ]
            changes.append({"path": destination, "type": "directory", "mode": f"{mode:04o}"})
        else:
            commands += [
                f"rm {safe(destination)}",
                f"write {safe(source)} {safe(destination)}",
                f"set_inode_field {safe(destination)} uid 0",
                f"set_inode_field {safe(destination)} gid 0",
                f"set_inode_field {safe(destination)} mode 010{mode:04o}",
            ]
            changes.append({
                "path": destination,
                "type": "file",
                "mode": f"{mode:04o}",
                "size": info.st_size,
                "sha256": sha256(source),
            })
    commands += [
        "rm /etc/runlevels/default/weston-control",
        "rm /etc/runlevels/default/weston-post-clear",
        "symlink /etc/runlevels/default/weston-post-clear /etc/init.d/weston-post-clear",
    ]
    changes += [
        {"path": "/etc/runlevels/default/weston-control", "type": "removed-symlink-only"},
        {"path": "/etc/runlevels/default/weston-post-clear", "type": "symlink", "target": "/etc/init.d/weston-post-clear"},
    ]
    CMDS.write_text("\n".join(commands) + "\n")
    return changes


def main():
    prepare_payload()
    runner = PAYLOAD / "usr/local/sbin/weston-post-clear-run"
    if runner.stat().st_size == 0 or not os.access(runner, os.X_OK):
        raise RuntimeError("weston-post-clear-run must be non-empty and executable")
    changes = generate_commands()
    shutil.copyfile(REFERENCE, OUT)
    with REFERENCE.open("rb") as src, ROOTFS.open("wb") as dst:
        src.seek(ROOT_START * SECTOR_SIZE)
        remaining = ROOT_SECTORS * SECTOR_SIZE
        while remaining:
            block = src.read(min(8 * 1024 * 1024, remaining))
            if not block:
                raise RuntimeError("short read extracting pmOS_root")
            dst.write(block)
            remaining -= len(block)
    with (WORK / "debugfs-inject.log").open("w") as log:
        run(["debugfs", "-w", "-f", CMDS, ROOTFS], stdout=log, stderr=subprocess.STDOUT)
    with (WORK / "e2fsck.log").open("w") as log:
        run(["e2fsck", "-fy", ROOTFS], stdout=log, stderr=subprocess.STDOUT)
    with OUT.open("r+b") as dst, ROOTFS.open("rb") as src:
        dst.seek(ROOT_START * SECTOR_SIZE)
        shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)
    MANIFEST.write_text(json.dumps({
        "schema": "d-repro-01-weston-post-clear/v2",
        "reference": {"path": str(REFERENCE), "size": REFERENCE.stat().st_size, "sha256": sha256(REFERENCE)},
        "output_raw": {"path": str(OUT), "size": OUT.stat().st_size, "sha256": sha256(OUT)},
        "root_partition": {"sector_size": SECTOR_SIZE, "start_sector": ROOT_START, "sector_count": ROOT_SECTORS},
        "historical_modetest": {
            "package": "libdrm-tests-2.4.134-r0 aarch64",
            "package_sha256": "e562e3cc297944991b8b249bc26e13a4e48b0891d646ebd0acb96d3e7bfad2bb",
            "apkindex_checksum": "Q1e+M+5acvRB1abHMFixGugAhOkeA=",
            "binary_sha256": sha256(MODETEST),
        },
        "kernel_dtb_boot_image": "unchanged; userdata-only derivative",
        "changes": changes,
    }, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
