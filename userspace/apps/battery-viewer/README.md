# Battery viewer

This GTK4/Libadwaita viewer reads the local CSV produced by the separately installed `battery-logger` service. It does not install or replace that service. No logs or personal data belong in this directory.

Build with Rust, Cargo, GTK4 and libadwaita development headers: `cargo test --locked` then `cargo build --release --locked`. The phone-tested viewer package was installed separately as version 0.1.3; this source keeps the same user-facing behavior and corrects misleading legacy comments and test names. Debian packaging and a clean-image integration are not yet provided here. The installed logger 0.1.0 does not supply all suspension fields: unavailable values appear as N/A, and deep hardware sleep is not measured.

The displayed battery power is derived from voltage and battery current, not total USB input power or per-service energy. The screen-off average uses only samples marked discharging, screen off and not resume; sparse samples do not prove energy consumption during system suspend.
