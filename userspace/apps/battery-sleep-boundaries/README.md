# Battery sleep boundaries

The systemd-sleep hook records a local `pre` and `post` snapshot around suspend. It makes no periodic wakeups and does not write to sysfs. A three-second timeout and a successful wrapper exit prevent a failed snapshot from indefinitely blocking suspend. Captured fields include both clocks, boot ID, battery status and capacity, current, voltage, temperature, available charge counter, suspend count and the MSOC byte and mirror when readable. Missing fields are marked explicitly.

The journal is `/var/lib/battery-diag/sleep-boundaries.csv`, root-owned and readable by the mobian group. Files with unexpected headers or unsafe ownership, permissions or symlinks are rejected. Captures before installation cannot be reconstructed. On 16 November an end-to-end test recorded both boundaries around an s2idle cycle; the post snapshot already reported charging, so it cannot establish an uninterrupted discharge comparison.

Use `sh package-device.sh OUTPUT_DIRECTORY` to build the optional Debian package; it never installs the package and refuses to overwrite an existing output. On removal, the package does not delete recorded data. `test_boundaries.py` uses fake sysfs data; ownership and symlink tests require root in an isolated test environment.
