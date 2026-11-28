#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys,zlib,shutil,os
source=Path(os.environ.get('LMI_BUNDLE_DIRECTORY','/linux7-bundle'));out=Path(sys.argv[3]);data=(source/'lmi-outer-linux7.bin').read_bytes()
assert hashlib.sha256(data).hexdigest()==os.environ['LMI_EXPECTED_BUNDLE_SHA256']
assert len(data)<64*1024*1024
record=json.loads((source/'BUNDLE_RESULT.json').read_text())
assert record['sha256']==hashlib.sha256(data).hexdigest()
shutil.copyfile(source/'lmi-outer-linux7.bin',out/'lmi-outer-mobian.bin')
(out/'lmi-outer-mobian.json').write_text(json.dumps(record,indent=2)+'\n')
(out/'outer-ident.h').write_text(
    '/* Candidate only. */\n'
    '#define LMI_OUTER_KERNEL_SHA "%s"\n'
    '#define LMI_OUTER_DTB_SHA "%s"\n'
    '#define LMI_OUTER_INITRD_SHA "%s"\n'
    '#define LMI_OUTER_BOOTARGS " qcom_pm8150b_charger.lmi_icl_hc_enable=1"\n'
    % (
        record['components']['linux7/kernel']['decoded_sha256'],
        record['components']['linux7/dtb']['decoded_sha256'],
        record['components']['linux7/initrd']['decoded_sha256'],
    ))
(out/'outer-lock.h').write_text('/* Candidate only. */\n#define LMI_OUTER_BYTES '+str(len(data))+'u\n#define LMI_OUTER_CRC32 0x%08Xu\n'%zlib.crc32(data))
