#!/usr/bin/env python3
"""Check the actual observer fragment with bounded DT/SRAM stubs, never hardware."""
from pathlib import Path
import hashlib
import re
import subprocess
import sys
import tempfile

SOURCE_SHA = '0f5676829cb2a40daa191a456998c700d744afe8346e07dd3c7af2a7e8685957'
RELATIVE = 'drivers/power/supply/qcom/qpnp-fg-gen4.c'

STUBS = r'''
#include <assert.h>
#include <errno.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
typedef unsigned char u8;
struct device_node { int refs, id; };
struct device { struct device_node *of_node; };
struct device_attribute { int unused; };
struct fg_dev { int profile_load_status, batt_id_ohms; };
struct fg_gen4_chip { struct fg_dev fg; struct { bool force_load_profile, multi_profile_load; } dt; };
static struct fg_gen4_chip chip;
static struct device_node container = {1,0}, unrelated = {1,1}, profile = {1,2};
static struct device dev;
static bool missing_chip, missing_link, missing_profile;
static int data_len, reads, fail_read;
static u8 marker_before, marker_after, reference[PROFILE_LEN], retained[PROFILE_LEN];
static void *dev_get_drvdata(struct device *d) { assert(d == &dev); return missing_chip ? NULL : &chip; }
static struct device_node *get(struct device_node *p) { if (p) p->refs++; return p; }
static void of_node_put(struct device_node *p) { if (p) { p->refs--; assert(p->refs >= 1); } }
static struct device_node *of_parse_phandle(struct device_node *p, const char *name, int index) {
    assert(p == dev.of_node && !strcmp(name,"qcom,battery-data") && !index);
    return missing_link ? NULL : get(&container);
}
static struct device_node *next_child(struct device_node *parent, struct device_node *previous) {
    assert(parent == &container);
    if (!previous) return get(&unrelated);
    of_node_put(previous);
    return previous == &unrelated && !missing_profile ? get(&profile) : NULL;
}
#define for_each_child_of_node(parent, child) for(child=next_child(parent,NULL); child; child=next_child(parent,child))
static int of_property_read_string(struct device_node *node, const char *name, const char **value) {
    assert(!strcmp(name,"qcom,battery-type"));
    *value = node == &profile ? "j11sun_4700mah" : "other";
    return 0;
}
static const void *of_get_property(struct device_node *node, const char *name, int *len) {
    assert(node == &profile && !strcmp(name,"qcom,fg-profile-data"));
    *len = data_len; return reference;
}
static int fg_sram_read(struct fg_dev *fg, int word, int offset, u8 *dst, int count, int mode) {
    assert(fg == &chip.fg && !offset && mode == FG_IMA_DEFAULT);
    reads++;
    if (reads == fail_read) return -EIO;
    if (word == PROFILE_INTEGRITY_WORD) {
        assert(count == 1); *dst = reads == 1 ? marker_before : marker_after;
    } else { assert(word == PROFILE_LOAD_WORD && count == PROFILE_LEN); memcpy(dst,retained,count); }
    return 0;
}
static int scnprintf(char *dst, size_t cap, const char *format, ...) {
    va_list args; va_start(args,format); int n=vsnprintf(dst,cap,format,args); va_end(args);
    assert(n >= 0 && (size_t)n < cap); return n;
}
static void reset(void) {
    assert(container.refs == 1 && unrelated.refs == 1 && profile.refs == 1);
    missing_chip=missing_link=missing_profile=false;
    data_len=PROFILE_LEN; reads=fail_read=0; marker_before=marker_after=9;
    chip.fg.profile_load_status=3; chip.fg.batt_id_ohms=99800;
    chip.dt.force_load_profile=true; chip.dt.multi_profile_load=false;
    for (int i=0;i<PROFILE_LEN;i++) reference[i]=retained[i]=(u8)i;
}
'''
LOAD_GUARD = '''#ifdef CONFIG_DEBUG_FS
\t/* Diagnostic variant: never clear/reload a mismatching gauge profile. */
\tpr_warn("lmi diagnostic: required profile reload blocked\\n");
\tgoto out;
#endif

'''
TESTS = r'''
int main(void) {
    char buf[PAGE_SIZE]; struct device_attribute attr={0}; struct fg_gen4_chip before;
    reset(); before=chip;
    assert(lmi_fg_profile_show(&dev,&attr,buf)>0 && reads==3);
    assert(strstr(buf,"prefix24_match=1 full416_match=1") && !memcmp(&before,&chip,sizeof(chip)));
    reset(); retained[100]^=1;
    assert(lmi_fg_profile_show(&dev,&attr,buf)>0 && strstr(buf,"prefix24_match=1 full416_match=0"));
    reset(); retained[0]^=1;
    assert(lmi_fg_profile_show(&dev,&attr,buf)>0 && strstr(buf,"prefix24_match=0 full416_match=0"));
    for(int i=1;i<=3;i++) { reset(); fail_read=i; assert(lmi_fg_profile_show(&dev,&attr,buf)==-EIO && reads==i); }
    reset(); marker_after=0; assert(lmi_fg_profile_show(&dev,&attr,buf)==-EAGAIN);
    reset(); missing_chip=true; assert(lmi_fg_profile_show(&dev,&attr,buf)==-ENODEV && reads==0);
    reset(); missing_link=true; assert(lmi_fg_profile_show(&dev,&attr,buf)==-ENODATA && reads==0);
    reset(); missing_profile=true; assert(lmi_fg_profile_show(&dev,&attr,buf)==-ENODATA && reads==0);
    reset(); data_len=PROFILE_LEN-1; assert(lmi_fg_profile_show(&dev,&attr,buf)==-ENODATA && reads==0);
    reset(); marker_before=marker_after=0;
    assert(lmi_fg_profile_show(&dev,&attr,buf)>0 && strstr(buf,"integrity=0x00"));
    reset(); assert(container.refs==1 && unrelated.refs==1 && profile.refs==1);
    puts("PASS: 12 observer cases; errors explicit, references balanced, chip state unchanged");
    return 0;
}
'''

def main():
    source = Path(sys.argv[1]).resolve()
    original = source.read_bytes()
    assert hashlib.sha256(original).hexdigest() == SOURCE_SHA
    repo = Path(__file__).resolve().parents[3]
    patch = repo / 'kernel/patches/diagnostics/lmi-fg-profile-observer-unvalidated.patch'
    with tempfile.TemporaryDirectory(prefix='lmi-fg-observer-test-') as tmp:
        work = Path(tmp)
        target = work / RELATIVE
        target.parent.mkdir(parents=True)
        target.write_bytes(original)
        subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=work,check=True,timeout=10)
        text = target.read_text()
        start = text.index('static ssize_t lmi_fg_profile_show')
        end = text.index('static struct device_attribute dev_attr_lmi_fg_profile',start)
        observer = text[start:end]
        calls = set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', observer))
        allowed = {'lmi_fg_profile_show','dev_get_drvdata','of_parse_phandle','for_each_child_of_node','of_property_read_string','strcmp','of_get_property','memcpy','of_node_put','fg_sram_read','memcmp','scnprintf','if'}
        assert calls <= allowed, calls-allowed
        assert '__ATTR(lmi_fg_profile, 0400, lmi_fg_profile_show, NULL)' in text
        # The existing driver outside the observer and registration stays intact.
        inserted = text[text.index('/* On-demand diagnostic:'):text.index('static struct attribute *fg_attrs[]')]
        removed = text.replace('\n'+inserted,'',1).replace('#ifdef CONFIG_DEBUG_FS\n\t&dev_attr_lmi_fg_profile.attr,\n#endif\n','',1)
        assert removed.count(LOAD_GUARD) == 1
        assert removed.replace(LOAD_GUARD, '', 1) == original.decode()
        begin = text.index('\tif (!is_profile_load_required(chip))')
        stop = text.index('\tif (!chip->dt.multi_profile_load) {', begin)
        guard_flow = text[begin:stop]
        guard_test = '''
static bool required_reload;
static bool is_profile_load_required(struct fg_gen4_chip *p) { assert(p == &chip); return required_reload; }
#define pr_warn(...) ((void)0)
static int check_guard(void) {
    struct fg_gen4_chip *chip_ptr = &chip;
    struct fg_gen4_chip *chip = chip_ptr;
''' + guard_flow + '''
    return -1;
done: return 0;
out: return 1;
}
static void test_guard(void) {
    required_reload=false; assert(check_guard()==0);
    required_reload=true; assert(check_guard()==1);
}
'''
        names = ('PROFILE_LEN','PROFILE_COMP_LEN','PROFILE_LOAD_WORD','PROFILE_LOAD_OFFSET','PROFILE_INTEGRITY_WORD','PROFILE_INTEGRITY_OFFSET')
        constants = ''.join(re.search(r'^#define '+name+r'\s+\d+.*$', original.decode(), re.M).group(0)+'\n' for name in names)
        cfile=work/'check.c'; binary=work/'check'
        cfile.write_text(constants+'#define PAGE_SIZE 4096\n#define FG_IMA_DEFAULT 0\n#define CONFIG_DEBUG_FS 1\n'+STUBS+observer+guard_test+TESTS.replace('reset(); before=chip;', 'test_guard(); reset(); before=chip;'))
        subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(cfile),'-o',str(binary)],check=True,timeout=20)
        subprocess.run([str(binary)],check=True,timeout=5)
    assert source.read_bytes()==original
    print('No kernel build, gauge-data write, device access or live activation')

if __name__=='__main__':
    main()
