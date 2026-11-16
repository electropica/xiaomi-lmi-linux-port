# Battery logger

A local collector for battery and system observations. Version 0.1.1 adds elapsed and system-suspend seconds per interval using one pair of CLOCK_BOOTTIME and CLOCK_MONOTONIC readings. It does not measure hardware deep sleep or per-process energy. The first sample after a restart has no prior interval.

Build with Rust and Cargo: `cargo test --locked` and `cargo build --release --locked`. When CSV columns change, the existing file is archived without overwriting an existing archive. Preserve and verify logs before any service upgrade. The viewer reads both current and archived CSVs. Installation/service packaging and clean-image integration require separate review; this source does not launch a service or alter a device by itself.
