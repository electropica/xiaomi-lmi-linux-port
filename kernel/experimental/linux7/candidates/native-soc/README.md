# Optional native battery percentage candidate

This experimental patch adds an opt-in `qcom_fg.lmi_native_soc` parameter, defaulting to false, to the reconstructed lmi fuel-gauge driver. When enabled, the driver reports its native MSOC-to-percentage conversion and clears the previous full latch. It does not change charge control, voltage, current or termination.

The patch was checked with `patch --dry-run --fuzz=0` against the reconstructed lot 9g tree. It has not been compiled, installed, or tested on hardware, and the complete equivalence of that tree with the currently running kernel has not been established. The optional mode does not calibrate the battery or independently establish the real state of charge.

`simulate-recordings.py` models the driver's conversion against existing, separately sampled gauge and capacity records. The model is not the kernel code. In a hypothetical latch release at raw 240 to 239, the native conversion changes from 94% to 93%; an existing latch holding 100% until that point could therefore cause a visible jump. Actual latch transitions require measurement.

Usage: `python3 simulate-recordings.py /path/to/overnight-9d-device.log /path/to/overnight-9d-day4.csv`. Input recordings are not included because device logs can contain private information.
