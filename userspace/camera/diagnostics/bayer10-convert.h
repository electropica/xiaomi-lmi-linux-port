/* SPDX-License-Identifier: MIT
 *
 * Bayer RAW10 (MIPI packed) to BGRx conversion for the lmi rear camera.
 *
 * The CAMSS VFE of this board has no process block: from a Bayer sensor it
 * only delivers the Bayer bytes themselves. The layout is the one the V4L2
 * specification describes for the packed 10 bit formats: four pixels share
 * five bytes, the first four carry the eight most significant bits of the
 * pixels and the fifth carries their two least significant bits, the first
 * pixel in the two least significant bits of that byte.
 *
 * Every line is padded to the stride the driver negotiated, so the packed
 * bytes of a line are stride wide and not width * 10 / 8 wide.
 *
 * The file has no dependency, so the conversion can be exercised on a host
 * against a captured frame before it is used on the phone.
 */
#ifndef LMI_BAYER10_CONVERT_H
#define LMI_BAYER10_CONVERT_H

#include <stddef.h>
#include <stdint.h>

/* The Bayer phase of the mosaic. MEDIA_BUS_FMT_SGRBG10_1X10 is GRBG: the
 * 2x2 cell holds G R on the first line and B G on the second one. */
enum lmi_bayer_phase {
	LMI_BAYER_GRBG = 0,
	LMI_BAYER_GBRG,
	LMI_BAYER_BGGR,
	LMI_BAYER_RGBG,
};

/* The tone mapping of the conversion. The black level and the span are
 * measured on the frame itself, so a dim scene is stretched instead of
 * crushed. The gains carry the white balance. */
struct lmi_bayer_tuning {
	uint16_t black[3];	/* black level per channel, in 10 bit codes */
	uint16_t span[3];	/* usable range per channel, in 10 bit codes */
	float gain[3];		/* white balance, applied after the span */
	float gamma;		/* 2.2 by default */
};

/* Fill the tuning with a usable default. */
void lmi_bayer_default_tuning(struct lmi_bayer_tuning *tuning);

/* Measure the frame: black level, span and a grey world white balance.
 * Returns 0 on success, a negative value when the frame is unusable. */
int lmi_bayer_analyse(const uint8_t *raw, size_t raw_size,
		      uint32_t width, uint32_t height, uint32_t stride,
		      enum lmi_bayer_phase phase,
		      struct lmi_bayer_tuning *tuning);

/* Convert one frame into BGRx. The output stride is width * 4 bytes.
 * Returns 0 on success, a negative value when the arguments do not match
 * the frame geometry. */
int lmi_bayer_convert(const uint8_t *raw, size_t raw_size,
		      uint32_t width, uint32_t height, uint32_t stride,
		      enum lmi_bayer_phase phase,
		      const struct lmi_bayer_tuning *tuning,
		      uint8_t *bgrx, uint32_t bgrx_stride);

/* The Bayer phase that matches a media bus code, -1 when unknown. */
int lmi_bayer_phase_from_mbus(uint32_t mbus_code);

/* The channel of a position: 0 for red, 1 for green, 2 for blue. */
int lmi_bayer_channel(enum lmi_bayer_phase phase, uint32_t x, uint32_t y);

#endif /* LMI_BAYER10_CONVERT_H */
