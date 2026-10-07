#!/usr/bin/env python3
"""Compile actual locked gauge functions with simulated reads; no device access."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile

SOURCE_SHA = 'c969590d0f30c2746a725497969eb49cad9a951e2426b1753b670c2bf7f94837'
NAMES = ('fg_get_battery_current', 'fg_get_battery_voltage')


def functions(text):
    result = []
    for name in NAMES:
        start = text.index('int ' + name + '(')
        end = text.index('\n}', start) + 2
        result.append(text[start:end])
    return '\n'.join(result)


STUBS = r"""
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint64_t u64;
typedef int64_t s64;
struct fg_dev { int wa_flags; };
#define MAX_READ_TRIES 5
#define BATT_CURRENT_NUMR 488281
#define BATT_CURRENT_DENR 1000
#define BATT_VOLTAGE_NUMR 122070
#define BATT_VOLTAGE_DENR 1000
#define PMI8998_V1_REV_WA 1
#define BATT_INFO_IBATT_LSB(fg) 0
#define BATT_INFO_IBATT_LSB_CP(fg) 1
#define BATT_INFO_VBATT_LSB(fg) 2
#define BATT_INFO_VBATT_LSB_CP(fg) 3
#define pr_err(...) ((void)0)
#define pr_debug(...) ((void)0)
static int calls, match_at, error_at;
static int fg_read(struct fg_dev *fg, int reg, u8 *buf, int bytes) {
    (void)fg; (void)reg; assert(bytes==2);
    calls++;
    if(calls==error_at) return -EIO;
    buf[0]=0; buf[1]=128;
    if(calls%2==0 && calls/2!=match_at) buf[0]=1;
    return 0;
}
static int32_t sign_extend32(uint32_t value, int bit) {
    return (int32_t)(value<<(31-bit))>>(31-bit);
}
static int64_t div_s64(int64_t a, int64_t b) { return a/b; }
static uint64_t div_u64(uint64_t a, uint64_t b) { return a/b; }
"""
HARNESS = r"""
int main(void) {
    int (*readers[])(struct fg_dev *,int *)={fg_get_battery_current,fg_get_battery_voltage};
    struct fg_dev fg={0};
    unsigned cases=0;
    for(unsigned reader=0;reader<2;reader++) {
        for(int match=1;match<=5;match++) {
            calls=0; match_at=match; error_at=0; int value=12345;
            int rc=readers[reader](&fg,&value);
            assert(rc==((!EXPECT_FIXED && match==5)?-EINVAL:0));
            assert(calls==match*2);
            if(rc==0) assert(value==(reader==0?-15999991:3999989));
            cases++;
        }
        calls=0; match_at=0; error_at=0; int value=12345;
        assert(readers[reader](&fg,&value)==(EXPECT_FIXED?-EINVAL:0));
        assert(calls==10);
        if(EXPECT_FIXED) assert(value==12345);
        cases++;
        const int errors[]={1,2,9,10};
        for(unsigned i=0;i<4;i++) {
            calls=0; match_at=0; error_at=errors[i]; value=12345;
            assert(readers[reader](&fg,&value)==-EIO);
            assert(value==12345 && calls==errors[i]);
            cases++;
        }
    }
    printf("%s: %u actual-function simulated-read cases\n",EXPECT_FIXED?"PATCHED_PASS":"ORIGINAL_BUG_REPRODUCED",cases);
    return 0;
}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='locked external drivers/power/supply/qcom/fg-util.c')
    args = parser.parse_args()
    data = args.source.read_bytes()
    assert hashlib.sha256(data).hexdigest() == SOURCE_SHA, 'Source identity mismatch'
    original = data.decode()
    patch = Path(__file__).resolve().parents[2] / 'patches/diagnostics/lmi-fg-shadow-retry-unvalidated.patch'
    with tempfile.TemporaryDirectory(prefix='lmi-fg-retry-test-') as tmp:
        base = Path(tmp)
        target = base / 'drivers/power/supply/qcom/fg-util.c'
        target.parent.mkdir(parents=True)
        target.write_bytes(data)
        subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(base),'-i',str(patch)], check=True, timeout=10)
        changed = target.read_text()
        expected = original
        for name in NAMES:
            start = expected.index('int ' + name + '(')
            end = expected.index('\n}',start)+2
            function = expected[start:end]
            assert function.count('while (tries++ < MAX_READ_TRIES)') == 1
            function = function.replace('while (tries++ < MAX_READ_TRIES)', 'for (tries = 0; tries < MAX_READ_TRIES; tries++)', 1)
            expected = expected[:start]+function+expected[end:]
        assert changed==expected, 'Patch changes more than the two reviewed loops'
        for fixed, text in ((0,original),(1,changed)):
            cfile = base / ('fixture-' + str(fixed) + '.c')
            exe = cfile.with_suffix('')
            cfile.write_text(STUBS + functions(text) + HARNESS)
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-DEXPECT_FIXED='+str(fixed),str(cfile),'-o',str(exe)], check=True, timeout=15)
            subprocess.run([str(exe)], check=True, timeout=5)
    assert args.source.read_bytes()==data, 'External source must remain unchanged'
    print('No kernel build, live reads, calibration or deployment')


if __name__=='__main__':
    main()
