/* SPDX-License-Identifier: MIT
 * Shared by early PEI reservation, the loader and host tests.
 * Input FDT cells are big endian and may contain one or two cells.
 */
#ifndef LMI_OUTER_RANGE_H
#define LMI_OUTER_RANGE_H
#include <stdint.h>
#include <stddef.h>
struct lmi_outer_range { uint64_t start, end, page_start, page_end; };
static int lmi_outer_cell(const void *data, int length, uint64_t *out) {
    const unsigned char *p=data;
    uint64_t v=0; int i;
    if(!p||!out||(length!=4&&length!=8))return -1;
    for(i=0;i<length;i++)v=(v<<8)|p[i];
    *out=v;return 0;
}
static int lmi_outer_decode(const void *start,int ns,const void *end,int ne,
                            struct lmi_outer_range *r) {
    uint64_t a,b;
    if(!r||lmi_outer_cell(start,ns,&a)||lmi_outer_cell(end,ne,&b))return -1;
    if(a<0x80000000ULL||b<=a||b-a>64ULL*1024*1024||b>UINT64_MAX-4095)return -1;
    r->start=a;r->end=b;r->page_start=a&~4095ULL;r->page_end=(b+4095)&~4095ULL;
    return 0;
}
static int lmi_outer_within(const struct lmi_outer_range *r,uint64_t base,uint64_t size) {
    return r&&size&&base<=UINT64_MAX-size&&r->page_start>=base&&r->page_end<=base+size;
}
static int lmi_outer_overlap(const struct lmi_outer_range *r,uint64_t base,uint64_t size) {
    if(!r||!size||base>UINT64_MAX-size)return 1;
    return r->page_start<base+size&&base<r->page_end;
}
#endif
