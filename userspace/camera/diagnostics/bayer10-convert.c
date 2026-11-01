/* SPDX-License-Identifier: MIT
 *
 * Implementation of the Bayer RAW10 to BGRx conversion.
 */
#include "bayer10-convert.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

#define LMI_RAW10_MAX 1023

/* The pattern of the mosaic: pattern[y % 2][x % 2] gives the channel.
 * The index of a channel is 0 for red, 1 for green and 2 for blue. */
static const uint8_t lmi_bayer_pattern[4][2][2] = {
	{ { 1, 0 }, { 2, 1 } },	/* GRBG */
	{ { 1, 2 }, { 0, 1 } },	/* GBRG */
	{ { 2, 1 }, { 1, 0 } },	/* BGGR */
	{ { 0, 1 }, { 1, 2 } },	/* RGBG */
};

/* The media bus codes of the Bayer 10 bit formats. */
#define LMI_BUS_FMT_SGRBG10_1X10	0x300a
#define LMI_BUS_FMT_SGBRG10_1X10	0x300b
#define LMI_BUS_FMT_SBGGR10_1X10	0x300c
#define LMI_BUS_FMT_SRGBG10_1X10	0x300d

int lmi_bayer_phase_from_mbus(uint32_t mbus_code)
{
	switch (mbus_code) {
	case LMI_BUS_FMT_SGRBG10_1X10:
		return LMI_BAYER_GRBG;
	case LMI_BUS_FMT_SGBRG10_1X10:
		return LMI_BAYER_GBRG;
	case LMI_BUS_FMT_SBGGR10_1X10:
		return LMI_BAYER_BGGR;
	case LMI_BUS_FMT_SRGBG10_1X10:
		return LMI_BAYER_RGBG;
	default:
		return -1;
	}
}

int lmi_bayer_channel(enum lmi_bayer_phase phase, uint32_t x, uint32_t y)
{
	if (phase < 0 || phase > LMI_BAYER_RGBG)
		return -1;
	return lmi_bayer_pattern[phase][y & 1][x & 1];
}

void lmi_bayer_default_tuning(struct lmi_bayer_tuning *tuning)
{
	if (!tuning)
		return;
	memset(tuning, 0, sizeof(*tuning));
	for (int c = 0; c < 3; c++) {
		tuning->black[c] = 0;
		tuning->span[c] = LMI_RAW10_MAX;
		tuning->gain[c] = 1.0f;
	}
	tuning->gamma = 2.2f;
}

/* Unpack one line of the frame into 10 bit values. */
static void lmi_unpack_line(const uint8_t *raw, uint32_t y, uint32_t stride,
			    uint32_t width, uint16_t *line)
{
	const uint8_t *row = raw + (size_t)y * stride;
	uint32_t groups = width / 4;
	for (uint32_t g = 0; g < groups; g++) {
		const uint8_t *group = row + g * 5;
		uint8_t low = group[4];
		line[g * 4 + 0] = (uint16_t)((group[0] << 2) | ((low >> 0) & 3));
		line[g * 4 + 1] = (uint16_t)((group[1] << 2) | ((low >> 2) & 3));
		line[g * 4 + 2] = (uint16_t)((group[2] << 2) | ((low >> 4) & 3));
		line[g * 4 + 3] = (uint16_t)((group[3] << 2) | ((low >> 6) & 3));
	}
}

/* The tone curve of one channel, as a table: the conversion runs on every
 * pixel of every frame, so the curve is computed once per frame. */
static void lmi_build_lut(const struct lmi_bayer_tuning *tuning,
			  uint8_t lut[3][LMI_RAW10_MAX + 1])
{
	for (int c = 0; c < 3; c++) {
		float gamma = tuning->gamma > 0.0f ? tuning->gamma : 1.0f;
		for (int v = 0; v <= LMI_RAW10_MAX; v++) {
			float linear = (float)v - (float)tuning->black[c];
			if (linear < 0.0f)
				linear = 0.0f;
			linear *= tuning->gain[c];
			if (tuning->span[c] > 0)
				linear *= 255.0f / (float)tuning->span[c];
			if (linear > 255.0f)
				linear = 255.0f;
			float corrected = powf(linear / 255.0f, 1.0f / gamma);
			int out = (int)(corrected * 255.0f + 0.5f);
			if (out < 0)
				out = 0;
			if (out > 255)
				out = 255;
			lut[c][v] = (uint8_t)out;
		}
	}
}

/* Bilinear interpolation of one channel at a position that does not hold it.
 *
 * In a 2x2 mosaic the same colour is never at distance one in every
 * direction: at a red pixel the blue neighbours are the four diagonals, at
 * a blue pixel the red neighbours are the four diagonals too, and at a
 * green pixel they are the two neighbours of the same row or column. The
 * interpolation therefore takes every neighbour of the 3x3 box that holds
 * the wanted colour, which is the usual bilinear demosaic of a Bayer
 * frame. */
static float lmi_interpolate(const uint16_t *up, const uint16_t *middle,
			     const uint16_t *down, uint32_t x, uint32_t y,
			     uint32_t width, uint32_t height,
			     enum lmi_bayer_phase phase, int target)
{
	static const int offsets[8][2] = {
		{ -1, -1 }, { 0, -1 }, { 1, -1 },
		{ -1, 0 }, { 1, 0 },
		{ -1, 1 }, { 0, 1 }, { 1, 1 },
	};
	float total = 0.0f;
	int count = 0;
	for (int i = 0; i < 8; i++) {
		int nx = (int)x + offsets[i][0];
		int ny = (int)y + offsets[i][1];
		if (nx < 0 || ny < 0 || (uint32_t)nx >= width || (uint32_t)ny >= height)
			continue;
		if (lmi_bayer_pattern[phase][ny & 1][nx & 1] != target)
			continue;
		const uint16_t *row = (offsets[i][1] < 0) ? up
			: ((offsets[i][1] > 0) ? down : middle);
		total += (float)row[nx];
		count++;
	}
	return count > 0 ? total / (float)count : 0.0f;
}

int lmi_bayer_analyse(const uint8_t *raw, size_t raw_size,
		      uint32_t width, uint32_t height, uint32_t stride,
		      enum lmi_bayer_phase phase,
		      struct lmi_bayer_tuning *tuning)
{
	if (!raw || !tuning || width < 4 || height < 2 || width % 4)
		return -1;
	uint32_t packed = width / 4 * 5;
	if (stride < packed || raw_size < (size_t)stride * height)
		return -1;
	if (phase < 0 || phase > LMI_BAYER_RGBG)
		return -1;

	uint32_t histograms[3][LMI_RAW10_MAX + 1];
	memset(histograms, 0, sizeof(histograms));

	uint16_t *line = malloc(width * sizeof(uint16_t));
	if (!line)
		return -1;

	uint64_t counts[3] = { 0, 0, 0 };
	uint64_t sums[3] = { 0, 0, 0 };

	/* Every pixel of every line is visited: the mosaic alternates on both
	 * axes, so sampling only half of the columns or half of the lines
	 * would leave one of the three channels without any sample. */
	for (uint32_t y = 0; y < height; y++) {
		lmi_unpack_line(raw, y, stride, width, line);
		for (uint32_t x = 0; x < width; x++) {
			int channel = lmi_bayer_pattern[phase][y & 1][x & 1];
			histograms[channel][line[x]]++;
			counts[channel]++;
			sums[channel] += (uint64_t)line[x];
		}
	}
	free(line);

	for (int c = 0; c < 3; c++) {
		if (!counts[c])
			return -1;
		/* The black level is the second percentile. */
		uint64_t target = counts[c] / 50;
		uint64_t seen = 0;
		uint32_t black = 0;
		for (uint32_t v = 0; v <= LMI_RAW10_MAX; v++) {
			seen += histograms[c][v];
			if (seen >= target) {
				black = v;
				break;
			}
		}
		/* The white point is the 99.9th percentile: a dim scene only
		 * reaches a small part of the scale, and the noise must not
		 * set the span. */
		target = counts[c] * 999 / 1000;
		seen = 0;
		uint32_t white = black;
		for (uint32_t v = 0; v <= LMI_RAW10_MAX; v++) {
			seen += histograms[c][v];
			if (seen >= target) {
				white = v;
				break;
			}
		}
		uint32_t span = white > black ? white - black : 1;
		tuning->black[c] = (uint16_t)black;
		tuning->span[c] = (uint16_t)(span > LMI_RAW10_MAX ? LMI_RAW10_MAX : span);
	}

	/* Grey world white balance on the measured means, limited so that a
	 * single strong colour cannot take over the picture. */
	float means[3];
	for (int c = 0; c < 3; c++)
		means[c] = (float)sums[c] / (float)counts[c];
	float reference = (means[0] + means[1] + means[2]) / 3.0f;
	if (reference < 1.0f)
		reference = 1.0f;
	for (int c = 0; c < 3; c++) {
		float gain = reference / (means[c] > 1.0f ? means[c] : 1.0f);
		if (gain < 0.6f)
			gain = 0.6f;
		if (gain > 1.6f)
			gain = 1.6f;
		tuning->gain[c] = gain;
	}
	tuning->gamma = 2.2f;
	return 0;
}

int lmi_bayer_convert(const uint8_t *raw, size_t raw_size,
		      uint32_t width, uint32_t height, uint32_t stride,
		      enum lmi_bayer_phase phase,
		      const struct lmi_bayer_tuning *tuning,
		      uint8_t *bgrx, uint32_t bgrx_stride)
{
	if (!raw || !tuning || !bgrx || width < 4 || height < 2 || width % 4)
		return -1;
	uint32_t packed = width / 4 * 5;
	if (stride < packed || raw_size < (size_t)stride * height)
		return -1;
	if (bgrx_stride < width * 4)
		return -1;
	if (phase < 0 || phase > LMI_BAYER_RGBG)
		return -1;

	uint16_t *lines = malloc((size_t)width * 3 * sizeof(uint16_t));
	if (!lines)
		return -1;
	uint8_t lut[3][LMI_RAW10_MAX + 1];
	lmi_build_lut(tuning, lut);

	/* Three lines are kept: the one above, the current one and the one
	 * below. The first and the last line are used twice. */
	lmi_unpack_line(raw, 0, stride, width, lines);
	if (height > 1)
		lmi_unpack_line(raw, 1, stride, width, lines + width);
	else
		memcpy(lines + width, lines, width * sizeof(uint16_t));
	memcpy(lines + 2 * width, lines, width * sizeof(uint16_t));

	for (uint32_t y = 0; y < height; y++) {
		if (y >= 1) {
			uint32_t source = (y + 1 < height) ? (y + 1) : y;
			lmi_unpack_line(raw, source, stride, width,
					lines + (size_t)((y + 1) % 3) * width);
		}
		const uint16_t *middle = lines + (size_t)(y % 3) * width;
		const uint16_t *up = lines + (size_t)((y + 2) % 3) * width;
		const uint16_t *down = lines + (size_t)((y + 1) % 3) * width;

		uint8_t *out = bgrx + (size_t)y * bgrx_stride;
		for (uint32_t x = 0; x < width; x++) {
			int channel = lmi_bayer_pattern[phase][y & 1][x & 1];
			int own = middle[x];
			int values[3];
			for (int c = 0; c < 3; c++) {
				if (c == channel)
					values[c] = own;
				else
					values[c] = (int)lmi_interpolate(up, middle, down,
									  x, y, width, height,
									  phase, c);
			}
			out[x * 4 + 0] = lut[2][values[2]];
			out[x * 4 + 1] = lut[1][values[1]];
			out[x * 4 + 2] = lut[0][values[0]];
			out[x * 4 + 3] = 255;
		}
	}
	free(lines);
	return 0;
}
