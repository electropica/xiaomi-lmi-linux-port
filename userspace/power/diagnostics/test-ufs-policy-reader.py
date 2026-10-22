#!/usr/bin/env python3
"""Tests for the UFS suspend-policy reader classifier and identity guard.

Run from the repository root:

    python3 userspace/power/diagnostics/test-ufs-policy-reader.py

The reader classifies a failed attribute read from the DIRECTORY LISTING,
never from a bare existence test. On this platform the unprivileged adb shell
is denied getattr() by SELinux on the UFS attribute files, so `[ -e ]` is
false for entries that exist: a refusal must never be reported as an absence,
and a failed listing must never be reported as an absence either.
"""

import importlib.util
import pathlib
import sys

READER = pathlib.Path(__file__).with_name("ufs-policy-read.py")
spec = importlib.util.spec_from_file_location("ufs_policy_read", READER)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def verdict(attribute, lines):
    out = reader.classify(reader.parse("\n".join(lines)))
    return {v["attribute"]: v for v in out}[attribute]


def test_failed_listing_is_unknown():
    v = verdict("clkscale_enable", [
        "LIST /r FAILED Permission denied",
        "ATTR /r/clkscale_enable UNKNOWN 1 cat: /r/clkscale_enable: No such file",
    ])
    assert v["state"] == "UNKNOWN", v
    assert v["state"] != "ABSENT"


def test_explicit_permission_failure_is_denied():
    v = verdict("clkgate_enable", [
        "LIST /r OK clkgate_enable",
        "ATTR /r/clkgate_enable DENIED 1 cat: /r/clkgate_enable: Permission denied",
    ])
    assert v["state"] == "DENIED", v
    assert v["errno"] == "1", v


def test_listed_but_unreadable_is_not_absence():
    v = verdict("rpm_lvl", [
        "LIST /r OK rpm_lvl",
        "ATTR /r/rpm_lvl UNKNOWN 1 cat: /r/rpm_lvl: Permission denied",
    ])
    assert v["state"] == "LISTED_BUT_UNREADABLE", v


def test_true_absence():
    v = verdict("clkscale_enable", [
        "LIST /r OK clkgate_enable",
        "ATTR /r/clkscale_enable UNKNOWN 1 cat: /r/clkscale_enable: No such file",
    ])
    assert v["state"] == "ABSENT", v


def test_both_scaling_spellings_are_independent():
    lines = [
        "LIST /r OK clk_scaling_enable",
        "ATTR /r/clkscale_enable UNKNOWN 1 cat: /r/clkscale_enable: No such file",
        "ATTR /r/clk_scaling_enable DENIED 1 cat: /r/clk_scaling_enable: Permission denied",
    ]
    out = {v["attribute"]: v for v in reader.classify(reader.parse("\n".join(lines)))}
    assert out["clkscale_enable"]["state"] == "ABSENT", out["clkscale_enable"]
    assert out["clk_scaling_enable"]["state"] == "DENIED", out["clk_scaling_enable"]


def test_no_listing_for_parent_is_unknown():
    v = verdict("runtime_status", [
        "ATTR /r/power/runtime_status UNKNOWN 1 cat: ...: No such file",
    ])
    assert v["state"] == "UNKNOWN", v


def test_identity_guard_rejects_substring_match():
    props = {
        "ro.product.device": "lmipro-x",
        "ro.product.name": "lineage_lmi",
        "ro.lineage.version": "23.2-20261007-NIGHTLY-lmi",
        "ro.build.fingerprint": "Redmi/lmipro/lmipro:12/abc/user-keys",
    }
    assert reader.check_identity(props)["verdict"] == "REJECTED"


def test_identity_guard_accepts_exact_device_and_build():
    props = {
        "ro.product.device": "lmipro",
        "ro.product.name": "lineage_lmi",
        "ro.lineage.version": "23.2-20261007-NIGHTLY-lmi",
        "ro.build.fingerprint": "Redmi/lmipro/lmipro:12/abc/user-keys",
    }
    assert reader.check_identity(props)["verdict"] == "ACCEPTED"
    props["ro.product.device"] = "lmi"
    assert reader.check_identity(props)["verdict"] == "ACCEPTED"


def test_identity_guard_fails_closed_on_other_builds():
    props = {
        "ro.product.device": "lmipro",
        "ro.product.name": "lineage_lmi",
        "ro.lineage.version": "23.2-20261008-NIGHTLY-lmi",
        "ro.build.fingerprint": "Redmi/lmipro/lmipro:12/abc/user-keys",
    }
    assert reader.check_identity(props)["verdict"] == "REJECTED"
    props["ro.lineage.version"] = "23.2-20261007-NIGHTLY-lmi"
    props["ro.build.fingerprint"] = "Other/device/device:12/abc/user-keys"
    assert reader.check_identity(props)["verdict"] == "REJECTED"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS %s" % t.__name__)
    print("%d tests passed" % len(tests))
    return 0


if __name__ == "__main__":
    sys.exit(main())
