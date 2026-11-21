# Battery viewer

This GTK4/Libadwaita viewer reads the local CSV produced by the separately installed `battery-logger` service. It does not install or replace that service. No logs or personal data belong in this directory.

Build with Rust, Cargo, GTK4 and libadwaita development headers: `cargo test --locked` then `cargo build --release --locked`. Version 0.1.13 displays the last complete sleep boundary pair prominently even if the sleep started before the selected time window, with an explicit whole-sleep label. Logger 0.1.1 adds system-suspend intervals; older logs lack these fields and unavailable values appear as N/A. Deep hardware sleep is not measured. The independent Debian packaging and clean-image integration are in `../battery-packaging` and `../../mobian-clean-linux7`.

The displayed battery power is derived from voltage and battery current, not total USB input power or per-service energy. The screen-off average uses only samples marked discharging, screen off and not resume; sparse samples do not prove energy consumption during system suspend.

The graph breaks lines across gaps longer than six minutes instead of inventing values for missing samples. Screen-state bands do not extend across those gaps. The top summary shows the latest sampled capacity and charging status; the nearby timestamp shows when it was measured. Short suspension durations include seconds.
