/* SPDX-License-Identifier: MIT
 *
 * Host test of the Bayer RAW10 conversion.
 *
 * Without arguments it runs the synthetic checks. With a captured frame it
 * measures that frame, converts it and writes a PPM that can be looked at.
 */
#include "bayer10-convert.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures;

#define CHECK(condition, message) do { \
	if (!(condition)) { \
		printf("FAIL %s (%s:%d)\n", (message), __FILE__, __LINE__); \
		failures++; \
	} \
} while (0)

/* Pack four 10 bit values the way the sensor does. */
static void pack_group(uint8_t *out, const uint16_t values[4])
{
	for (int i = 0; i < 4; i++)
		out[i] = (uint8_t)(values[i] >> 2);
	uint8_t low = 0;
	for (int i = 0; i < 4; i++)
		low |= (uint8_t)((values[i] & 3) << (2 * i));
	out[4] = low;
}

static void synthetic(void)
{
	/* A 4x2 frame, GRBG, with a stride of 9 bytes for 5 packed bytes. */
	const uint16_t row0[4] = { 100, 800, 200, 900 };
	const uint16_t row1[4] = { 400, 300, 500, 600 };
	uint8_t frame[2 * 9];
	memset(frame, 0xaa, sizeof(frame));
	pack_group(frame, row0);
	/* The second line starts after the stride, not after the packed
	 * bytes: the padding of the first line must be preserved. */
	pack_group(frame + 9, row1);

	struct lmi_bayer_tuning tuning;
	lmi_bayer_default_tuning(&tuning);
	tuning.black[0] = tuning.black[1] = tuning.black[2] = 0;
	tuning.span[0] = tuning.span[1] = tuning.span[2] = 1023;
	tuning.gain[0] = tuning.gain[1] = tuning.gain[2] = 1.0f;
	tuning.gamma = 1.0f;

	uint8_t bgrx[4 * 2 * 4];
	memset(bgrx, 0, sizeof(bgrx));
	int rc = lmi_bayer_convert(frame, sizeof(frame), 4, 2, 9, LMI_BAYER_GRBG,
				   &tuning, bgrx, 4 * 4);
	CHECK(rc == 0, "the synthetic frame converts");

	/* The red pixel of the first cell is at x=1, the blue one at x=0,y=1.
	 * With a black level of zero, a span of 1023 and a gain of one, the
	 * tone curve is the linear scale from 0 to 255. */
#define EXPECT(value) ((int)((value) * 255.0f / 1023.0f + 0.5f))
	if (bgrx[1 * 4 + 2] != EXPECT(800))
		printf("  red at (1,0) = %d, expected %d\n", bgrx[1 * 4 + 2], EXPECT(800));
	CHECK(bgrx[1 * 4 + 2] == EXPECT(800), "the red sample is read at the GRBG place");
	if (bgrx[0 * 4 + 0] != EXPECT(400))
		printf("  blue at (0,1) = %d, expected %d\n", bgrx[0 * 4 + 0], EXPECT(400));
	CHECK(bgrx[0 * 4 + 0] == EXPECT(400), "the blue sample is read at the GRBG place");
	CHECK(bgrx[0 * 4 + 1] == EXPECT(100), "the green sample is read at the GRBG place");

	/* The colours that a pixel does not hold must be interpolated, not
	 * dropped: at a green pixel the red neighbours are in the same row,
	 * at a blue pixel the red neighbours are the four diagonals. A
	 * demosaic that only looks at the four direct neighbours loses half
	 * of the red and of the blue samples. */
	CHECK(bgrx[0 * 4 + 2] > 0, "the red of a green pixel is interpolated");
	CHECK(bgrx[0 * 4 + 0] > 0, "the blue of a green pixel is interpolated");
	CHECK(bgrx[1 * 4 + 0] > 0, "the blue of a red pixel is interpolated");
	CHECK(bgrx[0 * 4 + 2] != 0 && bgrx[0 * 4 + 2] != 255,
	      "the interpolated red is not saturated");

	/* The padding must not leak into the picture: the last pixel of the
	 * first line is the red one of the second group of the line. */
	CHECK(bgrx[3 * 4 + 2] == EXPECT(900), "the padding of the line is ignored");

	/* A frame that is too short must be refused. */
	CHECK(lmi_bayer_convert(frame, sizeof(frame) - 1, 4, 2, 9, LMI_BAYER_GRBG,
				&tuning, bgrx, 4 * 4) < 0,
	      "a truncated frame is refused");
	CHECK(lmi_bayer_convert(frame, sizeof(frame), 4, 2, 4, LMI_BAYER_GRBG,
				&tuning, bgrx, 4 * 4) < 0,
	      "a stride shorter than the line is refused");

	/* The media bus codes map to the right phase. */
	CHECK(lmi_bayer_phase_from_mbus(0x300a) == LMI_BAYER_GRBG, "SGRBG10 is GRBG");
	CHECK(lmi_bayer_phase_from_mbus(0x300b) == LMI_BAYER_GBRG, "SGBRG10 is GBRG");
	CHECK(lmi_bayer_phase_from_mbus(0x300c) == LMI_BAYER_BGGR, "SBGGR10 is BGGR");
	CHECK(lmi_bayer_phase_from_mbus(0x300d) == LMI_BAYER_RGBG, "SRGBG10 is RGBG");
	CHECK(lmi_bayer_phase_from_mbus(0x1234) < 0, "an unknown code is refused");

	/* The measurement must cover the three channels of the mosaic: the
	 * mosaic alternates on both axes, so a sampling that skips lines
	 * would leave one channel without any sample. */
	uint8_t mosaic[4 * 9];
	memset(mosaic, 0, sizeof(mosaic));
	for (uint32_t y = 0; y < 4; y++) {
		uint16_t values[4];
		for (uint32_t x = 0; x < 4; x++) {
			uint16_t value = (uint16_t)(100 + y * 40 + x * 10);
			if (lmi_bayer_channel(LMI_BAYER_GRBG, x, y) == 0)
				value = 900;	/* the red plane stands out */
			values[x] = value;
		}
		pack_group(mosaic + y * 9, values);
	}
	struct lmi_bayer_tuning measured;
	CHECK(lmi_bayer_analyse(mosaic, sizeof(mosaic), 4, 4, 9, LMI_BAYER_GRBG,
				&measured) == 0,
	      "a synthetic frame can be measured");
	CHECK(measured.black[0] <= measured.black[1] + 40,
	      "the measured black level stays in the expected range");
	CHECK(measured.span[0] > 0 && measured.span[1] > 0 && measured.span[2] > 0,
	      "the three channels get a usable span");
}

static int convert_file(const char *path, const char *out_path,
			uint32_t width, uint32_t height, uint32_t stride)
{
	FILE *file = fopen(path, "rb");
	if (!file) {
		printf("cannot open %s\n", path);
		return 1;
	}
	fseek(file, 0, SEEK_END);
	long size = ftell(file);
	fseek(file, 0, SEEK_SET);
	if (size <= 0) {
		fclose(file);
		printf("%s is empty\n", path);
		return 1;
	}
	uint8_t *raw = malloc((size_t)size);
	if (!raw || fread(raw, 1, (size_t)size, file) != (size_t)size) {
		free(raw);
		fclose(file);
		printf("cannot read %s\n", path);
		return 1;
	}
	fclose(file);

	struct lmi_bayer_tuning tuning;
	int rc = lmi_bayer_analyse(raw, (size_t)size, width, height, stride,
				   LMI_BAYER_GRBG, &tuning);
	if (rc < 0) {
		free(raw);
		printf("the frame cannot be measured\n");
		return 1;
	}
	printf("measured black level : %d %d %d\n",
	       tuning.black[0], tuning.black[1], tuning.black[2]);
	printf("measured span        : %d %d %d\n",
	       tuning.span[0], tuning.span[1], tuning.span[2]);
	printf("white balance gains  : %.3f %.3f %.3f\n",
	       tuning.gain[0], tuning.gain[1], tuning.gain[2]);

	uint32_t bgrx_stride = width * 4;
	uint8_t *bgrx = malloc((size_t)bgrx_stride * height);
	if (!bgrx) {
		free(raw);
		printf("out of memory\n");
		return 1;
	}
	rc = lmi_bayer_convert(raw, (size_t)size, width, height, stride,
			       LMI_BAYER_GRBG, &tuning, bgrx, bgrx_stride);
	if (rc < 0) {
		free(raw);
		free(bgrx);
		printf("the frame cannot be converted\n");
		return 1;
	}
	free(raw);

	FILE *out = fopen(out_path, "wb");
	if (!out) {
		free(bgrx);
		printf("cannot write %s\n", out_path);
		return 1;
	}
	fprintf(out, "P6\n%u %u\n255\n", width, height);
	for (uint32_t y = 0; y < height; y++) {
		for (uint32_t x = 0; x < width; x++) {
			fputc(bgrx[(size_t)y * bgrx_stride + x * 4 + 0], out);
			fputc(bgrx[(size_t)y * bgrx_stride + x * 4 + 1], out);
			fputc(bgrx[(size_t)y * bgrx_stride + x * 4 + 2], out);
		}
	}
	fclose(out);
	free(bgrx);
	printf("written %s\n", out_path);
	return 0;
}

int main(int argc, char **argv)
{
	synthetic();
	if (failures)
		printf("%d synthetic check(s) failed\n", failures);
	else
		printf("the synthetic checks pass\n");
	if (argc >= 5)
		return convert_file(argv[1], argv[2],
				    (uint32_t)strtoul(argv[3], NULL, 10),
				    (uint32_t)strtoul(argv[4], NULL, 10),
				    (uint32_t)strtoul(argv[5], NULL, 10));
	return failures ? 1 : 0;
}
