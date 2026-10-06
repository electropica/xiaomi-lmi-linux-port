/* Diagnostic BT.601 limited-range row conversion, identical integer rounding.
 * Requires w % 8 == 0 and validated plane/output spans from the caller. */
#include <arm_neon.h>
#include <stdint.h>
static uint8x8_t lmi_clip_rgb(int32x4_t lo,int32x4_t hi) {
    lo=vshrq_n_s32(vaddq_s32(lo,vdupq_n_s32(128)),8);
    hi=vshrq_n_s32(vaddq_s32(hi,vdupq_n_s32(128)),8);
    return vqmovn_u16(vcombine_u16(vqmovun_s32(lo),vqmovun_s32(hi)));
}
static void lmi_yuv_row_neon(const uint8_t *y,const uint8_t *cb,
                            const uint8_t *cr,unsigned step,unsigned w,uint8_t *out) {
    for(unsigned x=0;x<w;x+=8) {
        int16_t ua[8],va[8];
        for(unsigned j=0;j<8;j+=2) {
            int16_t u=(int16_t)cb[((x+j)/2)*step]-128;
            int16_t v=(int16_t)cr[((x+j)/2)*step]-128;
            ua[j]=ua[j+1]=u;va[j]=va[j+1]=v;
        }
        int16x8_t l=vsubq_s16(vreinterpretq_s16_u16(vmovl_u8(vld1_u8(y+x))),vdupq_n_s16(16));
        int16x8_t u=vld1q_s16(ua),v=vld1q_s16(va);
        int16x4_t ll=vget_low_s16(l),lh=vget_high_s16(l);
        int32x4_t base_lo=vmull_n_s16(ll,298),base_hi=vmull_n_s16(lh,298);
        uint8x8x3_t rgb;
        rgb.val[0]=lmi_clip_rgb(vmlal_n_s16(base_lo,vget_low_s16(v),409),vmlal_n_s16(base_hi,vget_high_s16(v),409));
        rgb.val[1]=lmi_clip_rgb(vmlal_n_s16(vmlal_n_s16(base_lo,vget_low_s16(u),-100),vget_low_s16(v),-208),
                              vmlal_n_s16(vmlal_n_s16(base_hi,vget_high_s16(u),-100),vget_high_s16(v),-208));
        rgb.val[2]=lmi_clip_rgb(vmlal_n_s16(base_lo,vget_low_s16(u),516),vmlal_n_s16(base_hi,vget_high_s16(u),516));
        vst3_u8(out+3*x,rgb);
    }
}
