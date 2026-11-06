#!/usr/bin/env python3
"""Summarize collector JSONL into cautious, actionable correlations."""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def records(path):
    with Path(path).open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid JSON on line {line_no}: {exc}") from exc


def valid_boot_id(value):
    return isinstance(value, str) and bool(value.strip()) and not value.startswith("{")


def analyze(rows):
    samples = [r for r in rows if r.get("event") == "sample"]
    findings = []
    warnings = []
    legacy_process_rows = 0
    cpu_ticks = defaultdict(int)
    cpu_processes = {}
    unit_ticks = defaultdict(int)
    explicit_deltas = any("baseline_only" in r.get("process_activity", {}) for r in samples)
    omitted_active = 0
    if explicit_deltas:
        for sample in samples:
            activity = sample.get("process_activity", {})
            if not valid_boot_id(sample.get("boot_id")):
                warnings.append("CPU delta skipped: boot_id missing or invalid.")
                continue
            omitted_active += activity.get("omitted_active", 0)
            for current in activity.get("processes", []):
                delta = current.get("cpu_ticks_delta", 0)
                if not isinstance(delta, int) or delta <= 0 or current.get("start_ticks") is None:
                    continue
                identity = (sample.get("boot_id"), current.get("pid"), current.get("start_ticks"))
                cpu_ticks[identity] += delta
                cpu_processes[identity] = current
                units = current.get("cgroup_units") or ["(no systemd unit/scope found)"]
                for unit in units:
                    unit_ticks[unit] += delta
        if omitted_active:
            warnings.append(f"{omitted_active} active process entries were outside the per-sample top-process cap.")
    else:
        for before, after in zip(samples, samples[1:]):
            boot_before, boot_after = before.get("boot_id"), after.get("boot_id")
            if not valid_boot_id(boot_before) or not valid_boot_id(boot_after):
                warnings.append("CPU delta skipped: boot_id missing or invalid from one or both adjacent samples.")
                continue
            if boot_before != boot_after:
                continue
            old_rows = before.get("process_activity", {}).get("processes", [])
            new_rows = after.get("process_activity", {}).get("processes", [])
            legacy_process_rows += sum("start_ticks" not in p for p in old_rows + new_rows)
            old = { (p.get("pid"), p.get("start_ticks")): p for p in old_rows
                    if p.get("pid") is not None and p.get("start_ticks") is not None }
            new = { (p.get("pid"), p.get("start_ticks")): p for p in new_rows
                    if p.get("pid") is not None and p.get("start_ticks") is not None }
            for identity, current in new.items():
                prior = old.get(identity)
                if prior is None:
                    continue
                delta = current.get("cpu_ticks_total", 0) - prior.get("cpu_ticks_total", 0)
                if delta <= 0:
                    continue
                identity = (boot_after, *identity)
                cpu_ticks[identity] += delta
                cpu_processes[identity] = current
                units = current.get("cgroup_units") or ["(no systemd unit/scope found)"]
                for unit in units:
                    unit_ticks[unit] += delta

    if cpu_ticks:
        ranked = sorted(cpu_ticks, key=cpu_ticks.get, reverse=True)[:8]
        findings.append({"kind": "observed_cpu_activity", "processes": [
            {"boot_id": k[0], "pid": cpu_processes[k]["pid"], "start_ticks": cpu_processes[k]["start_ticks"],
             "comm": cpu_processes[k].get("comm"), "cpu_tick_delta": cpu_ticks[k],
             "cgroup_units": cpu_processes[k].get("cgroup_units", [])}
            for k in ranked], "unit_cpu_tick_delta": dict(sorted(unit_ticks.items(),
                                                                  key=lambda item: item[1], reverse=True)[:8]),
            "omitted_active_entries": omitted_active,
            "meaning": "CPU activity context only; not watts, energy, or proof of battery drain."})

    if len(samples) >= 2:
        first, last = samples[0], samples[-1]
        blockers = {}
        for sample in samples:
            inhibitors = sample.get("logind_inhibitors", [])
            if isinstance(inhibitors, list):
                process_by_pid = {p.get("pid"): p for p in
                                  sample.get("process_activity", {}).get("processes", [])}
                for item in inhibitors:
                    if ("sleep" in str(item.get("what", "")).split(":") and
                            item.get("mode") == "block"):
                        proc = process_by_pid.get(item.get("pid"), {})
                        key = (item.get("who"), item.get("why"), item.get("mode"), item.get("pid"),
                               proc.get("comm"), ", ".join(proc.get("cgroup_units", [])))
                        blockers[key] = blockers.get(key, 0) + 1
        same_boot = (valid_boot_id(first.get("boot_id")) and
                     first.get("boot_id") == last.get("boot_id"))
        try:
            if not same_boot:
                raise ValueError("boot identity missing or changed")
            succeeded = int(last.get("suspend_success")) - int(first.get("suspend_success"))
            failed = int(last.get("suspend_fail")) - int(first.get("suspend_fail"))
        except (TypeError, ValueError):
            succeeded = failed = None
        if blockers and succeeded == 0 and same_boot:
            findings.append({"kind": "sleep_inhibitors_seen_without_success_delta",
                             "holders": [{"who": k[0], "why": k[1], "mode": k[2], "pid": k[3],
                                          "comm": k[4], "cgroup_units": k[5],
                                          "samples_seen": n}
                                         for k, n in sorted(blockers.items(), key=lambda x: x[1], reverse=True)],
                             "next_step": "Correlate holder lifetime and inhibitor mode with the no-suspend interval; this is not causal proof."})
        delay_inhibitors = {}
        for sample in samples:
            inhibitors = sample.get("logind_inhibitors", [])
            if isinstance(inhibitors, list):
                for item in inhibitors:
                    if "sleep" in str(item.get("what", "")).split(":") and item.get("mode") == "delay":
                        key = (item.get("who"), item.get("why"), item.get("pid"))
                        delay_inhibitors[key] = delay_inhibitors.get(key, 0) + 1
        if delay_inhibitors:
            findings.append({"kind": "sleep_delay_inhibitors_observed", "holders": [
                {"who": k[0], "why": k[1], "pid": k[2], "samples_seen": count}
                for k, count in delay_inhibitors.items()],
                "meaning": "Delay inhibitors can defer a transition temporarily; presence alone is not evidence they prevented suspension."})
        findings.append({"kind": "suspend_counter_delta", "success": succeeded, "fail": failed,
                         "last_resume_reason": last.get("last_resume_reason")})
        findings.append({"kind": "battery_endpoint_readings", "first": first.get("battery"),
                         "last": last.get("battery"),
                         "meaning": "Device-level gauge readings; endpoints alone do not isolate workload or process."})

    requests = [r for r in rows if r.get("event") == "logind-request"]
    if requests:
        findings.append({"kind": "logind_requests", "requests": [
            {"recorded_wall_utc": r.get("wall_utc"),
             "request_wall_utc": r.get("request_wall_utc"),
             "request_boottime": r.get("request_boottime"), "method": r.get("method"),
             "caller": r.get("caller"), "body": r.get("body")} for r in requests]})
    sleep_events = [r for r in rows if r.get("event") == "prepare-for-sleep"]
    if sleep_events:
        findings.append({"kind": "sleep_wake_events", "events": [
            {"wall_utc": r.get("wall_utc"), "boottime": r.get("boottime"),
             "suspending": r.get("suspending")} for r in sleep_events]})
    if legacy_process_rows:
        warnings.append(f"{legacy_process_rows} legacy process entries lack start_ticks; their CPU activity was omitted to avoid PID-reuse attribution.")
    return {"samples": len(samples), "findings": findings, "warnings": sorted(set(warnings)),
            "limitations": ["No per-process power/energy measurement.",
                            "Correlation does not establish causation.",
                            "Processes absent from either endpoint or restarted between samples have no CPU delta."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", help="collector JSONL")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of readable text")
    args = parser.parse_args()
    report = analyze(list(records(args.capture)))
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Échantillons : {report['samples']}")
        for warning in report["warnings"]:
            print(f"\nAVERTISSEMENT : {warning}")
        for finding in report["findings"]:
            print(f"\n[{finding['kind']}]")
            print(json.dumps(finding, indent=2, ensure_ascii=False))
        print("\nLimites : " + " ".join(report["limitations"]))


if __name__ == "__main__":
    main()
