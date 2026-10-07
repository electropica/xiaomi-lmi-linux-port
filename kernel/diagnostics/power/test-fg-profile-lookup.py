#!/usr/bin/env python3
"""Exercise the patched DT lookup with bounded host-only reference stubs."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

SOURCE_SHA = '0f5676829cb2a40daa191a456998c700d744afe8346e07dd3c7af2a7e8685957'
RELATIVE = 'drivers/power/supply/qcom/qpnp-fg-gen4.c'
OLD = '\tbatt_node = of_find_node_by_name(node, "qcom,battery-data");\n'
NEW = '''\t/* The lmi profile can precede the gauge in the global DT order. */
\tbatt_node = of_parse_phandle(node, "qcom,battery-data", 0);
\tif (!batt_node)
\t\tbatt_node = of_find_node_by_name(of_node_get(node),
\t\t\t\t\t       "qcom,battery-data");
'''

def main():
    source = Path(sys.argv[1]).resolve()
    original = source.read_bytes()
    assert hashlib.sha256(original).hexdigest() == SOURCE_SHA
    repo = Path(__file__).resolve().parents[3]
    patch = repo / 'kernel/patches/diagnostics/lmi-fg-profile-phandle-unvalidated.patch'
    with tempfile.TemporaryDirectory(prefix='lmi-fg-profile-check-') as tmp:
        work = Path(tmp)
        target = work / RELATIVE
        target.parent.mkdir(parents=True)
        target.write_bytes(original)
        subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)], cwd=work, check=True, timeout=10)
        modified = target.read_text()
        assert modified == original.decode().replace(OLD, NEW)
        start = modified.index('\t/* The lmi profile can precede')
        end = modified.index('\tif (!batt_node) {', start)
        actual_lookup = modified[start:end]
        c = r'''
#include <assert.h>
#include <stddef.h>
#include <string.h>
struct device_node { int refs; };
static struct device_node gauge = {1}, lmi = {1}, generic = {1};
static struct device_node *explicit_profile, *legacy_profile;
static int parses, searches;
static struct device_node *of_node_get(struct device_node *p) { if (p) p->refs++; return p; }
static void of_node_put(struct device_node *p) { if (p) { p->refs--; assert(p->refs >= 1); } }
static struct device_node *of_parse_phandle(struct device_node *p, const char *name, int index) {
    assert(p == &gauge && !strcmp(name, "qcom,battery-data") && index == 0);
    parses++; return of_node_get(explicit_profile);
}
static struct device_node *of_find_node_by_name(struct device_node *p, const char *name) {
    assert(p == &gauge && !strcmp(name, "qcom,battery-data"));
    searches++; of_node_put(p); return of_node_get(legacy_profile);
}
static struct device_node *lookup(struct device_node *node) {
    struct device_node *batt_node;
''' + actual_lookup + r'''
    return batt_node;
}
int main(void) {
    struct device_node *result;
    /* Explicit lmi link wins despite a later generic container. */
    explicit_profile = &lmi; legacy_profile = &generic;
    result = lookup(&gauge); assert(result == &lmi && searches == 0); of_node_put(result);
    /* Legacy boards without the property retain their search path. */
    explicit_profile = NULL;
    result = lookup(&gauge); assert(result == &generic && searches == 1); of_node_put(result);
    /* Missing link and missing legacy container remain unavailable. */
    legacy_profile = NULL;
    result = lookup(&gauge); assert(result == NULL && searches == 2);
    /* Repeated calls do not consume the device's borrowed node reference. */
    for (int i = 0; i < 100; i++) {
        explicit_profile = &lmi; result = lookup(&gauge); of_node_put(result);
        explicit_profile = NULL; legacy_profile = &generic;
        result = lookup(&gauge); of_node_put(result);
    }
    assert(parses == 203 && searches == 102);
    assert(gauge.refs == 1 && lmi.refs == 1 && generic.refs == 1);
    return 0;
}
'''
        cfile = work / 'check.c'
        cfile.write_text(c)
        binary = work / 'check'
        subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', str(cfile), '-o', str(binary)], check=True, timeout=20)
        subprocess.run([str(binary)], check=True, timeout=5)
    assert source.read_bytes() == original
    print('PASS: explicit link, legacy fallback, unavailable profile and 200 repeated reference-balanced lookups')
    print('Source unchanged; no kernel build or device access')

if __name__ == '__main__':
    main()
