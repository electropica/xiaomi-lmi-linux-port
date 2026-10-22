/* SPDX-License-Identifier: MIT */
#include <stdio.h>
#include "variant-args.h"
#define CHECK(c) do{if(!(c)){fprintf(stderr,"line %d\n",__LINE__);return 1;}}while(0)
int main(void){
 char args[4096]="before androidboot.hwc=CN androidboot.hwversion=3.9.0 androidboot.product.hardware.sku=pro middle androidboot.hwc=GLOBAL androidboot.hwversion=3.19.1 androidboot.product.hardware.sku=std androidboot.veritymode=enforcing after";
 CHECK(!lmi_variant_args(args,sizeof(args)));
 CHECK(!strcmp(args,"before middle androidboot.hwc=GLOBAL androidboot.hwversion=3.19.1 androidboot.product.hardware.sku=std androidboot.veritymode=enforcing after"));
 char copy[4096];strcpy(copy,args);CHECK(!lmi_variant_args(args,sizeof(args))&&!strcmp(args,copy));
 strcpy(args,"androidboot.hwc=OTHER androidboot.hwc=GLOBAL");strcpy(copy,args);
 CHECK(lmi_variant_args(args,sizeof(args))==-1&&!strcmp(args,copy));
 strcpy(args,"androidboot.hwc=CN androidboot.hwc=GLOBAL androidboot.hwc=EU");strcpy(copy,args);
 CHECK(lmi_variant_args(args,sizeof(args))==-1&&!strcmp(args,copy));
 strcpy(args,"androidboot.hwc=CN androidboot.hwc=");strcpy(copy,args);
 CHECK(lmi_variant_args(args,sizeof(args))==-1&&!strcmp(args,copy));
 memset(args,'x',sizeof(args));CHECK(lmi_variant_args(args,sizeof(args))==-1);
 puts("VARIANT_ARGS_TARGETED_DEDUP_AND_REFUSAL_PASS");return 0;
}
