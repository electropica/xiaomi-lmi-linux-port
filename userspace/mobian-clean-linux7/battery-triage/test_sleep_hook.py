import json
import os
import tempfile
import unittest
from pathlib import Path

from sleep_hook import append_private, main, snapshot


class SleepHookTests(unittest.TestCase):
    def write(self, root, absolute, value):
        path = root / absolute.lstrip("/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)
        return path

    def test_snapshot_reads_boundaries_and_preserves_zero_as_text(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write(root, "/proc/sys/kernel/random/boot_id", "boot-test\n")
            self.write(root, "/proc/uptime", "123.45 60.00\n")
            self.write(root, "/sys/power/suspend_stats/success", "2\n")
            self.write(root, "/sys/power/suspend_stats/fail", "0\n")
            self.write(root, "/sys/kernel/debug/qcom_stats/aosd", "0\n")
            self.write(root, "/sys/kernel/debug/qcom_stats/cxsd", "5\n")
            self.write(root, "/sys/kernel/debug/qcom_stats/ddr_stats", "0\n")
            self.write(root, "/sys/class/power_supply/qcom-battery/capacity", "81\n")
            self.write(root, "/sys/class/power_supply/qcom-battery/current_now", "-22000\n")
            self.write(root, "/sys/class/backlight/panel0-backlight/bl_power", "4\n")
            record = snapshot("post", "suspend", root)
            self.assertEqual(record["phase"], "post")
            self.assertEqual(record["qcom_stats"]["aosd"], "0")
            self.assertEqual(record["qcom_stats"]["cxsd"], "5")
            self.assertEqual(record["suspend_stats"]["success"], "2")
            self.assertEqual(record["power_supplies"]["qcom-battery"]["current_now"], "-22000")
            self.assertEqual(record["backlights"]["panel0-backlight"]["bl_power"], "4")
            self.assertIn("not evidence of zero energy", record["interpretation"])

    def test_absent_debugfs_is_reported_without_mount_attempt(self):
        with tempfile.TemporaryDirectory() as temp:
            record = snapshot("pre", "suspend", Path(temp))
            self.assertIn("unavailable", record["qcom_stats"]["aosd"])
            self.assertEqual(record["qcom_stats"]["aosd"]["unavailable"], "FileNotFoundError")

    def test_append_is_private_and_invalid_phase_is_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "hook.jsonl"
            append_private(log, {"phase": "pre"})
            append_private(log, {"phase": "post"})
            rows = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual([row["phase"] for row in rows], ["pre", "post"])
            self.assertEqual(os.stat(log).st_mode & 0o777, 0o600)
            env_key = "MOBIAN_TRIAGE_SLEEP_HOOK_LOG"
            old = os.environ.get(env_key)
            try:
                os.environ[env_key] = str(root / "ignored.jsonl")
                self.assertEqual(main(["other", "suspend"]), 0)
                self.assertFalse((root / "ignored.jsonl").exists())
            finally:
                if old is None:
                    os.environ.pop(env_key, None)
                else:
                    os.environ[env_key] = old

    def test_refuses_links_without_modifying_their_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / 'target'
            target.write_text('untouched')
            sym = root / 'symlink'
            sym.symlink_to(target)
            hard = root / 'hardlink'
            os.link(target, hard)
            for link in (sym, hard):
                with self.assertRaises(OSError):
                    append_private(link, {'test': True})
            self.assertEqual(target.read_text(), 'untouched')


if __name__ == "__main__":
    unittest.main()
