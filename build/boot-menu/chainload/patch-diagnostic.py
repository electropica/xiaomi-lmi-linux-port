#!/usr/bin/env python3
"""Diagnostic-only additions to already qualified SimpleInit handoff sources."""
def patch_entry(text):
    text=text.replace('int run_boot_linux(boot_config*boot){','extern void lmi_boot_stage(const char*stage);\nextern void lmi_boot_failed(void);\nextern int linux_boot_lmi_android_fstab(linux_boot*lb);\n\nint run_boot_linux(boot_config*boot){')
    for needle,label in [('if(!(cfg=linux_config_new_from_confd(boot->key)))','01 configuration'),('if(!(lb=linux_boot_new(cfg)))','02 boot object'),('if(linux_boot_lmi_bundle(lb,boot->ident)!=0)','03 verified RAM bundle'),('if(linux_boot_execute(lb)!=0)','15 execute / ARM handoff validation')]:
        assert text.count('\t'+needle)==1
        text=text.replace('\t'+needle,'\tlmi_boot_stage("'+label+'");\n\t'+needle)
    assert text.count('\tdone:\n')==1
    text=text.replace('\tlmi_boot_stage("15 execute / ARM handoff validation");','\tlmi_boot_stage("14 Android logical ramdisk fstab");\n\tif(linux_boot_lmi_android_fstab(lb)!=0)\n\t\tEDONE(tlog_error("prepare Android logical ramdisk fstab failed"));\n\tlmi_boot_stage("15 execute / ARM handoff validation");')
    text=text.replace('extern int linux_boot_lmi_android_fstab(linux_boot*lb);','extern int linux_boot_lmi_android_fstab(linux_boot*lb);\nextern int linux_boot_lmi_variant(linux_boot*lb);')
    text=text.replace('extern void lmi_boot_failed(void);','extern void lmi_boot_failed(void);\nextern void lmi_boot_target(const char*target);\nextern void lmi_boot_ready(void);')
    text=text.replace('\tlmi_boot_stage("01 configuration");','\tlmi_boot_target(boot->ident);\n\tlmi_boot_stage("01 configuration");')
    text=text.replace('\tif(linux_boot_execute(lb)!=0)','\tlmi_boot_ready();\n\tif(linux_boot_execute(lb)!=0)')
    text=text.replace('\tlmi_boot_stage("15 execute / ARM handoff validation");','\tif(linux_boot_lmi_variant(lb)!=0)\n\t\tEDONE(tlog_error("variant boot arguments remain ambiguous"));\n\tlmi_boot_stage("15 execute / ARM handoff validation");')
    return text.replace('\tdone:\n','\tdone:\n\tlmi_boot_failed();\n')

def patch_prepare(text):
    assert text.count('int linux_boot_prepare(linux_boot*lb){')==1
    text=text.replace('int linux_boot_prepare(linux_boot*lb){','extern void lmi_boot_stage(const char*stage);\n\nint linux_boot_prepare(linux_boot*lb){')
    text=text.replace('extern void lmi_boot_stage(const char*stage);','extern void lmi_boot_stage(const char*stage);\nextern int linux_boot_lmi_kernel_extent(linux_boot*lb);')
    needle='\tif(linux_boot_select_fdt(lb)!=0)'
    assert text.count(needle)==1
    text=text.replace(needle,'\tif(linux_boot_lmi_kernel_extent(lb)!=0)\n\t\treturn trlog_error(-1,"reserve complete ARM64 Image extent failed");\n'+needle)
    stages=[('linux_load_from_config(lb)','04 load components'),('linux_boot_install_random_seed()','05 random seed'),('linux_boot_uncompress_kernel(lb)','06 decompress kernel'),('linux_boot_select_fdt(lb)','07 select DTB'),('linux_boot_apply_dtbo(lb)','08 apply DTBO'),('linux_boot_generate_fdt(lb)','09 generate FDT'),('linux_boot_move(lb)','10 move components'),('linux_boot_install_initrd(lb)','11 install initrd'),('linux_boot_update_fdt(lb)','12 update FDT'),('check_boot(lb)','13 final checks')]
    for call,label in stages:
        needle='\tif('+call+'!=0)';assert text.count(needle)==1
        text=text.replace(needle,'\tlmi_boot_stage("'+label+'");\n'+needle)
    return text
