#!/usr/bin/env python3
"""
pm8150b-charger-targeted-read.py — releve cible du PM8150B (lmi, Mobian Linux 7)

But
---
Distinguer, sur un seul echantillon et sans rien ecrire :

  * terminaison normale     : 0x1006 bits[2:0] = 5 (TERMINATE) et 0x1070 = 0x50
  * reprise manquante       : 0x1007 bit6 (VBATT_LTET_RECHARGE) et 0x107E/0x107F
  * courant d'entree faible : 0x1370 (plafond), 0x1108 (limite effective),
                              0x110A bit6 (SOFT_ILIMIT), 0x1365 bit4
                              (ICL_OVERRIDE_AFTER_APSD), 0x1308 (APSD: SDP ?)
  * erreur d'affichage      : 0x4009/0x400A (MSOC brut) contre la tension
                              et le courant de la jauge

Regles strictes
---------------
  * lecture seule : aucun ecart de registre, aucune commande de charge,
    aucun changement de reglage, aucun arrimage de veille ;
  * pas de balayage : le regmap est resolu puis VERIFIE, on ne parcourt pas
    tous les regmaps de la machine pour deviner lequel est le bon ;
  * lectures ciblees : une seule ligne de debugfs par registre demande.

Resolution du regmap
--------------------
Le PMIC PM8150B est le pmic@2 du bus SPMI 0, donc son regmap debugfs est
"0-02". Le script deduit ce nom du device tree vivant
(/proc/device-tree/spmi@0/pmic@2/compatible) puis VERIFIE la signature du
PMIC avant toute lecture : les registres 0x1006 (chargeur) et 0x4009 (jauge)
doivent se trouver dans CE regmap. Un seul PMIC de ce modele possede les deux
blocs ; si la verification echoue, le script s'arrete au lieu de rendre une
mesure d'un autre peripherique. C'est exactement le defaut du script de
trajectoire MSOC, qui retenait le premier regmap contenant une adresse.

Usage sur l'appareil (Mobian, root) :

    python3 pm8150b-charger-targeted-read.py --once
    python3 pm8150b-charger-targeted-read.py --interval 10 --duration 3600 \
        --out /root/pm8150b-charger.csv

References
----------
  smb5-reg.h (CAF 4.19)  : 0x1006 CHG_STATUS_1, 0x1007 CHG_STATUS_2,
                           0x1042 CHG_ENABLE, 0x1051 CHGR_CFG2,
                           0x1070 FLOAT_VOLTAGE_CFG (3,6 V + code*10 mV),
                           0x107D seuil SOC, 0x107E/0x107F seuil VBAT,
                           0x1106 ICL_MAX_STATUS, 0x1107 ICL_STATUS,
                           0x1108 AICL_ICL_STATUS, 0x110A AICL_STATUS,
                           0x110B POWER_PATH_STATUS, 0x1307/0x1308 APSD,
                           0x1310 USBIN_INT_RT_STS, 0x1340 USBIN_CMD_IL,
                           0x1342 CMD_ICL_OVERRIDE, 0x1365 USBIN_LOAD_CFG,
                           0x1366 USBIN_ICL_OPTIONS,
                           0x1370 USBIN_CURRENT_LIMIT_CFG,
                           0x1380 USBIN_AICL_OPTIONS_CFG,
                           0x1506 TYPE_C_SNK_STATUS
  smb5-lib.h (CAF 4.19)  : VBAT_TO_VRAW_ADC(v) = v*1e6/194637
                           => mV du seuil VBAT = raw * 194637 / 1e6
"""

import argparse
import csv
import os
import re
import sys
import time

REG_DEBUGFS = os.environ.get("PM8150B_REG_DEBUGFS", "/sys/kernel/debug/regmap")
DT_ROOT = os.environ.get("PM8150B_DT_ROOT", "/proc/device-tree")
PSY_DIR = os.environ.get("PM8150B_PSY_DIR", "/sys/class/power_supply")

ROW_RE = re.compile(rb"^\s*([0-9a-fA-F]+):\s*([0-9a-fA-F]{2,4}|XX)\s*$")
HEADER_PROBE = 256

# --- Registres demandes, avec la question a laquelle chacun repond ---------
# (adresse, libelle, ce que la lecture permet de departager)
REGISTERS = [
    (0x1006, "CHG_STATUS_1",
     "etat de charge bits[2:0] (5=TERMINATE), bit6 courant de charge nul"),
    (0x1007, "CHG_STATUS_2",
     "bit6 VBATT_LTET_RECHARGE (reprise en cours), bit5 VBATT_GTET_INHIBIT, "
     "bit1 BAT_OV"),
    (0x1042, "CHG_ENABLE_CMD", "commande charge enable (ecrite par le pilote)"),
    (0x1051, "CHGR_CFG2",
     "bits[2:1] source du seuil de reprise (0b10=VBAT, 0b11=SOC), "
     "bit2 AUTO_RECHG, bit0 inhibe"),
    (0x1067, "ITERM_UP_MSB", "seuil ADC de fin de charge (partie haute)"),
    (0x1068, "ITERM_UP_LSB", "seuil ADC de fin de charge (partie basse)"),
    (0x1069, "ITERM_LO_MSB", "seuil ADC de fin de charge, borne basse (haut)"),
    (0x106A, "ITERM_LO_LSB", "seuil ADC de fin de charge, borne basse (bas)"),
    (0x106B, "TERM_RCHG_CFG", "recharge sans echantillon de courant"),
    (0x1070, "FLOAT_VOLTAGE_CFG",
     "tension de fin de charge : 3,6 V + code*10 mV (PM8150B)"),
    (0x107D, "RCHG_SOC_THRESHOLD",
     "seuil SOC de reprise ; inerte tant que 0x1051 bits[2:1] != 0b11"),
    (0x107E, "ADC_RCHG_THR_MSB", "seuil VBAT de reprise (partie haute)"),
    (0x107F, "ADC_RCHG_THR_LSB", "seuil VBAT de reprise (partie basse)"),
    (0x1106, "ICL_MAX_STATUS", "plafond de limite d'entree (50 mA par unite)"),
    (0x1107, "ICL_STATUS", "limite d'entree courante"),
    (0x1108, "AICL_ICL_STATUS", "limite d'entree EFFECTIVE (50 mA par unite)"),
    (0x110A, "AICL_STATUS", "bit0 fin de l'AICL, bit6 SOFT_ILIMIT (entree limite)"),
    (0x110B, "POWER_PATH_STATUS",
     "bit0 source d'entree valide, bit4 alimentation par USBIN, "
     "bit6 USBIN suspendu, bits[2:1] chemin d'alimentation"),
    (0x1307, "APSD_STATUS", "deroulement de la detection de source"),
    (0x1308, "APSD_RESULT_STATUS",
     "source detectee : bit0 SDP, bit2 CDP, bit3 DCP (etait SDP le 30/10)"),
    (0x1310, "USBIN_INT_RT_STS", "bit4 entree USB presente"),
    (0x1340, "USBIN_CMD_IL", "bit0 entree USB suspendue"),
    (0x1341, "CMD_APSD", "bit0 redemarrage de la detection"),
    (0x1342, "CMD_ICL_OVERRIDE", "bit1 surcharge de la limite d'entree"),
    (0x1365, "USBIN_LOAD_CFG",
     "bit4 ICL_OVERRIDE_AFTER_APSD : impose la limite d'apres l'APSD"),
    (0x1366, "USBIN_ICL_OPTIONS", "bit0 mode de charge USB2"),
    (0x1370, "USBIN_CURRENT_LIMIT_CFG",
     "PLAFOND de la limite d'entree ecrite (50 mA par unite) : 10 = 500 mA"),
    (0x1380, "USBIN_AICL_OPTIONS_CFG",
     "bit2 AICL actif, bit4 rerun periodique, bit3 ADC, "
     "bit7 suspension sur effondrement de l'entree"),
    (0x1506, "TYPE_C_SNK_STATUS",
     "capacite annoncee par la source : bit1 Rp 3,0 A, bit2 Rp 1,5 A, "
     "bit3 Rp defaut (etait Rp 1,5 A le 30/10)"),
    (0x1509, "TYPE_C_STATE_MACHINE_STATUS", "etat de la machine d'etat Type-C"),
    (0x150B, "TYPE_C_MISC_STATUS", "bit0 CC attache, bit1 orientation"),
    (0x4009, "FG_MSOC", "MSOC brut de la jauge (0..255)"),
    (0x400A, "FG_MSOC_SHADOW", "miroir du MSOC (controle de coherence)"),
]

CHARGER_STATES = {
    0: "TRICKLE", 1: "PRE", 2: "FAST", 3: "FULLON",
    4: "TAPER", 5: "TERMINATE", 6: "INHIBIT", 7: "DISABLE",
}

# Signature du PM8150B : le bloc chargeur (0x1000) et le bloc jauge (0x4000)
# sont dans le meme PMIC, donc dans le meme regmap.
SIGNATURE = (0x1006, 0x4009)


def log(msg):
    print(msg, flush=True)


class RegMap:
    """Vue ciblee d'un fichier regmap debugfs : pread unitaire, adresse revalidee."""

    def __init__(self, path, first_addr, step, stride, size=0):
        self.path = path
        self.first_addr = first_addr
        self.step = step
        self.stride = stride
        self.size = size
        self.fd = None

    @classmethod
    def probe(cls, path):
        try:
            fd = os.open(path, os.O_RDONLY)
        except OSError:
            return None
        try:
            size = os.fstat(fd).st_size
            buf = os.pread(fd, HEADER_PROBE, 0)
        except OSError:
            os.close(fd)
            return None
        rows = []
        for line in buf.split(b"\n"):
            m = ROW_RE.match(line)
            if m:
                rows.append((int(m.group(1), 16), m.group(2), len(line) + 1))
        if len(rows) < 2:
            os.close(fd)
            return None
        widths = {}
        for _a, _v, w in rows:
            widths[w] = widths.get(w, 0) + 1
        stride = max(widths.items(), key=lambda kv: kv[1])[0]
        sel = [r for r in rows if r[2] == stride]
        if len(sel) < 2:
            os.close(fd)
            return None
        first_addr = sel[0][0]
        step = sel[1][0] - first_addr
        if step <= 0:
            os.close(fd)
            return None
        obj = cls(path, first_addr, step, stride, size)
        obj.fd = fd
        return obj

    def _offset(self, addr):
        if addr < self.first_addr:
            return None
        if (addr - self.first_addr) % self.step:
            return None
        idx = (addr - self.first_addr) // self.step
        off = idx * self.stride
        if self.size and off + self.stride > self.size:
            return None
        return off

    def read(self, addr):
        """Valeur brute du registre, ou None si la ligne ne se revalide pas."""
        off = self._offset(addr)
        if off is None:
            return None
        try:
            buf = os.pread(self.fd, self.stride, off)
        except OSError:
            return None
        line = buf.split(b"\n")[0]
        m = ROW_RE.match(line)
        if not m:
            return None
        if int(m.group(1), 16) != addr:
            return None
        try:
            return int(m.group(2), 16)
        except ValueError:
            return None

    def close(self):
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None


def dt_pmic_regmap_name():
    """Nom du regmap debugfs du PMIC PM8150B, deduit du device tree vivant."""
    for dirpath, _dirnames, _files in os.walk(DT_ROOT):
        compat = os.path.join(dirpath, "compatible")
        if not os.path.isfile(compat):
            continue
        try:
            with open(compat, "rb") as fh:
                blob = fh.read()
        except OSError:
            continue
        if b"pm8150b" not in blob:
            continue
        # spmi@0/pmic@2 -> bus SPMI 0, USID 2 -> regmap "0-02"
        node = os.path.basename(dirpath)
        if "@" not in node:
            continue
        usid = node.split("@", 1)[1]
        try:
            usid_value = int(usid, 16)
        except ValueError:
            continue
        return "0-%02x" % usid_value, dirpath
    return None, None


def resolve_regmap(explicit=None):
    """Retourne (chemin, RegMap) pour le regmap du PM8150B, apres verification."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    else:
        name, dtpath = dt_pmic_regmap_name()
        if name:
            log("device tree : %s -> regmap %s" % (dtpath, name))
            candidates.append(name)
        candidates.append("0-02")

    seen = set()
    for name in candidates:
        if name in seen:
            continue
        seen.add(name)
        path = os.path.join(REG_DEBUGFS, name, "registers")
        if not os.path.exists(path):
            log("regmap %s : absent" % name)
            continue
        rm = RegMap.probe(path)
        if rm is None:
            log("regmap %s : format debugfs non reconnu" % name)
            continue
        # Verification de signature : le PM8150B expose le bloc chargeur ET
        # le bloc jauge. Un regmap qui n'a pas les deux n'est pas le bon.
        if all(rm.read(a) is not None for a in SIGNATURE):
            log("regmap %s : signature PM8150B confirmee (0x1006 + 0x4009)"
                % name)
            return path, rm
        rm.close()
        log("regmap %s : signature PM8150B absente, ecarte" % name)

    return None, None


def read_psy(name, base=PSY_DIR):
    try:
        with open(os.path.join(base, name), "r") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def battery_psy():
    if not os.path.isdir(PSY_DIR):
        return ""
    for entry in sorted(os.listdir(PSY_DIR)):
        try:
            with open(os.path.join(PSY_DIR, entry, "type"), "r") as fh:
                if fh.read().strip() == "Battery":
                    return entry
        except OSError:
            continue
    return ""


def sample(rm):
    """Un echantillon : registres cibles + etat de la jauge."""
    row = {"iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for addr, label, _why in REGISTERS:
        value = rm.read(addr)
        row["0x%04x" % addr] = "" if value is None else "0x%x" % value
        row[label] = "" if value is None else value
    psy = battery_psy()
    for prop in ("capacity", "status", "voltage_now", "current_now"):
        row[prop] = read_psy(prop, os.path.join(PSY_DIR, psy)) if psy else ""
    row["charger_psy"] = read_psy("online", os.path.join(PSY_DIR, "pm8150b-charger"))
    return row


def decode(row):
    """Lecture commentee de l'echantillon."""
    out = []

    def get(addr):
        v = row.get("0x%04x" % addr)
        return None if v in (None, "") else int(v, 16)

    status1 = get(0x1006)
    if status1 is not None:
        out.append("0x1006 = 0x%02x : etat %s%s"
                   % (status1,
                      CHARGER_STATES.get(status1 & 0x07, "?"),
                      ", bit6 courant de charge nul" if status1 & 0x40 else ""))
    status2 = get(0x1007)
    if status2 is not None:
        out.append("0x1007 = 0x%02x : %s"
                   % (status2,
                      ", ".join(filter(None, [
                          "VBATT_LTET_RECHARGE" if status2 & 0x40 else "",
                          "VBATT_GTET_INHIBIT" if status2 & 0x20 else "",
                          "BATT_GT_FULL_ON" if status2 & 0x08 else "",
                          "BAT_OV" if status2 & 0x02 else "",
                      ])) or "aucun evenement"))
    cfg2 = get(0x1051)
    if cfg2 is not None:
        source = {0: "aucune", 1: "SOC", 2: "VBAT", 3: "SOC+VBAT"}.get(
            (cfg2 >> 1) & 0x03, "?")
        out.append("0x1051 = 0x%02x : reprise %s, AUTO_RECHG=%d, inhibe=%d"
                   % (cfg2, source, (cfg2 >> 2) & 1, cfg2 & 1))
    fv = get(0x1070)
    if fv is not None:
        out.append("0x1070 = %d -> float %d mV (3,6 V + code*10 mV)"
                   % (fv, (3600000 + fv * 10000) // 1000))
    msb = get(0x107E)
    lsb = get(0x107F)
    if msb is not None and lsb is not None:
        raw = (msb << 8) | lsb
        out.append("0x107e/0x107f = 0x%04x -> seuil de reprise %.1f mV "
                   "(raw * 194637 / 1e6)" % (raw, raw * 194637 / 1000000))
    for addr, label in ((0x1370, "plafond d'entree"),
                         (0x1108, "limite d'entree effective"),
                         (0x1106, "plafond d'entree (statut)")):
        v = get(addr)
        if v is not None:
            out.append("0x%04x = %d -> %s %d mA" % (addr, v, label, v * 50))
    aicl = get(0x110A)
    if aicl is not None:
        out.append("0x110a = 0x%02x : AICL %s, %s"
                   % (aicl,
                      "termine" if aicl & 0x01 else "en cours",
                      "limite souple (entree s'effondre)" if aicl & 0x40 else
                      "pas de limite souple"))
    load = get(0x1365)
    if load is not None:
        out.append("0x1365 = 0x%02x : %s"
                   % (load,
                      "l'APSD impose la limite d'entree" if load & 0x10 else
                      "l'APSD n'impose pas la limite d'entree"))
    apsd = get(0x1308)
    if apsd is not None:
        kind = []
        for bit, name in ((0, "SDP"), (1, "OCP"), (2, "CDP"), (3, "DCP"),
                          (4, "FLOAT"), (5, "QC2"), (6, "QC3")):
            if apsd & (1 << bit):
                kind.append(name)
        out.append("0x1308 = 0x%02x : source vue par l'APSD : %s"
                   % (apsd, ", ".join(kind) or "aucune"))
    snk = get(0x1506)
    if snk is not None:
        rp = []
        if snk & 0x02:
            rp.append("Rp 3,0 A")
        if snk & 0x04:
            rp.append("Rp 1,5 A")
        if snk & 0x08:
            rp.append("Rp defaut")
        out.append("0x1506 = 0x%02x : capacite de la source : %s"
                   % (snk, ", ".join(rp) or "aucune"))
    pp = get(0x110B)
    if pp is not None:
        out.append("0x110b = 0x%02x : source valide=%d, alimentation USBIN=%d, "
                   "USBIN suspendu=%d" % (pp, pp & 1, (pp >> 4) & 1, (pp >> 6) & 1))
    msoc = get(0x4009)
    shadow = get(0x400A)
    if msoc is not None:
        out.append("0x4009 = %d (0x%x), miroir 0x400a = %s : %s"
                   % (msoc, msoc,
                      "identique" if shadow == msoc else "DIVERGENT",
                      "MSOC brut, jauge non tear-safe" if shadow != msoc
                      else "MSOC brut"))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--regmap", default=None,
                    help="nom du regmap debugfs (defaut : deduit du device tree)")
    ap.add_argument("--once", action="store_true", help="un seul echantillon")
    ap.add_argument("--interval", type=float, default=10.0,
                    help="intervalle entre echantillons, en secondes")
    ap.add_argument("--duration", type=float, default=0.0,
                    help="duree totale du suivi, en secondes")
    ap.add_argument("--out", default=None, help="fichier CSV de sortie")
    args = ap.parse_args()

    path, rm = resolve_regmap(args.regmap)
    if rm is None:
        log("ECHEC : aucun regmap PM8150B verifie. Aucun releve n'est produit.")
        return 2

    log("regmap retenu : %s" % path)
    log("cable present d'apres 0x1310 bit4 : %s"
        % ("oui" if (rm.read(0x1310) or 0) & 0x10 else "non"))
    log("")

    writer = None
    fh = None
    if args.out:
        fh = open(args.out, "w", newline="")
        writer = csv.DictWriter(fh, fieldnames=list(sample(rm).keys()))
        writer.writeheader()

    try:
        deadline = time.time() + args.duration if args.duration else None
        while True:
            row = sample(rm)
            log("=== %s ===" % row["iso"])
            for line in decode(row):
                log("  " + line)
            log("  jauge : %s %% / %s / %s uV / %s uA"
                % (row.get("capacity"), row.get("status"),
                   row.get("voltage_now"), row.get("current_now")))
            log("")
            if writer:
                writer.writerow(row)
                fh.flush()
            if args.once:
                break
            if deadline is not None and time.time() >= deadline:
                break
            time.sleep(args.interval)
    finally:
        rm.close()
        if fh:
            fh.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
