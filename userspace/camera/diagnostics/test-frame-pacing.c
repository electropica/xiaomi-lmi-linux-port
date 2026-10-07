/* SPDX-License-Identifier: MIT
 * Host-only deterministic timing tests; no PipeWire, camera or microphone.
 */
#include <assert.h>
#include <stdio.h>
#include "frame-pacing.h"
int main(void) {
    struct lmi_frame_pacing steady={0}, uneven={0}, limits={0};
    for(unsigned n=0;n<5;n++) lmi_frame_pacing_add(&steady,n*0.04);
    const double times[]={0,0.01,0.08,0.09,0.16};
    for(unsigned n=0;n<5;n++) lmi_frame_pacing_add(&uneven,times[n]);
    assert(steady.count==4 && uneven.count==4);
    assert(fabs(steady.sum_ms/4-40)<1e-8 && fabs(uneven.sum_ms/4-40)<1e-8);
    assert(steady.max_ms<41 && uneven.max_ms>69);
    assert(steady.over_60_ms==0 && uneven.over_60_ms==2);
    assert(lmi_frame_pacing_upper_ms(&steady,95)<=45);
    assert(lmi_frame_pacing_upper_ms(&uneven,95)>=70);
    assert(lmi_frame_pacing_upper_ms(&limits,50)==-1);
    lmi_frame_pacing_add(&limits,0);
    lmi_frame_pacing_add(&limits,0.75);
    assert(limits.count==1 && limits.bins[100]==1 && limits.over_80_ms==1);
    assert(lmi_frame_pacing_upper_ms(&limits,99)==-1);
    lmi_frame_pacing_add(&limits,NAN);
    lmi_frame_pacing_add(&limits,0.75);
    lmi_frame_pacing_add(&limits,0.50);
    assert(limits.invalid==3 && limits.count==1);
    assert(lmi_frame_pacing_upper_ms(&steady,0)==-1);
    assert(lmi_frame_pacing_upper_ms(&steady,101)==-1);
    puts("PASS: equal mean/different pacing, quantile bounds, overflow and invalid clocks");
    return 0;
}
