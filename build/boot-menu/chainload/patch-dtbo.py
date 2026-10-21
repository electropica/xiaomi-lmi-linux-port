#!/usr/bin/env python3
"""Allow board-only Qualcomm overlays to inherit the selected platform SoC."""
def patch(text):
    old='\t\tqcom_parse_id(dtbo->address,&dtbo->info);\n\t\ttlog_verbose("voting dtbo %zu (%s)",dtbo->id,model);'
    assert text.count(old)==1
    return text.replace(old,'''\t\tqcom_parse_id(dtbo->address,&dtbo->info);
\t\t/* LMI_DTBO_BOARD_ONLY_V1: overlays may omit the SoC tuple already
\t\t * supplied by the base DTB. Keep board matching and never override
\t\t * an explicit (including malformed) msm-id property. */
\t\tint msm_len=0,board_len=0;
\t\tconst void*msm=fdt_getprop(dtbo->address,0,"qcom,msm-id",&msm_len);
\t\tconst void*board=fdt_getprop(dtbo->address,0,"qcom,board-id",&board_len);
\t\tif(!msm&&msm_len==-FDT_ERR_NOTFOUND&&board&&
\t\t   board_len>=(int)sizeof(qcom_board_id)&&board_len%(int)sizeof(qcom_board_id)==0){
\t\t\tdtbo->info.soc_id=chip_info->soc_id;
\t\t\tdtbo->info.soc_rev=chip_info->soc_rev;
\t\t\tdtbo->info.foundry_id=chip_info->foundry_id;
\t\t\ttlog_notice("board-only DTBO %zu inherits base platform SoC",dtbo->id);
\t\t}
\t\ttlog_verbose("voting dtbo %zu (%s)",dtbo->id,model);''')
