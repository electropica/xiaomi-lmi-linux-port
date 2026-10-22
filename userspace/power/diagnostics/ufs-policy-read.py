#!/usr/bin/env python3
"""Read-only UFS suspend-policy reader, v2.

Plan-only by default. One read at most, explicit --execute.

  ufs-reader-v2.py plan [--os adb|ssh]         print the commands, touch nothing
  ufs-reader-v2.py --execute --os adb          ONE read through Windows adb.exe
  ufs-reader-v2.py --execute --os ssh          ONE read through the predefined route
  ufs-reader-v2.py parse FILE                  parse a captured line protocol
  ufs-reader-v2.py --self-test                 classifier and guard tests

Corrections applied after the 2026-10-22 review of v1:

  * CLASSIFICATION. v1 used `[ -e ]` as the existence oracle. On the device the
    unprivileged adb shell is denied getattr() by SELinux on the UFS attribute
    files, so `[ -e ]` is FALSE for entries that exist, and v1 reported
    permission refusals as ABSENT. v2 classifies from the DIRECTORY LISTING:
      - a successful listing that does not contain the name -> ABSENT
        (local absence, scoped to the inspected directory);
      - a failed listing -> UNKNOWN, never ABSENT;
      - an explicit permission failure -> DENIED;
      - a name the listing contains but that cannot be read ->
        LISTED_BUT_UNREADABLE.
  * OS GUARD. v1 accepted any property containing the substring "lmi". v2
    requires exact membership of an explicit device-identifier set AND an
    explicit build-identity set, and records every property it looked at.
  * CONTEXT. The UID and the SELinux context are recorded with every read.

Guarantees of the read: sysfs reads only; no write, no open-for-write, no
echo >, no reboot, no root command, no privileged helper, no periodic
collection.
"""

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNIPPET = os.path.join(HERE, "ufs-policy-read.sh")

# explicit, exact known identifiers -- no substring matching
EXPECTED_DEVICES = ("lmi", "lmipro")
EXPECTED_BUILDS = ("23.2-20261007-NIGHTLY-lmi",)
# documented ROM family of the known reference build (prefix on a family, used
# only in addition to the two exact checks above)
EXPECTED_FINGERPRINT_PREFIX = "Redi/lmipro/lmipro:12/"
EXPECTED_FINGERPRINT_PREFIX = "Redmi/lmipro/lmipro:12/"

SSH = [
    "wsl.exe", "-d", "Ubuntu", "-u", "linuxagent", "--",
    "ssh", "-i", "/home/linuxagent/.ssh/id_ed25519_codex_lmi",
    "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
    "root@172.16.42.1", "sh", "-s",
]

POLICY_ATTRS = [
    "clkscale_enable", "clk_scaling_enable", "clkgate_enable",
    "clkgate_delay_ms", "rpm_lvl", "spm_lvl", "auto_hibern8", "auto_bkops",
    "rpm_target_link_state", "rpm_target_dev_state",
    "spm_target_link_state", "spm_target_dev_state", "max_bus_bw",
]
RUNTIME_ATTRS = ["runtime_status", "control", "runtime_active_time",
                 "runtime_suspended_time", "autosuspend_delay_ms"]
ATTRIBUTES_DIR_ATTRS = ["psa_state", "current_power_mode", "bkops_status",
                        "active_icc_level"]
QCOM_ATTRS = ["clk_status", "power_mode", "bus_speed_mode", "err_count",
              "err_state"]
REQUESTED = (POLICY_ATTRS + RUNTIME_ATTRS + ATTRIBUTES_DIR_ATTRS + QCOM_ATTRS)

LIMITS = (
    "Enabled policy attributes are configuration, not a measurement of the "
    "physical state during sleep. This read observes the UFS host's policy "
    "and runtime-PM bookkeeping only; it does not observe the link state, "
    "the device low-power entry, the rail, or any current."
)


# ---------------------------------------------------------------------------
# adb / ssh location
# ---------------------------------------------------------------------------

def _windows_home_from_path(path):
    p = path.replace("\\", "/")
    m = re.match(r"^/mnt/([a-z])/Users/([^/]+)/", p, re.I)
    if m:
        return "/mnt/%s/Users/%s" % (m.group(1).lower(), m.group(2))
    return ""


def find_adb(explicit=None):
    cands = []
    if explicit:
        cands.append(explicit)
    if os.environ.get("ADB"):
        cands.append(os.environ["ADB"])
    cands.append(os.path.join(os.path.expanduser("~"), "Downloads",
                              "platform-tools", "adb.exe"))
    w = _windows_home_from_path(os.path.abspath(__file__))
    if w:
        cands.append(os.path.join(w, "Downloads", "platform-tools", "adb.exe"))
    up = os.environ.get("USERPROFILE")
    if up:
        cands.append(os.path.join(up, "Downloads", "platform-tools",
                                  "adb.exe"))
    # WSL: the Windows toolchain lives on the C: volume, not in the WSL home
    for base in ("/mnt/c/Users", "/mnt/d/Users", "/mnt/e/Users"):
        if os.path.isdir(base):
            try:
                names = sorted(os.listdir(base))
            except OSError:
                names = []
            for name in names:
                cands.append(os.path.join(base, name, "Downloads",
                                          "platform-tools", "adb.exe"))
    for c in cands:
        if c and os.path.exists(c):
            return c
    return cands[0] if cands else ""


# ---------------------------------------------------------------------------
# parser + classifier
# ---------------------------------------------------------------------------

def parse(text):
    info, roots, listings, attrs, unparsed = {}, {}, {}, {}, []
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        parts = line.split(" ", 1)
        kind = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        if kind == "INFO":
            kv = rest.split(" ", 1)
            if len(kv) == 2:
                info[kv[0]] = kv[1].strip()
        elif kind == "ROOT":
            b = rest.split(" ", 1)
            roots[b[0]] = b[1].strip() if len(b) > 1 else ""
        elif kind == "LIST":
            b = rest.split(" ", 2)
            path = b[0]
            if len(b) >= 3 and b[1] == "OK":
                listings[path] = {"status": "OK", "names": b[2].split()}
            else:
                listings[path] = {"status": "FAILED",
                                  "names": [],
                                  "message": b[2].strip() if len(b) > 2 else ""}
        elif kind == "ATTR":
            b = rest.split(" ", 2)
            path, state = b[0], (b[1] if len(b) > 1 else "UNKNOWN")
            tail = b[2] if len(b) > 2 else ""
            attrs[path] = {"raw_state": state, "tail": tail}
        else:
            unparsed.append(line)
    return {"info": info, "roots": roots, "listings": listings,
            "attributes": attrs, "unparsed": unparsed}


def classify(parsed):
    """Turn the raw ATTR states into verified verdicts."""
    out = []
    for path in sorted(parsed["attributes"]):
        rec = parsed["attributes"][path]
        state, tail = rec["raw_state"], rec["tail"]
        parent = os.path.dirname(path)
        base = os.path.basename(path)
        listing = parsed["listings"].get(parent)
        verdict = {"path": path, "attribute": base}
        if state == "OK":
            verdict["state"] = "OK"
            verdict["value"] = tail
        elif state == "DENIED":
            verdict["state"] = "DENIED"
            verdict["errno"] = tail.split(" ", 1)[0]
            verdict["reason"] = tail.split(" ", 1)[1] if " " in tail else tail
        else:
            # the read did not give a value: the listing decides
            if listing is None:
                verdict["state"] = "UNKNOWN"
                verdict["reason"] = "no listing for the parent directory"
            elif listing["status"] != "OK":
                verdict["state"] = "UNKNOWN"
                verdict["reason"] = "directory listing failed: %s" % \
                    listing.get("message", "")
            elif base in listing["names"]:
                verdict["state"] = "LISTED_BUT_UNREADABLE"
                verdict["reason"] = tail
            else:
                verdict["state"] = "ABSENT"
                verdict["reason"] = "not enumerated in a successful listing"
        out.append(verdict)
    return out


def summarise(parsed):
    verdicts = classify(parsed)
    seen = {}
    for v in verdicts:
        seen.setdefault(v["attribute"], v)
    listing_status = {k: v["status"] for k, v in parsed["listings"].items()}
    failed_listings = [k for k, v in listing_status.items() if v != "OK"]
    return {
        "info": parsed["info"],
        "roots": parsed["roots"],
        "listing_status": listing_status,
        "failed_listings": failed_listings,
        "attributes": list(seen.values()),
        "all_attribute_verdicts": verdicts,
        "coverage": {
            "requested": REQUESTED,
            "ok": sorted({v["attribute"] for v in verdicts if v["state"] == "OK"}),
            "denied": sorted({v["attribute"] for v in verdicts
                              if v["state"] == "DENIED"}),
            "absent": sorted({v["attribute"] for v in verdicts
                              if v["state"] == "ABSENT"}),
            "listed_but_unreadable": sorted(
                {v["attribute"] for v in verdicts
                 if v["state"] == "LISTED_BUT_UNREADABLE"}),
            "unknown": sorted({v["attribute"] for v in verdicts
                               if v["state"] == "UNKNOWN"}),
        },
        "unparsed_lines": parsed["unparsed"],
        "limits": LIMITS,
    }


# ---------------------------------------------------------------------------
# OS guard (strict, explicit)
# ---------------------------------------------------------------------------

def check_identity(props, devices=EXPECTED_DEVICES, builds=EXPECTED_BUILDS,
                    fingerprint_prefix=EXPECTED_FINGERPRINT_PREFIX):
    """Exact membership checks. No substring matching on the device name."""
    report = {"ro.product.device": props.get("ro.product.device", ""),
              "ro.product.name": props.get("ro.product.name", ""),
              "ro.lineage.version": props.get("ro.lineage.version", ""),
              "ro.build.fingerprint": props.get("ro.build.fingerprint", ""),
              "ro.build.version.release":
                  props.get("ro.build.version.release", ""),
              "expected_devices": list(devices),
              "expected_builds": list(builds),
              "expected_fingerprint_prefix": fingerprint_prefix}
    dev = props.get("ro.product.device", "")
    build = props.get("ro.lineage.version", "")
    fp = props.get("ro.build.fingerprint", "")
    if dev not in devices:
        report["verdict"] = "REJECTED"
        report["reason"] = "ro.product.device %r is not an exact member of %r" \
            % (dev, list(devices))
        return report
    if build not in builds:
        report["verdict"] = "REJECTED"
        report["reason"] = "ro.lineage.version %r is not an exact member of %r" \
            % (build, list(builds))
        return report
    if not fp.startswith(fingerprint_prefix):
        report["verdict"] = "REJECTED"
        report["reason"] = "ro.build.fingerprint does not start with %r" \
            % fingerprint_prefix
        return report
    report["verdict"] = "ACCEPTED"
    report["reason"] = "exact device and build identity match"
    return report


# ---------------------------------------------------------------------------
# transports
# ---------------------------------------------------------------------------

def adb_devices(adb):
    if not adb or not os.path.exists(adb):
        raise SystemExit("adb.exe not found (looked at %s)" % adb)
    p = subprocess.run([adb, "devices"], capture_output=True, text=True,
                       timeout=30)
    devices = []
    for line in p.stdout.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        bits = line.split()
        devices.append({"serial": bits[0],
                        "state": bits[1] if len(bits) > 1 else ""})
    return devices


def adb_getprop(adb, serial, name):
    p = subprocess.run([adb, "-s", serial, "shell", "getprop", name],
                       capture_output=True, text=True, timeout=15)
    return p.stdout.strip()


def run_adb(adb, serial, snippet):
    p = subprocess.run([adb, "-s", serial, "shell", "sh", "-s"],
                       input=snippet, capture_output=True, text=True,
                       timeout=120)
    return p.returncode, p.stdout, p.stderr


def run_ssh(snippet):
    p = subprocess.run(SSH, input=snippet, capture_output=True, text=True,
                       timeout=120)
    return p.returncode, p.stdout, p.stderr


# ---------------------------------------------------------------------------
# modes
# ---------------------------------------------------------------------------

def windows_path(path):
    r"""Map a WSL path to the form Windows PowerShell can read.

    The repository lives in the WSL filesystem; Windows reaches it through the
    \\wsl.localhost\<distro>\... share, so the plan must print that form.
    """
    p = path.replace("\\", "/")
    m = re.match(r"^/home/([^/]+)/(.*)$", p)
    if not m:
        return path
    distro = "Ubuntu"
    try:
        out = subprocess.run(["wsl.exe", "-l", "-q"], capture_output=True,
                             text=True, timeout=10).stdout
        for line in out.splitlines():
            line = line.strip().lstrip("\u0000")
            if line:
                distro = line
                break
    except (OSError, subprocess.SubprocessError):
        pass
    return "\\\\wsl.localhost\\%s\\home\\%s\\%s" % (
        distro, m.group(1), m.group(2).replace("/", "\\"))


def cmd_plan(args):
    print("PLAN (no device is contacted, nothing is written)")
    print("remote snippet (read-only, one shot): %s" % SNIPPET)
    print()
    print("--- LineageOS, Windows adb.exe ---")
    print("resolved adb: %s" % find_adb(args.adb))
    print(r'$adb = "$env:USERPROFILE\Downloads\platform-tools\adb.exe"')
    print(r'& $adb devices')
    print(r'Get-Content "%s" | & $adb -s <SERIAL> shell sh -s' % windows_path(SNIPPET))
    print()
    print("--- Mobian, predefined SSH route (one attempt, no key inspection) ---")
    print(" ".join(SSH) + "   < " + SNIPPET)
    print()
    print("OS guard: exact membership in devices=%s and builds=%s" %
          (list(args.expect_device), list(args.expect_build)))
    print("attributes covered: %s" % ", ".join(REQUESTED))
    print("limits: %s" % LIMITS)
    return 0


def cmd_execute(args):
    snippet = open(SNIPPET, "r", encoding="utf-8").read()
    if args.os == "adb":
        adb = find_adb(args.adb)
        print(json.dumps({"step": "adb_path", "path": adb,
                          "exists": bool(adb) and os.path.exists(adb)},
                         indent=2))
        devices = adb_devices(adb)
        ready = [d for d in devices if d["state"] == "device"]
        print(json.dumps({"step": "adb_devices", "devices": devices,
                          "ready": len(ready)}, indent=2))
        if len(ready) != 1:
            print("STOP: exactly one authorised device is required, found %d "
                  "ready. Nothing else is attempted." % len(ready))
            return 2
        serial = ready[0]["serial"]
        props = {}
        for n in ("ro.product.device", "ro.product.name", "ro.lineage.version",
                  "ro.build.fingerprint", "ro.build.version.release"):
            props[n] = adb_getprop(adb, serial, n)
        ident = check_identity(props, tuple(args.expect_device),
                               tuple(args.expect_build))
        print(json.dumps({"step": "identity_guard", "report": ident}, indent=2))
        if ident["verdict"] != "ACCEPTED":
            print("STOP: identity guard rejected the device; no read performed.")
            return 3
        rc, out, err = run_adb(adb, serial, snippet)
        if rc != 0:
            print("STOP: adb read failed rc=%d\n%s" % (rc, err.strip()))
            return 3
    else:
        print(json.dumps({"step": "ssh_preflight",
                          "target": "root@172.16.42.1",
                          "note": "one attempt only"}, indent=2))
        rc, out, err = run_ssh(snippet)
        if rc != 0:
            print("STOP: SSH read failed rc=%d\n%s" % (rc, err.strip()))
            return 3
    parsed = parse(out)
    print(json.dumps(summarise(parsed), indent=2))
    return 0


def cmd_parse(args):
    with open(args.file, "r", encoding="utf-8") as fh:
        parsed = parse(fh.read())
    print(json.dumps(summarise(parsed), indent=2))
    return 0


def cmd_self_test():
    # --- 1. unreadable directory listing -> UNKNOWN, never ABSENT
    s = classify(parse("\n".join([
        "LIST /r FAILED Permission denied",
        "ATTR /r/clkscale_enable UNKNOWN 1 cat: /r/clkscale_enable: No such file",
    ])))
    assert s[0]["state"] == "UNKNOWN", s[0]
    assert s[0]["state"] != "ABSENT"

    # --- 2. listed but denied -> DENIED (explicit permission failure)
    s = classify(parse("\n".join([
        "LIST /r OK clkgate_enable clkscale_enable",
        "ATTR /r/clkgate_enable DENIED 1 cat: /r/clkgate_enable: Permission denied",
    ])))
    by = {v["attribute"]: v for v in s}
    assert by["clkgate_enable"]["state"] == "DENIED", by["clkgate_enable"]

    # --- 3. listed but unreadable for another reason -> LISTED_BUT_UNREADABLE
    s = classify(parse("\n".join([
        "LIST /r OK rpm_lvl",
        "ATTR /r/rpm_lvl UNKNOWN 1 cat: /r/rpm_lvl: Permission denied",
    ])))
    assert s[0]["state"] == "LISTED_BUT_UNREADABLE", s[0]

    # --- 4. true absence: successful listing without the name
    s = classify(parse("\n".join([
        "LIST /r OK clkgate_enable",
        "ATTR /r/clkscale_enable UNKNOWN 1 cat: /r/clkscale_enable: No such file",
    ])))
    assert s[0]["state"] == "ABSENT", s[0]

    # --- 5. both scaling spellings are covered and classified independently
    s = classify(parse("\n".join([
        "LIST /r OK clk_scaling_enable",
        "ATTR /r/clkscale_enable UNKNOWN 1 cat: /r/clkscale_enable: No such file",
        "ATTR /r/clk_scaling_enable DENIED 1 cat: /r/clk_scaling_enable: Permission denied",
    ])))
    by = {v["attribute"]: v for v in s}
    assert by["clkscale_enable"]["state"] == "ABSENT"
    assert by["clk_scaling_enable"]["state"] == "DENIED"

    # --- 6. no listing at all for the parent -> UNKNOWN
    s = classify(parse("ATTR /r/power/runtime_status UNKNOWN 1 nope"))
    assert s[0]["state"] == "UNKNOWN", s[0]

    # --- 7. OS guard: a substring match must NOT be accepted
    props = {"ro.product.device": "lmipro-x", "ro.product.name": "lineage_lmi",
             "ro.lineage.version": "23.2-20261007-NIGHTLY-lmi",
             "ro.build.fingerprint": "Redmi/lmipro/lmipro:12/abc/user-keys"}
    assert check_identity(props)["verdict"] == "REJECTED"

    # --- 8. OS guard: exact device and exact build are accepted
    props["ro.product.device"] = "lmipro"
    assert check_identity(props)["verdict"] == "ACCEPTED", check_identity(props)
    props["ro.product.device"] = "lmi"
    assert check_identity(props)["verdict"] == "ACCEPTED"

    # --- 9. OS guard: a different build is rejected (fail closed)
    props["ro.lineage.version"] = "23.2-20261008-NIGHTLY-lmi"
    assert check_identity(props)["verdict"] == "REJECTED"
    props["ro.lineage.version"] = "23.2-20261007-NIGHTLY-lmi"
    # --- 10. OS guard: a foreign ROM family is rejected
    props["ro.build.fingerprint"] = "Other/device/device:12/abc/user-keys"
    assert check_identity(props)["verdict"] == "REJECTED"

    print("SELF-TEST PASS: listing-based absence, failed listing -> UNKNOWN, "
          "listed-but-denied, listed-but-unreadable, true absence, both "
          "scaling names, strict identity guard")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--os", choices=["adb", "ssh"], default="adb")
    ap.add_argument("--adb", default=None)
    ap.add_argument("--expect-device", action="append",
                    default=list(EXPECTED_DEVICES))
    ap.add_argument("--expect-build", action="append",
                    default=list(EXPECTED_BUILDS))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("mode", nargs="?", default="plan",
                    choices=["plan", "parse"])
    ap.add_argument("file", nargs="?")
    args = ap.parse_args()

    if args.self_test:
        cmd_self_test()
        return 0
    if args.execute:
        if args.mode != "plan":
            ap.error("--execute is only valid with the plan mode")
        return cmd_execute(args)
    if args.mode == "parse":
        if not args.file:
            ap.error("parse mode needs a file")
        return cmd_parse(args)
    return cmd_plan(args)


if __name__ == "__main__":
    sys.exit(main())
