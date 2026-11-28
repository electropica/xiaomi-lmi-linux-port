#!/usr/bin/env python3
"""Compile the actual status function with mocked read-only hardware values."""
from pathlib import Path
import subprocess,sys,tempfile
if len(sys.argv)!=2:
    raise SystemExit('Usage: test-charger-status-host.py SOURCE_DIRECTORY')
src=(Path(sys.argv[1])/'drivers/power/supply/qcom_pm8150b_charger.c').read_text()
start=src.index('static int smb5_get_prop_status(')
end=src.index('static inline int smb5_get_current_limit(',start)
function=src[start:end]
harness=r'''
#include <stdio.h>
#include <stdbool.h>
#define BATTERY_CHARGER_STATUS_1 6
#define BATTERY_CHARGER_STATUS_MASK 7
#define VBATT_GTET_INHIBIT_BIT 32
#define POWER_SUPPLY_STATUS_CHARGING 1
#define POWER_SUPPLY_STATUS_DISCHARGING 2
#define POWER_SUPPLY_STATUS_NOT_CHARGING 3
#define POWER_SUPPLY_STATUS_FULL 4
#define POWER_SUPPLY_STATUS_UNKNOWN 0
#define dev_err(...) ((void)0)
enum {TRICKLE_CHARGE, PRE_CHARGE, FAST_CHARGE, FULLON_CHARGE, TAPER_CHARGE,
      TERMINATE_CHARGE, INHIBIT_CHARGE, DISABLE_CHARGE};
struct smb5_chip { void *regmap; int base; void *dev; bool reached_taper; };
static int online, status1, status2;
static int smb5_get_prop_usb_online(struct smb5_chip *c, int *out)
{ (void)c; *out=online; return 0; }
static int regmap_bulk_read(void *m, int r, void *out, int n)
{ unsigned char *s=out; (void)m; (void)r; (void)n; s[0]=status1; s[1]=status2; return 0; }
static void smb5_track_charge_state(struct smb5_chip *c, int s) { (void)c; (void)s; }
'''+function+r'''
static int test(int plugged,int one,int two,int want)
{ struct smb5_chip c={0}; int got=-1; online=plugged; status1=one; status2=two;
  if (smb5_get_prop_status(&c,&got) || got!=want) { fprintf(stderr,"FAIL %d %d %d got %d expected %d\n",plugged,one,two,got,want); return 1; } return 0; }
int main(void) {
 if (test(0,3,0x28,2) || test(1,3,0x28,1) || test(1,4,0x20,1) ||
     test(1,7,0,3) || test(1,7,0x20,4) || test(1,5,0,4)) return 1;
 puts("CHARGER_STATUS_6_CASES_PASS"); return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='lmi-charger-status-') as tmp:
    p=Path(tmp); (p/'test.c').write_text(harness)
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
