// SPDX-License-Identifier: GPL-2.0-only
/*
 * DRM panel driver for the Samsung AMS667UU01 DDIC AMOLED panel fitted to the
 * Xiaomi POCO F2 Pro / Redmi K30 Pro (board lmi).
 *
 * Base: the community lmi mainline driver
 *   (yuweiyuan8/linux-xiaomi-thyme-mainline, v7.2-rc5,
 *    drivers/gpu/drm/panel/panel-samsung-ams667uu01.c), itself generated from
 *   the vendor 4.19 device tree.
 * This port keeps the Linux 7.2 DRM panel API (devm_drm_panel_alloc) and adds
 * what the community driver left to the bootloader state:
 *
 *   - explicit panel rail control: vddio 1.88 V and vci 3.0 V, enabled in the
 *     vendor order with the vendor delays (6 ms after vddio, 10 ms after vci,
 *     10 ms before vci is dropped);
 *   - the vendor DCS power-on sequence, including "35 00" (tear off) and
 *     "55 00", which the generated community sequence drops;
 *   - the vendor geometry (1080x2400 @ 60 Hz, hfp 64 / hpw 20 / hbp 64,
 *     vfp 34 / vpw 20 / vbp 34) and backlight range (DCS 0x51, 0..2047,
 *     vendor initial level 536).
 *
 * Tear handling: the vendor sequence turns the panel TE signal off ("35 00").
 * Upstream v7.2 has no TE source configured for the lmi DSI link, so leaving
 * tear-on enabled would stall the panel on a TE signal that never arrives.
 * This is a deliberate divergence from the community driver, which sends
 * tear-on (0x35 0x01) and relies on a TE path this board does not describe.
 */

#include <linux/backlight.h>
#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/module.h>
#include <linux/regulator/consumer.h>

#include <video/mipi_display.h>

#include <drm/drm_mipi_dsi.h>
#include <drm/drm_modes.h>
#include <drm/drm_panel.h>
#include <drm/drm_probe_helper.h>

struct ams667uu01 {
	struct drm_panel panel;
	struct mipi_dsi_device *dsi;
	struct gpio_desc *reset_gpio;
	struct regulator *vddio;
	struct regulator *vci;
};

static inline struct ams667uu01 *to_ams667uu01(struct drm_panel *panel)
{
	return container_of(panel, struct ams667uu01, panel);
}

static void ams667uu01_reset(struct ams667uu01 *ctx)
{
	/* reset-gpios is GPIO_ACTIVE_LOW: 1 asserts reset, 0 releases it. */
	gpiod_set_value_cansleep(ctx->reset_gpio, 1);
	usleep_range(1000, 2000);
	gpiod_set_value_cansleep(ctx->reset_gpio, 0);
	usleep_range(10000, 11000);
}

static int ams667uu01_enable_rails(struct ams667uu01 *ctx)
{
	int ret;

	ret = regulator_enable(ctx->vddio);
	if (ret < 0)
		return ret;

	/* vendor kona-sde-display.dtsi: vddio post-on 6 ms */
	usleep_range(6000, 6000);

	ret = regulator_enable(ctx->vci);
	if (ret < 0) {
		regulator_disable(ctx->vddio);
		return ret;
	}

	/* vendor kona-sde-display.dtsi: vci post-on 10 ms */
	usleep_range(10000, 10000);

	return 0;
}

static void ams667uu01_disable_rails(struct ams667uu01 *ctx)
{
	/* vendor kona-sde-display.dtsi: vci pre-off 10 ms */
	usleep_range(10000, 10000);
	regulator_disable(ctx->vci);
	regulator_disable(ctx->vddio);
}

/*
 * Vendor power-on sequence, transcribed from
 * qcom,mdss-dsi-on-command in the lmi 4.19 device tree.
 */
static int ams667uu01_on(struct ams667uu01 *ctx)
{
	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

	mipi_dsi_dcs_exit_sleep_mode_multi(&dsi_ctx);
	mipi_dsi_usleep_range(&dsi_ctx, 10000, 11000);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x35, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb7, 0x01, 0x4b);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);
	mipi_dsi_dcs_set_page_address_multi(&dsi_ctx, 0x0000, 0x095f);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfc, 0x5a, 0x5a);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xe9,
				     0x11, 0x75, 0xa5, 0x8e, 0x76, 0xa6, 0x37,
				     0xbe, 0x00, 0x32, 0x32);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xe1,
				     0x00, 0x00, 0x02, 0x02, 0x42, 0x02);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xe2,
				     0x00, 0x00, 0x00, 0x00, 0x00, 0x00);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x0c);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xe1, 0x19);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xb0, 0x09);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xee, 0x07);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xf0, 0xa5, 0xa5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0xfc, 0xa5, 0xa5);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x53, 0x20);
	mipi_dsi_dcs_set_display_brightness_multi(&dsi_ctx, 0x0000);
	mipi_dsi_dcs_write_seq_multi(&dsi_ctx, 0x55, 0x00);
	mipi_dsi_msleep(&dsi_ctx, 67);
	mipi_dsi_dcs_set_display_on_multi(&dsi_ctx);

	return dsi_ctx.accum_err;
}

static int ams667uu01_off(struct ams667uu01 *ctx)
{
	struct mipi_dsi_multi_context dsi_ctx = { .dsi = ctx->dsi };

	mipi_dsi_dcs_set_display_off_multi(&dsi_ctx);
	mipi_dsi_usleep_range(&dsi_ctx, 40, 50);
	mipi_dsi_dcs_enter_sleep_mode_multi(&dsi_ctx);
	mipi_dsi_msleep(&dsi_ctx, 120);

	return dsi_ctx.accum_err;
}

static int ams667uu01_prepare(struct drm_panel *panel)
{
	struct ams667uu01 *ctx = to_ams667uu01(panel);
	struct device *dev = &ctx->dsi->dev;
	int ret;

	ret = ams667uu01_enable_rails(ctx);
	if (ret < 0)
		return dev_err_probe(dev, ret, "Failed to enable panel rails\n");

	ams667uu01_reset(ctx);

	ret = ams667uu01_on(ctx);
	if (ret < 0) {
		dev_err(dev, "Failed to initialize panel: %d\n", ret);
		gpiod_set_value_cansleep(ctx->reset_gpio, 1);
		ams667uu01_disable_rails(ctx);
		return ret;
	}

	return 0;
}

static int ams667uu01_unprepare(struct drm_panel *panel)
{
	struct ams667uu01 *ctx = to_ams667uu01(panel);
	struct device *dev = &ctx->dsi->dev;
	int ret;

	ret = ams667uu01_off(ctx);
	if (ret < 0)
		dev_err(dev, "Failed to un-initialize panel: %d\n", ret);

	gpiod_set_value_cansleep(ctx->reset_gpio, 1);
	ams667uu01_disable_rails(ctx);

	return 0;
}

/*
 * Vendor timing: 1080x2400 @ 60 Hz, hfp 64 / hpw 20 / hbp 64,
 * vfp 34 / vpw 20 / vbp 34. 183315 kHz matches the vendor
 * qcom,mdss-dsi-panel-clockrate of 1106000000 over four lanes at 24 bpp.
 */
static const struct drm_display_mode ams667uu01_mode = {
	.clock = (1080 + 64 + 20 + 64) * (2400 + 34 + 20 + 34) * 60 / 1000,
	.hdisplay = 1080,
	.hsync_start = 1080 + 64,
	.hsync_end = 1080 + 64 + 20,
	.htotal = 1080 + 64 + 20 + 64,
	.vdisplay = 2400,
	.vsync_start = 2400 + 34,
	.vsync_end = 2400 + 34 + 20,
	.vtotal = 2400 + 34 + 20 + 34,
	.width_mm = 69,
	.height_mm = 154,
	.type = DRM_MODE_TYPE_DRIVER | DRM_MODE_TYPE_PREFERRED,
};

static int ams667uu01_get_modes(struct drm_panel *panel,
				struct drm_connector *connector)
{
	return drm_connector_helper_get_modes_fixed(connector, &ams667uu01_mode);
}

static const struct drm_panel_funcs ams667uu01_panel_funcs = {
	.prepare = ams667uu01_prepare,
	.unprepare = ams667uu01_unprepare,
	.get_modes = ams667uu01_get_modes,
};

static int ams667uu01_bl_update_status(struct backlight_device *bl)
{
	struct mipi_dsi_device *dsi = bl_get_data(bl);
	u16 brightness = backlight_get_brightness(bl);
	int ret;

	dsi->mode_flags &= ~MIPI_DSI_MODE_LPM;

	ret = mipi_dsi_dcs_set_display_brightness_large(dsi, brightness);
	if (ret < 0)
		return ret;

	dsi->mode_flags |= MIPI_DSI_MODE_LPM;

	return 0;
}

static int ams667uu01_bl_get_brightness(struct backlight_device *bl)
{
	struct mipi_dsi_device *dsi = bl_get_data(bl);
	u16 brightness;
	int ret;

	dsi->mode_flags &= ~MIPI_DSI_MODE_LPM;

	ret = mipi_dsi_dcs_get_display_brightness_large(dsi, &brightness);
	if (ret < 0)
		return ret;

	dsi->mode_flags |= MIPI_DSI_MODE_LPM;

	return brightness;
}

static const struct backlight_ops ams667uu01_bl_ops = {
	.update_status = ams667uu01_bl_update_status,
	.get_brightness = ams667uu01_bl_get_brightness,
};

static struct backlight_device *
ams667uu01_create_backlight(struct mipi_dsi_device *dsi)
{
	struct device *dev = &dsi->dev;
	const struct backlight_properties props = {
		.type = BACKLIGHT_RAW,
		.brightness = 536,
		.max_brightness = 2047,
	};

	return devm_backlight_device_register(dev, dev_name(dev), dev, dsi,
					      &ams667uu01_bl_ops, &props);
}

static int ams667uu01_probe(struct mipi_dsi_device *dsi)
{
	struct device *dev = &dsi->dev;
	struct ams667uu01 *ctx;
	int ret;

	ctx = devm_drm_panel_alloc(dev, struct ams667uu01, panel,
				   &ams667uu01_panel_funcs,
				   DRM_MODE_CONNECTOR_DSI);
	if (IS_ERR(ctx))
		return PTR_ERR(ctx);

	ctx->vddio = devm_regulator_get(dev, "vddio");
	if (IS_ERR(ctx->vddio))
		return dev_err_probe(dev, PTR_ERR(ctx->vddio),
				     "Failed to get vddio regulator\n");

	ctx->vci = devm_regulator_get(dev, "vci");
	if (IS_ERR(ctx->vci))
		return dev_err_probe(dev, PTR_ERR(ctx->vci),
				     "Failed to get vci regulator\n");

	/* keep the panel in reset until the rails are up */
	ctx->reset_gpio = devm_gpiod_get(dev, "reset", GPIOD_OUT_HIGH);
	if (IS_ERR(ctx->reset_gpio))
		return dev_err_probe(dev, PTR_ERR(ctx->reset_gpio),
				     "Failed to get reset-gpios\n");

	ctx->dsi = dsi;
	mipi_dsi_set_drvdata(dsi, ctx);

	dsi->lanes = 4;
	dsi->format = MIPI_DSI_FMT_RGB888;
	dsi->mode_flags = MIPI_DSI_MODE_VIDEO_BURST |
			  MIPI_DSI_CLOCK_NON_CONTINUOUS | MIPI_DSI_MODE_LPM;

	ctx->panel.prepare_prev_first = true;

	ctx->panel.backlight = ams667uu01_create_backlight(dsi);
	if (IS_ERR(ctx->panel.backlight))
		return dev_err_probe(dev, PTR_ERR(ctx->panel.backlight),
				     "Failed to create backlight\n");

	drm_panel_add(&ctx->panel);

	ret = mipi_dsi_attach(dsi);
	if (ret < 0) {
		drm_panel_remove(&ctx->panel);
		return dev_err_probe(dev, ret, "Failed to attach to DSI host\n");
	}

	return 0;
}

static void ams667uu01_remove(struct mipi_dsi_device *dsi)
{
	struct ams667uu01 *ctx = mipi_dsi_get_drvdata(dsi);
	int ret;

	ret = mipi_dsi_detach(dsi);
	if (ret < 0)
		dev_err(&dsi->dev, "Failed to detach from DSI host: %d\n", ret);

	drm_panel_remove(&ctx->panel);
}

static const struct of_device_id ams667uu01_of_match[] = {
	{ .compatible = "xiaomi,lmi-ams667uu01" },
	{ /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, ams667uu01_of_match);

static struct mipi_dsi_driver ams667uu01_driver = {
	.probe = ams667uu01_probe,
	.remove = ams667uu01_remove,
	.driver = {
		.name = "panel-samsung-ams667uu01",
		.of_match_table = ams667uu01_of_match,
	},
};
module_mipi_dsi_driver(ams667uu01_driver);

MODULE_DESCRIPTION("DRM driver for the xiaomi j11 38 08 0a fhd AMOLED panel");
MODULE_LICENSE("GPL");
