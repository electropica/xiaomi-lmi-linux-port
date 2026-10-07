/* SPDX-License-Identifier: MIT */
#ifndef LMI_FRAME_PACING_H
#define LMI_FRAME_PACING_H
#include <math.h>
#include <stdint.h>

/* Fixed-size histogram: [0,5), [5,10), ... [495,500), >=500 ms.
 * Quantiles are upper bounds, not exact percentiles. -1 means overflow.
 * These are publication intervals, not sensor-to-panel latency.
 */
struct lmi_frame_pacing {
    uint64_t count, invalid, over_60_ms, over_80_ms, bins[101];
    double previous, sum_ms, min_ms, max_ms;
    int started;
};
static inline void lmi_frame_pacing_add(struct lmi_frame_pacing *p, double now) {
    if (!isfinite(now)) { p->invalid++; return; }
    if (!p->started) { p->started=1; p->previous=now; return; }
    double gap=(now-p->previous)*1000.0;
    p->previous=now;
    if (!(gap>0.0) || !isfinite(gap)) { p->invalid++; return; }
    if (!p->count || gap<p->min_ms) p->min_ms=gap;
    if (gap>p->max_ms) p->max_ms=gap;
    p->count++; p->sum_ms+=gap;
    if (gap>60.0) p->over_60_ms++;
    if (gap>80.0) p->over_80_ms++;
    unsigned bin=gap>=500.0 ? 100 : (unsigned)(gap/5.0);
    p->bins[bin]++;
}
static inline int lmi_frame_pacing_upper_ms(const struct lmi_frame_pacing *p,
                                           unsigned percentile) {
    if (!p->count || !percentile || percentile>100) return -1;
    uint64_t rank=(p->count*percentile+99)/100, cumulative=0;
    for (unsigned bin=0;bin<101;bin++) {
        cumulative+=p->bins[bin];
        if (cumulative>=rank) return bin==100 ? -1 : (int)(bin+1)*5;
    }
    return -1;
}
#endif
