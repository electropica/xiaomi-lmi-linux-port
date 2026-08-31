#!/usr/bin/env python3
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
REFERENCE = BASE / "output/D-repro-01-userdata-rootfs-ssh-key.img"
WORK = BASE / "weston-control"
PAYLOAD = WORK / "payload-root"
CONFIG = WORK / "config"
OUT = BASE / "output/D-repro-01-userdata-rootfs-ssh-key-weston-control.img"
ROOTFS = WORK / "D-repro-01-weston-control-pmOS_root.ext4"
CMDS = WORK / "debugfs-inject.commands"
MANIFEST = WORK / "D-repro-01-weston-control-changes.json"

SECTOR_SIZE = 4096
ROOT_START = 62464
ROOT_SECTORS = 301056


def run(argv, **kwargs):
    subprocess.run([str(x) for x in argv], check=True, **kwargs)


def q(value: str) -> str:
    if any(c.isspace() for c in value) or '"' in value or "'" in value:
        raise ValueError(f"debugfs-unsafe path: {value!r}")
    return value


def add_local_files():
    destinations = {
        CONFIG / "weston.ini": PAYLOAD / "etc/weston-control/weston.ini",
        CONFIG / "weston-control-run": PAYLOAD / "usr/local/sbin/weston-control-run",
        CONFIG / "weston-control.initd": PAYLOAD / "etc/init.d/weston-control",
    }
    for source, destination in destinations.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def generate_commands():
    entries = sorted(PAYLOAD.rglob("*"), key=lambda p: (len(p.parts), str(p)))
    commands = []
    changes = []

    for source in entries:
        relative = source.relative_to(PAYLOAD)
        destination = "/" + relative.as_posix()
        info = source.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if source.is_dir():
            commands.append(f"mkdir {q(destination)}")
            commands.append(f"set_inode_field {q(destination)} uid 0")
            commands.append(f"set_inode_field {q(destination)} gid 0")
            commands.append(f"set_inode_field {q(destination)} mode 04{mode:04o}")
            changes.append({"path": destination, "type": "directory", "mode": f"{mode:04o}"})
        elif source.is_symlink():
            target = os.readlink(source)
            commands.append(f"rm {q(destination)}")
            commands.append(f"symlink {q(destination)} {q(target)}")
            changes.append({"path": destination, "type": "symlink", "target": target})
        elif source.is_file():
            commands.append(f"rm {q(destination)}")
            commands.append(f"write {q(str(source))} {q(destination)}")
            commands.append(f"set_inode_field {q(destination)} uid 0")
            commands.append(f"set_inode_field {q(destination)} gid 0")
            commands.append(f"set_inode_field {q(destination)} mode 010{mode:04o}")
            changes.append({
                "path": destination,
                "type": "file",
                "mode": f"{mode:04o}",
                "size": info.st_size,
            })
        else:
            raise RuntimeError(f"unsupported payload entry: {source}")

    commands.extend([
        "rm /etc/runlevels/default/shelli",
        "rm /etc/runlevels/default/weston-control",
        "symlink /etc/runlevels/default/weston-control /etc/init.d/weston-control",
    ])
    changes.extend([
        {"path": "/etc/runlevels/default/shelli", "type": "removed-symlink-only"},
        {
            "path": "/etc/runlevels/default/weston-control",
            "type": "symlink",
            "target": "/etc/init.d/weston-control",
        },
    ])
    CMDS.write_text("\n".join(commands) + "\n")
    MANIFEST.write_text(json.dumps({
        "schema": "d-repro-01-weston-control-changes/v1",
        "reference": str(REFERENCE),
        "output": str(OUT),
        "root_partition": {
            "sector_size": SECTOR_SIZE,
            "start_sector": ROOT_START,
            "sector_count": ROOT_SECTORS,
        },
        "deployment": "verified APK payloads; APK database intentionally unchanged",
        "changes": changes,
    }, indent=2, sort_keys=True) + "\n")


def main():
    add_local_files()
    generate_commands()
    shutil.copyfile(REFERENCE, OUT)
    with REFERENCE.open("rb") as src, ROOTFS.open("wb") as dst:
        src.seek(ROOT_START * SECTOR_SIZE)
        remaining = ROOT_SECTORS * SECTOR_SIZE
        while remaining:
            block = src.read(min(8 * 1024 * 1024, remaining))
            if not block:
                raise RuntimeError("short read while extracting pmOS_root")
            dst.write(block)
            remaining -= len(block)
    run(["debugfs", "-w", "-f", CMDS, ROOTFS], stdout=WORK.joinpath("debugfs-inject.log").open("w"), stderr=subprocess.STDOUT)
    run(["e2fsck", "-fy", ROOTFS], stdout=WORK.joinpath("e2fsck.log").open("w"), stderr=subprocess.STDOUT)
    with OUT.open("r+b") as dst, ROOTFS.open("rb") as src:
        dst.seek(ROOT_START * SECTOR_SIZE)
        shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)


if __name__ == "__main__":
    main()
