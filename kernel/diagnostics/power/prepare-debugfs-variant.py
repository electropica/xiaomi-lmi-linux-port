#!/usr/bin/env python3
"""Prepare a private debugfs boot recipe; never compile or contact hardware."""
import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

BASE_SHA = "c92da38b49b345ad996799af4d6de7319071f2822ff321affc763fb50241afdc"
CONFIG_SHA = "6512a0c29ebf987d25c0cceb79917df32d6fed4b67e4c3b94bfad9fdb1745e37"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise SystemExit("Unexpected transformation anchor: " + old[:100])
    return text.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", required=True,
                        help="new private directory, outside tracked source paths")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    audio = root / "kernel/diagnostics/audio"
    out = Path(args.output_directory).absolute()
    # Limit repository-local generated content to an already ignored state tree.
    resolved = out.resolve()
    if resolved == root or root in resolved.parents:
        rel = resolved.relative_to(audio) if audio in resolved.parents else None
        if rel is None or not rel.parts[0].startswith("state-"):
            raise SystemExit("Repository-local output must be in audio/state-*")
    if out.exists() or out.is_symlink():
        raise SystemExit("Refusing existing output directory")
    base = (audio / "build-audio-swr-diagnostic-boot.sh").read_bytes()
    config = (root / "kernel/configs/dv43-qca6390-v2.config").read_bytes()
    if digest(base) != BASE_SHA or digest(config) != CONFIG_SHA:
        raise SystemExit("Locked base recipe/config identity mismatch")
    delta = (Path(__file__).resolve().parent / "power-debugfs-config.patch").read_bytes()
    if digest(delta) != "97aa555bc14351f5e820eec053680299c5108c097ee905c550a6e0fac56cfca9":
        raise SystemExit("Reviewed power config delta identity mismatch")
    with tempfile.TemporaryDirectory(prefix="lmi-power-config-") as staging:
        target = Path(staging) / "candidate.config"
        target.write_bytes(config)
        subprocess.run(["patch", "--batch", "--fuzz=0", "--silent", str(target)],
                       input=delta, check=True)
        candidate = target.read_bytes()
    cfgsha = digest(candidate)
    derived = replace_once(base.decode(), "EXPECTED_CONFIG=" + CONFIG_SHA,
                           "EXPECTED_CONFIG=" + cfgsha)
    wrapper = (audio / "build-audio-swr-reset-gpio-diagnostic-boot.sh").read_text()
    wrapper = replace_once(wrapper, "EXPECTED_BASE=" + BASE_SHA,
                           "EXPECTED_BASE=" + digest(derived.encode()))
    old_name = "D-repro-01-audio-swr-reset-gpio-diagnostic-boot.img"
    if wrapper.count(old_name) != 2:
        raise SystemExit("Unexpected reset variant output-name anchors")
    wrapper = wrapper.replace(old_name,
                              "D-repro-01-power-debugfs-reset-gpio-diagnostic-boot.img")
    wrapper = replace_once(wrapper,
        '${AUDIO_DIAG_CONFIG:-$PROJECT_ROOT/kernel/configs/dv43-qca6390-v2.config}',
        '${AUDIO_DIAG_CONFIG:-$ROOT/power-debugfs.config}')
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    (out / "patches").mkdir(mode=0o700)
    files = {
        "power-debugfs.config": candidate,
        "build-audio-swr-diagnostic-boot.sh": derived.encode(),
        "build-audio-swr-reset-gpio-diagnostic-boot.sh": wrapper.encode(),
        "patches/0001-lmi-wcd938x-rx-soundwire-diagnostic.patch":
            (audio / "patches/0001-lmi-wcd938x-rx-soundwire-diagnostic.patch").read_bytes(),
    }
    for name, data in files.items():
        (out / name).write_bytes(data)
    (out / "SHA256SUMS").write_text("".join(
        digest(data) + "  " + name + "\n" for name, data in files.items()))
    print("PREPARED_ONLY=" + str(out))
    print("CONFIG_SHA256=" + cfgsha)
    print("DELTA=reviewed debugfs + required MSM idle statistics; no build or hardware action")


if __name__ == "__main__":
    main()
