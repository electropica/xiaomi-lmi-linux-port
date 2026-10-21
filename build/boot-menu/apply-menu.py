#!/usr/bin/env python3
"""Apply the temporary menu probe to the exact pinned SimpleInit revision."""
import argparse, hashlib, json
from pathlib import Path

MARKER = 'LMI_TEMPORARY_MENU_SMOKE_V1'

def patch_main(text):
    if MARKER in text:
        return text
    assert text.count('\tconfd_init();') == 1
    assert text.count('\tboot_init_configs();') == 1
    # Avoid loading config from logfs/ESP, scanning installed operating systems,
    # or importing an old boot.current that would override the requested default.
    setup = '''\t/* LMI_TEMPORARY_MENU_SMOKE_V1: no disk config or OS probing. */
\tconfd_set_string("boot.title", "lmi boot menu - temporary test");
\tconfd_set_string("boot.default", "mobian");
\tconfd_set_string("boot.current", "mobian");
\tconfd_set_integer("boot.timeout", 15);
\tconfd_set_boolean("boot.uefi_probe", false);
\tconfd_set_boolean("boot.uefi_bootmenu", false);
\tconfd_set_integer("boot.configs.mobian.mode", BOOT_REBOOT);
\tconfd_set_string("boot.configs.mobian.desc", "Mobian (restart installed OS)");
\tconfd_set_boolean("boot.configs.mobian.show", true);
\tconfd_set_boolean("boot.configs.mobian.enabled", true);
\tconfd_set_integer("boot.configs.fastboot.mode", BOOT_REBOOT);
\tconfd_set_string("boot.configs.fastboot.desc", "Fastboot");
\tconfd_set_string("boot.configs.fastboot.extra.arg", "bootloader");
\tconfd_set_boolean("boot.configs.fastboot.show", true);
\tconfd_set_boolean("boot.configs.fastboot.enabled", true);
\tconfd_set_integer("boot.configs.recovery.mode", BOOT_REBOOT);
\tconfd_set_string("boot.configs.recovery.desc", "Lineage recovery");
\tconfd_set_string("boot.configs.recovery.extra.arg", "recovery");
\tconfd_set_boolean("boot.configs.recovery.show", true);
\tconfd_set_boolean("boot.configs.recovery.enabled", true);'''
    return text.replace('\tconfd_init();', setup).replace(
        '\tboot_init_configs();', '\t/* Built-in entries and OS probing deliberately skipped. */')

def patch_save(text):
    if MARKER in text:
        return text
    old = '''int confd_save_file(const char*file){
\tconst char*fn=file?file:def_path;
\treturn conf_save_file(def_fp,fn);
}'''
    assert text.count(old) == 1
    return text.replace(old, '''int confd_save_file(const char*file){
\t/* LMI_TEMPORARY_MENU_SMOKE_V1: never persist probe settings. */
\t(void)file;
\treturn 0;
}''')

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
    base=a.source/'GPLDrivers/Library/SimpleInit'
    lock=json.loads(Path(__file__).with_name('sources.lock.json').read_text())
    manifest={}
    for path,patcher in [('src/main/uefimain.c',patch_main),('src/confd/uefi.c',patch_save)]:
        f=base/path;old=f.read_text();new=patcher(old)
        before=hashlib.sha256(old.encode()).hexdigest()
        expected=lock['patched_source_hashes'][path]
        assert before in (expected['before'],expected['after']), 'Unexpected source content: '+path
        assert hashlib.sha256(new.encode()).hexdigest()==expected['after']
        f.write_text(new)
        manifest[path]=hashlib.sha256(new.encode()).hexdigest()
    print(json.dumps({'phase':'temporary-menu-smoke','patched_sources':manifest},indent=2))
if __name__=='__main__':main()
