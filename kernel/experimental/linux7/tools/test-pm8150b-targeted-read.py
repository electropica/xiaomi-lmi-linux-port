#!/usr/bin/env python3
"""Offline check of pm8150b-charger-targeted-read.py.

Builds a synthetic regmap debugfs file, points the script at it and checks
that it selects the right device, reads only the wanted registers and
decodes them.  Nothing is executed against the handset.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "pm8150b-charger-targeted-read.py")

HEADER = ("0-02.regmap\n" + "# padding\n" * 30)[:256].ljust(256, "#")

# Valeurs de reference, prises sur les captures du 30/10 et du 01/11.
VALUES = {
    0x1006: 0x45,
    0x1007: 0x28,
    0x1042: 0x01,
    0x1051: 0x2C,
    0x1067: 0x00,
    0x1068: 0x00,
    0x1069: 0x00,
    0x106A: 0x00,
    0x106B: 0x00,
    0x1070: 0x50,
    0x107D: 0xF2,
    0x107E: 0x57,
    0x107F: 0x4B,
    0x1106: 0x0A,
    0x1107: 0x0A,
    0x1108: 0x0A,
    0x110A: 0x41,
    0x110B: 0x95,
    0x1307: 0x11,
    0x1308: 0x01,
    0x1310: 0x10,
    0x1340: 0x00,
    0x1341: 0x00,
    0x1342: 0x00,
    0x1365: 0xB5,
    0x1366: 0x03,
    0x1370: 0x0A,
    0x1380: 0x00,
    0x1506: 0x04,
    0x1509: 0x23,
    0x150B: 0x29,
    0x4009: 0xF6,
    0x400A: 0xF6,
}

ROW_RE = re.compile(rb"^\s*([0-9a-fA-F]+):\s*([0-9a-fA-F]{2,4}|XX)\s*$")


def build_map(path, values):
    """Ecrit un fichier regmap debugfs synthetique, format 8 bits, pas de 1."""
    with open(path, "wb") as fh:
        for addr in range(0x0000, 0x8000):
            fh.write(("%04x: %02x\n" % (addr, values.get(addr, 0x00) & 0xFF)).encode())


def main():
    tmp = tempfile.mkdtemp(prefix="pm8150b-selftest-")
    try:
        good = os.path.join(tmp, "regmap", "0-02")
        bad = os.path.join(tmp, "regmap", "0-05")
        os.makedirs(good)
        os.makedirs(bad)
        build_map(os.path.join(good, "registers"), VALUES)
        # Un regmap qui ne sert pas le PM8150B : la signature doit le rejeter.
        build_map(os.path.join(bad, "registers"), {0x1006: 0x00})

        env = dict(os.environ)
        env["PM8150B_REG_DEBUGFS"] = os.path.join(tmp, "regmap")
        env["PM8150B_PSY_DIR"] = os.path.join(tmp, "psy")
        os.makedirs(env["PM8150B_PSY_DIR"])

        out = subprocess.run([sys.executable, SCRIPT, "--once"],
                             capture_output=True, text=True, env=env)
        print(out.stdout)
        if out.returncode != 0:
            print(out.stderr)
            print("ECHEC : code de retour %d" % out.returncode)
            return 1

        text = out.stdout
        checks = [
            ("signature confirmee", "signature PM8150B confirmee" in text),
            ("etat TERMINATE", "TERMINATE" in text),
            ("float 4400 mV", "float 4400 mV" in text),
            ("seuil de reprise decode", "seuil de reprise 4349.6" in text),
            ("plafond 500 mA", "plafond d'entree 500 mA" in text),
            ("limite effective 500 mA", "limite d'entree effective 500 mA" in text),
            ("APSD SDP", "SDP" in text),
            ("Rp 1,5 A", "Rp 1,5 A" in text),
            ("ICL impose par l'APSD", "l'APSD impose la limite d'entree" in text),
            ("MSOC 246", "0x4009 = 246" in text),
        ]
        bad_checks = [name for name, ok in checks if not ok]
        for name, ok in checks:
            print("%-32s %s" % (name, "ok" if ok else "MANQUE"))
        if bad_checks:
            print("ECHEC : %s" % ", ".join(bad_checks))
            return 1
        print("SELFTEST_OK")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
