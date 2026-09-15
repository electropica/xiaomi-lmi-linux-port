#!/usr/bin/python3
"""Acquire a new M0 package lock. Never install packages or construct a rootfs."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from urllib.parse import urlsplit


REPO = Path(__file__).resolve().parents[2]
CONTRACT = REPO / "base/files/m0-direct-packages.txt"
DIRECT = frozenset("""ca-certificates mobian-archive-keyring systemd systemd-sysv
udev dbus openssh-server iproute2 kmod seatd libseat1 weston libweston-14-0
libpixman-1-0 libdrm2 libdrm-tests""".split())
FIELDS = ["package", "version", "architecture", "origin", "suite", "url",
          "size", "sha256", "cache_path"]


def fail(message):
    raise RuntimeError(message)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def roots():
    names = [line.strip() for line in CONTRACT.read_text().splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if len(names) != 16 or set(names) != DIRECT:
        fail("The contract must contain exactly the 16 approved unique M0 roots")
    return names


def forbidden(name):
    return (name in {"mobian-base", "network-manager", "mobile-usb-networking"}
            or name == "phosh" or name.startswith("phosh-")
            or name.startswith(("linux-image-", "linux-headers-", "initramfs-tools")))


def apt_value(value):
    return json.dumps(str(value))


def run(argv, env, log):
    result = subprocess.run(argv, env=env, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    log.write_text(result.stdout)
    if result.returncode:
        fail(f"Command failed ({result.returncode}); inspect {log}")
    return result.stdout


def tool_version(tool, env):
    result = subprocess.run([tool, "--version"], env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            check=True)
    lines = result.stdout.splitlines()
    if not lines:
        fail(f"No version reported by {tool}")
    return lines[0]


def uri_plan(text):
    entries = {}
    for line in text.splitlines():
        if not line.startswith("'"):
            continue
        fields = shlex.split(line)
        if len(fields) != 4 or not fields[1].endswith(".deb"):
            fail(f"Unexpected APT URI record: {line}")
        url, filename, size, _apt_hash = fields
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password:
            fail("Only credential-free HTTPS package URLs are allowed")
        if Path(filename).name != filename or filename in {".", ".."}:
            fail("Unsafe archive filename")
        if url in entries or any(e["filename"] == filename for e in entries.values()):
            fail("Duplicate URI or archive filename in APT plan")
        entries[url] = {"filename": filename, "size": int(size)}
    if not entries:
        fail("APT returned an empty acquisition plan")
    return entries


def metadata(plan, config_path):
    # apt_pkg reads only the same isolated state used by apt-get.
    import apt_pkg
    os.environ["APT_CONFIG"] = str(config_path)
    apt_pkg.config.clear()
    apt_pkg.init_config()
    apt_pkg.init_system()
    cache = apt_pkg.Cache()
    sources = apt_pkg.SourceList()
    sources.read_main_list()
    records = apt_pkg.PackageRecords(cache)
    found = {}
    for package in cache.packages:
        for version in package.version_list:
            for package_file, offset in version.file_list:
                index = sources.find_index(package_file)
                if index is None or not records.lookup((package_file, offset)):
                    continue
                url = index.archive_uri(records.filename)
                if url not in plan:
                    continue
                if not index.is_trusted:
                    fail(f"Unauthenticated index for {url}")
                if version.arch not in {"arm64", "all"}:
                    fail(f"Unexpected architecture: {version.arch}")
                sha = records.sha256_hash
                if not re.fullmatch(r"[0-9a-f]{64}", sha):
                    fail(f"Missing SHA-256 in authenticated metadata: {url}")
                name = records.name
                if forbidden(name):
                    fail(f"Forbidden M0 package selected: {name}")
                row = dict(package=name, version=version.ver_str,
                           architecture=version.arch, origin=package_file.origin,
                           suite=package_file.codename or package_file.archive,
                           url=url, size=version.size, sha256=sha,
                           cache_path=f"cache/{plan[url]['filename']}")
                if row["size"] != plan[url]["size"]:
                    fail(f"Size disagrees with APT plan: {name}")
                if url in found and found[url] != row:
                    fail(f"Ambiguous metadata for {url}")
                found[url] = row
    if set(found) != set(plan):
        fail("Some acquisition URLs have no matching authenticated package record")
    rows = sorted(found.values(), key=lambda r: (r["package"], r["architecture"]))
    identities = [(r["package"], r["architecture"]) for r in rows]
    if len(set(identities)) != len(rows):
        fail("Multiple versions selected for one package/architecture")
    if not DIRECT.issubset({r["package"] for r in rows}):
        fail("The acquisition plan does not contain all 16 roots")
    if not {"apt", "debian-archive-keyring"}.issubset({r["package"] for r in rows}):
        fail("APT and the Debian archive keyring must be present in the closure")
    return rows


def write_tsv(path, rows):
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def acquire(args, direct):
    for tool in ("apt-get", "dpkg-deb", "mmdebstrap"):
        if not shutil.which(tool):
            fail(f"Missing host tool: {tool}")
    try:
        import apt_pkg  # noqa: F401
    except ImportError:
        fail("Missing python3-apt for /usr/bin/python3")
    keys = {}
    for name in ("debian", "mobian"):
        supplied = getattr(args, f"{name}_keyring")
        if not supplied:
            fail(f"--{name}-keyring is required (trusted public keyring)")
        key = Path(supplied).resolve(strict=True)
        if not key.is_file() or key.suffix not in {".gpg", ".pgp", ".asc"}:
            fail(f"Unsupported public keyring: {key}")
        keys[name] = key
    output_root = (REPO / "output").resolve()
    work = Path(args.output_dir).resolve()
    if not work.is_relative_to(output_root) or work == output_root:
        fail("Choose a fresh reference directory strictly under repository output/")
    work.mkdir(parents=True, exist_ok=False)
    for relative in ("apt/etc/parts", "apt/etc/trustedparts", "apt/etc/authparts",
                     "apt/state/lists/partial", "cache/partial", "logs", "keyrings"):
        (work / relative).mkdir(parents=True, exist_ok=True)
    (work / "apt/state/status").write_text("")
    key_info = {}
    for name, source in keys.items():
        target = work / "keyrings" / (name + source.suffix)
        shutil.copyfile(source, target)
        target.chmod(0o644)
        key_info[name] = {"file": str(target.relative_to(work)), "sha256": digest(target)}
        keys[name] = target
    sources = work / "apt/etc/m0.sources"
    sources.write_text(
        "Types: deb\nURIs: https://deb.debian.org/debian\nSuites: trixie\n"
        f"Components: main\nArchitectures: arm64\nSigned-By: {keys['debian']}\n\n"
        "Types: deb\nURIs: https://security.debian.org/debian-security\n"
        f"Suites: trixie-security\nComponents: main\nArchitectures: arm64\nSigned-By: {keys['debian']}\n\n"
        "Types: deb\nURIs: https://repo.mobian.org/\nSuites: trixie\n"
        f"Components: main\nArchitectures: arm64\nSigned-By: {keys['mobian']}\n")
    preferences = work / "apt/etc/preferences"
    preferences.write_text("Package: *\nPin: release o=Mobian\nPin-Priority: 700\n")
    config = work / "apt/apt.conf"
    settings = {
        "Dir": work / "apt", "Dir::Etc::main": "/dev/null",
        "Dir::Etc::parts": work / "apt/etc/parts",
        "Dir::Etc::sourcelist": sources, "Dir::Etc::sourceparts": work / "apt/etc/parts",
        "Dir::Etc::preferences": preferences, "Dir::Etc::preferencesparts": work / "apt/etc/parts",
        "Dir::Etc::trusted": "/dev/null", "Dir::Etc::trustedparts": work / "apt/etc/trustedparts",
        "Dir::Etc::netrc": "/dev/null", "Dir::Etc::netrcparts": work / "apt/etc/authparts",
        "Dir::State::status": work / "apt/state/status",
        "Dir::State::lists": work / "apt/state/lists",
        "Dir::State::extended_states": work / "apt/state/extended_states",
        "Dir::Cache::archives": work / "cache", "Dir::Cache::pkgcache": "",
        "Dir::Cache::srcpkgcache": "", "Dir::Log": work / "logs",
        "APT::Architecture": "arm64", "APT::Install-Recommends": "false",
        "APT::Install-Suggests": "false", "Acquire::Languages": "none",
        "Acquire::ForceHash": "SHA256", "Acquire::Retries": "3",
        "APT::Update::Error-Mode": "any", "pkgCacheGen::ForceEssential": ",",
    }
    config.write_text("\n".join(f"{key} {apt_value(value)};" for key, value in settings.items())
                      + '\n#clear APT::Architectures;\nAPT::Architectures { "arm64"; };\n')
    # Do not inherit host APT_CONFIG or proxy credentials into acquisition/logs.
    env = {key: os.environ[key] for key in ("PATH", "HOME", "USER", "LOGNAME") if key in os.environ}
    env.update(APT_CONFIG=str(config), LC_ALL="C", DEBIAN_FRONTEND="noninteractive")
    run(["apt-get", "update"], env, work / "logs/update.log")
    # Reproduce mmdebstrap minbase selectors, including its explicit apt root.
    selectors = [
        "?narrow(?or(?archive(^trixie$),?codename(^trixie$)),?architecture(arm64),?essential)",
        "?narrow(?or(?archive(^trixie$),?codename(^trixie$)),?architecture(arm64),?and(?priority(required),?not(?essential)))",
    ]
    request = [*direct, "apt", "debian-archive-keyring", *selectors]
    plan_text = run(["apt-get", "--yes", "--download-only", "--print-uris",
                     "--no-install-recommends", "install", *request], env, work / "logs/plan.log")
    plan = uri_plan(plan_text)
    rows = metadata(plan, config)
    write_tsv(work / "m0-closure.candidate.tsv", rows)
    provenance = {
        "schema": 1, "architecture": "arm64", "variant": "minbase",
        "acquired_at": datetime.now(timezone.utc).isoformat(),
        "direct_packages": direct, "install_recommends": False,
        "keyrings": key_info, "sources": [
            {"url": "https://deb.debian.org/debian", "suite": "trixie", "component": "main"},
            {"url": "https://security.debian.org/debian-security", "suite": "trixie-security", "component": "main"},
            {"url": "https://repo.mobian.org/", "suite": "trixie", "component": "main"}],
        "mobian_priority": 700,
        "contract_sha256": digest(CONTRACT),
        "tools": {tool: tool_version(tool, env)
                  for tool in ("apt-get", "dpkg-deb", "mmdebstrap")},
        "indexes": {str(p.relative_to(work)): digest(p)
                    for p in sorted((work / "apt/state/lists").iterdir()) if p.is_file()},
    }
    (work / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    if args.plan_only:
        print(f"PLAN ONLY: {len(rows)} packages; candidate at {work}; no archives downloaded")
        return
    # Exact versions from the candidate; no second apt update or host installation.
    exact = [f"{r['package']}:{r['architecture']}={r['version']}" if r["architecture"] != "all"
             else f"{r['package']}={r['version']}" for r in rows]
    second = uri_plan(run(["apt-get", "--yes", "--download-only", "--print-uris",
                           "install", *exact], env, work / "logs/locked-plan.log"))
    if second != plan:
        fail("Exact-version acquisition differs from initial resolution")
    run(["apt-get", "--yes", "--download-only", "install", *exact], env, work / "logs/download.log")
    expected = {r["cache_path"] for r in rows}
    actual = {str(p.relative_to(work)) for p in (work / "cache").glob("*.deb")}
    if actual != expected:
        fail("Downloaded archive set differs from candidate")
    for row in rows:
        archive = work / row["cache_path"]
        if archive.stat().st_size != row["size"] or digest(archive) != row["sha256"]:
            fail(f"Size/SHA-256 mismatch: {archive.name}")
        identity = subprocess.check_output(
            ["dpkg-deb", "--show", "--showformat=${Package}\t${Version}\t${Architecture}", str(archive)],
            env=env, text=True).split("\t")
        if identity != [row["package"], row["version"], row["architecture"]]:
            fail(f"Archive identity mismatch: {archive.name}")
    write_tsv(work / "m0-closure.lock.tsv", rows)
    print(f"ACQUISITION VERIFIED: {len(rows)} packages; {work / 'm0-closure.lock.tsv'}")
    print("No rootfs built. Lock remains under output/ for review; nothing copied to Git.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-contract", action="store_true", help="Offline, read-only contract validation")
    parser.add_argument("--output-dir", help="Fresh reference directory under repository output/")
    parser.add_argument("--debian-keyring", help="Trusted Debian public archive keyring")
    parser.add_argument("--mobian-keyring", help="Trusted Mobian public archive keyring")
    parser.add_argument("--plan-only", action="store_true", help="Fetch indexes and resolve; do not download .deb")
    args = parser.parse_args()
    direct = roots()
    if args.check_contract:
        if args.output_dir or args.plan_only or args.debian_keyring or args.mobian_keyring:
            parser.error("--check-contract cannot be combined with acquisition options")
        print("CONTRACT OK: 16 unique approved M0 roots; no network or filesystem writes")
        return
    if not args.output_dir:
        parser.error("--output-dir is required for acquisition")
    acquire(args, direct)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
