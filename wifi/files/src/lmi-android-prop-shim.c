static int streq(const char *a, const char *b)
{
	while (*a && *b && *a == *b) {
		a++;
		b++;
	}
	return *a == *b;
}

static int copy_value(char *dst, const char *src)
{
	int len = 0;

	if (!src)
		src = "";
	while (src[len]) {
		dst[len] = src[len];
		len++;
	}
	dst[len] = 0;
	return len;
}

int property_get(const char *key, char *value, const char *default_value)
{
	if (streq(key, "ro.baseband"))
		return copy_value(value, "mdm");
	if (streq(key, "ro.bootmode"))
		return copy_value(value, "normal");
	if (streq(key, "ro.board.platform"))
		return copy_value(value, "kona");
	if (streq(key, "ro.build.type"))
		return copy_value(value, "user");
	if (streq(key, "ro.debuggable"))
		return copy_value(value, "0");
	if (streq(key, "ro.boot.product.hardware.sku"))
		return copy_value(value, "std");
	if (streq(key, "ro.product.vendor.device") ||
	    streq(key, "ro.product.device"))
		return copy_value(value, "lmi");
	if (streq(key, "persist.vendor.cnss-daemon.kmsg_logging") ||
	    streq(key, "persist.vendor.cnss-daemon.debug_level"))
		return copy_value(value, "1");
	if (streq(key, "persist.vendor.cnss-daemon.hw_trc_disable_override"))
		return copy_value(value, "0");
	return copy_value(value, default_value);
}

int property_get_int32(const char *key, int default_value)
{
	if (streq(key, "persist.vendor.cnss-daemon.kmsg_logging") ||
	    streq(key, "persist.vendor.cnss-daemon.debug_level"))
		return 1;
	if (streq(key, "persist.vendor.cnss-daemon.hw_trc_disable_override"))
		return 0;
	return default_value;
}
