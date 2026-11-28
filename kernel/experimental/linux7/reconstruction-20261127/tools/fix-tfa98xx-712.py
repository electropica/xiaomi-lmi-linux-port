#!/usr/bin/env python3
"""Adapt the imported TFA98XX driver to the Linux 7.2.12 API.

The vendor driver comes from the 4.19 Mobian tree; the import tool did the
first round of adaptations (dapm accessor, kcontrol accessor, gpiod consumer),
but that import was never compiled.  This script applies the remaining
adaptations, each one with an assertion on the number of matches so a silent
drift is impossible.  It is idempotent.

Adaptations:

  P2  fw_name              the container file name was declared only for the
                            "munch" platform; the driver needs it everywhere
  P3  request_firmware_nowait
                            FW_ACTION_HOTPLUG was removed from the kernel;
                            the parameter is now the "uevent" boolean
  P4  DAI format           SND_SOC_DAIFMT_CBS_CFS was removed with the new
                            DAI flags; the codec is the clock and frame
                            consumer (SND_SOC_DAIFMT_BC_FC)
  P5  irq line test        "!ptr != NULL" was produced by the mechanical
                            replacement of gpio_is_valid(); it is inverted
  P6  gpiod flags          devm_gpiod_get_optional() takes the GPIOD_* flags
  P7  gpio release         devm_gpio_free() on a member that no longer exists
                            (the gpiod consumer releases the lines)
  P8  speaker switch       gpio_direction_output() on the removed member
  P9  interrupt line       gpio_to_irq() on the removed member (dead code)

Usage:
    fix-tfa98xx-712.py [--check] FILE...
"""
import sys

PATCHES = [
    # ------------------------------------------------------------------ P2
    ('P2 fw_name declared for every platform', 1,
     """#if defined(CONFIG_MACH_XIAOMI_MUNCH)
static char *fw_name = "tfa98xx.cnt";
module_param(fw_name, charp, S_IRUGO | S_IWUSR);
MODULE_PARM_DESC(fw_name, "TFA98xx DSP firmware (container file) name.");
#endif
""",
     """/* The vendor driver declared the container file name only for the "munch"
 * platform; the driver needs it on every platform.
 */
static char *fw_name = "tfa98xx.cnt";
module_param(fw_name, charp, S_IRUGO | S_IWUSR);
MODULE_PARM_DESC(fw_name, "TFA98xx DSP firmware (container file) name.");
"""),
    # ------------------------------------------------------------------ P3
    ('P3 request_firmware_nowait uevent flag', 1,
     """	return request_firmware_nowait(THIS_MODULE, FW_ACTION_HOTPLUG, fw_name,
""",
     """	/* FW_ACTION_HOTPLUG was removed: the parameter is now the "uevent"
	 * boolean.
	 */
	return request_firmware_nowait(THIS_MODULE, true, fw_name,
"""),
    # ------------------------------------------------------------------ P4
    ('P4 DAI format flags', 1,
     """	case SND_SOC_DAIFMT_I2S:
		if ((fmt & SND_SOC_DAIFMT_MASTER_MASK) !=
		    SND_SOC_DAIFMT_CBS_CFS) {
""",
     """	case SND_SOC_DAIFMT_I2S:
		/* The new DAI flags replaced SND_SOC_DAIFMT_CBS_CFS: the codec
		 * is the clock and the frame consumer.
		 */
		if ((fmt & SND_SOC_DAIFMT_MASTER_MASK) !=
		    SND_SOC_DAIFMT_BC_FC) {
"""),
    # ------------------------------------------------------------------ P5
    ('P5 interrupt line test', 1,
     """	if (!tfa98xx->irq_gpiod != NULL) {
""",
     """	if (tfa98xx->irq_gpiod == NULL) {
"""),
    # ------------------------------------------------------------------ P6
    ('P6 reset gpiod flags', 1,
     """	tfa98xx->reset_gpiod = devm_gpiod_get_optional(dev, "reset", NULL);
""",
     """	tfa98xx->reset_gpiod = devm_gpiod_get_optional(dev, "reset",
						      GPIOD_OUT_LOW);
"""),
    ('P6 interrupt gpiod flags', 1,
     """	tfa98xx->irq_gpiod = devm_gpiod_get_optional(dev, "irq", NULL);
""",
     """	tfa98xx->irq_gpiod = devm_gpiod_get_optional(dev, "irq", GPIOD_IN);
"""),
    ('P6 speaker switch gpiod flags', 1,
     """	tfa98xx->spk_sw_gpiod = devm_gpiod_get_optional(dev, "spk-sw", NULL);
""",
     """	tfa98xx->spk_sw_gpiod = devm_gpiod_get_optional(dev, "spk-sw",
						       GPIOD_OUT_LOW);
"""),
    # ------------------------------------------------------------------ P7
    ('P7 gpio release', 1,
     """	if (tfa98xx->irq_gpiod != NULL)
		devm_gpio_free(&i2c->dev, tfa98xx->irq_gpio);
	if (tfa98xx->reset_gpiod != NULL)
		devm_gpio_free(&i2c->dev, tfa98xx->reset_gpio);
	if (tfa98xx->spk_sw_gpiod != NULL)
		/* the speaker switch line is released with the gpiod consumer */
""",
     """	/* the reset, interrupt and speaker switch lines are released by the
	 * gpiod consumer interface.
	 */
"""),
    # ------------------------------------------------------------------ P8
    ('P8 speaker switch direction', 1,
     """				if (tfa98xx->spk_sw_gpiod != NULL) {
					gpio_direction_output(
						tfa98xx->spk_sw_gpio, 1);
				}
""",
     """				if (tfa98xx->spk_sw_gpiod != NULL)
					gpiod_set_value_cansleep(
						tfa98xx->spk_sw_gpiod, 1);
"""),
    ('P8 speaker switch direction', 1,
     """				if (tfa98xx->spk_sw_gpiod != NULL) {
					gpio_direction_output(
						tfa98xx->spk_sw_gpio, 0);
				}
""",
     """				if (tfa98xx->spk_sw_gpiod != NULL)
					gpiod_set_value_cansleep(
						tfa98xx->spk_sw_gpiod, 0);
"""),
    # ------------------------------------------------------------------ P9
    ('P9 interrupt number of the gpiod line', 1,
     """			gpio_to_irq(tfa98xx->irq_gpio),
""",
     """			gpiod_to_irq(tfa98xx->irq_gpiod),
"""),
    ('P9 interrupt number of the gpiod line', 1,
     """				gpio_to_irq(tfa98xx->irq_gpio), ret);
""",
     """				gpiod_to_irq(tfa98xx->irq_gpiod), ret);
"""),
    # ----------------------------------------------------------------- P10
    ('P10 bin_attribute callback (register write)', 1,
     """static ssize_t tfa98xx_reg_write(struct file *filp, struct kobject *kobj,
				 struct bin_attribute *bin_attr, char *buf,
""",
     """static ssize_t tfa98xx_reg_write(struct file *filp, struct kobject *kobj,
				 const struct bin_attribute *bin_attr, char *buf,
"""),
    ('P10 bin_attribute callback (rw write)', 1,
     """static ssize_t tfa98xx_rw_write(struct file *filp, struct kobject *kobj,
				struct bin_attribute *bin_attr, char *buf,
""",
     """static ssize_t tfa98xx_rw_write(struct file *filp, struct kobject *kobj,
				const struct bin_attribute *bin_attr, char *buf,
"""),
    ('P10 bin_attribute callback (rw read)', 1,
     """static ssize_t tfa98xx_rw_read(struct file *filp, struct kobject *kobj,
			       struct bin_attribute *bin_attr, char *buf,
""",
     """static ssize_t tfa98xx_rw_read(struct file *filp, struct kobject *kobj,
			       const struct bin_attribute *bin_attr, char *buf,
"""),
    # ----------------------------------------------------------------- P11
    ('P11 i2c probe signature', 1,
     """static int tfa98xx_i2c_probe(struct i2c_client *i2c,
			     const struct i2c_device_id *id)
""",
     """static int tfa98xx_i2c_probe(struct i2c_client *i2c)
"""),
    # ----------------------------------------------------------------- P12
    ('P12 i2c remove signature', 1,
     """static int tfa98xx_i2c_remove(struct i2c_client *i2c)
""",
     """static void tfa98xx_i2c_remove(struct i2c_client *i2c)
"""),
    # ----------------------------------------------------------------- P13
    ('P13 removed SLAB_MEM_SPREAD flag', 1,
     """		(SLAB_HWCACHE_ALIGN | SLAB_RECLAIM_ACCOUNT |
		 SLAB_MEM_SPREAD), /* Cache property */
""",
     """		(SLAB_HWCACHE_ALIGN | SLAB_RECLAIM_ACCOUNT), /* Cache property */
"""),
    # ----------------------------------------------------------------- P14
    ('P14 forward declarations', 1,
     """#define TFA98XX_VERSION TFA98XX_API_REV_STR

#define I2C_RETRIES 50
""",
     """#define TFA98XX_VERSION TFA98XX_API_REV_STR

/* Forward declarations: the kernel builds with -Wmissing-prototypes and
 * these four functions are used before their definition.
 */
int nxp_spk_id_get(struct device_node *np);
int send_tfa_cal_apr(void *buf, int cmd_size, bool bRead);
int tfa98xx_init_misc_device(struct tfa98xx *tfa98xx);
void tfa98xx_remove_misc_device(struct tfa98xx *tfa98xx);

#define I2C_RETRIES 50
"""),
]


def fix_remove_return(text):
    """The remove callback became void: its "return 0;" must become "return;"."""
    marker = 'static void tfa98xx_i2c_remove(struct i2c_client *i2c)\n'
    start = text.find(marker)
    if start < 0:
        return text, 0
    end = text.find('\n}\n', start)
    if end < 0:
        return text, 0
    body = text[start:end + 1]
    if '\n\treturn 0;\n' not in body:
        return text, 0
    new_body = body.replace('\n\treturn 0;\n', '\n\treturn;\n')
    return text[:start] + new_body + text[end:], 1


def main(argv):
    check = False
    files = []
    for a in argv[1:]:
        if a == '--check':
            check = True
        else:
            files.append(a)
    if not files:
        print('usage: fix-tfa98xx-712.py [--check] FILE...')
        return 2

    rc = 0
    for path in files:
        with open(path, 'r', encoding='utf-8', errors='surrogateescape') as f:
            text = f.read()
        pending = 0
        for label, count, old, new in PATCHES:
            n = text.count(old)
            if n == 0:
                continue
            if n != count:
                print('  !! %s: %s has %d matches, expected %d'
                      % (path, label, n, count))
                rc = 1
                continue
            pending += n
            if not check:
                text = text.replace(old, new)
        if not check:
            text, n = fix_remove_return(text)
            pending += n
        if not check:
            with open(path, 'w', encoding='utf-8', errors='surrogateescape') as f:
                f.write(text)
        state = 'would fix' if check and pending else ('fixed' if pending else 'already ok')
        print('%-10s %s (%d replacements)' % (state, path, pending))
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv))
