#!/bin/sh
# Build local ARM64 Debian packages; never install or touch existing logs.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
apps=$(dirname "$here")
out=${1:?output directory required}
[ "$(dpkg --print-architecture)" = arm64 ] || { echo 'Run on arm64; cross-build is not configured.' >&2; exit 1; }
grep -qx 'version = "0.1.1"' "$apps/battery-logger/Cargo.toml" || { echo 'Logger version mismatch' >&2; exit 1; }
grep -qx 'version = "0.1.13"' "$apps/battery-viewer/Cargo.toml" || { echo 'Viewer version mismatch' >&2; exit 1; }
mkdir -p "$out"
out=$(CDPATH= cd -- "$out" && pwd)
for name in battery-logger_0.1.1_arm64.deb battery-viewer_0.1.13_arm64.deb battery-sleep-boundaries_0.1.0_all.deb; do
    [ ! -e "$out/$name" ] || { echo "Refusing to overwrite $out/$name" >&2; exit 1; }
done
cargo test --release --locked --manifest-path "$apps/battery-logger/Cargo.toml"
cargo test --release --locked --manifest-path "$apps/battery-viewer/Cargo.toml"
cargo build --release --locked --manifest-path "$apps/battery-logger/Cargo.toml"
cargo build --release --locked --manifest-path "$apps/battery-viewer/Cargo.toml"
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
install -d "$stage/logger/DEBIAN" "$stage/logger/usr/bin" "$stage/logger/lib/systemd/system"
install -m 755 "$apps/battery-logger/target/release/battery-logger" "$stage/logger/usr/bin/battery-logger"
cat > "$stage/logger/DEBIAN/control" <<'EOF'
Package: battery-logger
Version: 0.1.1
Architecture: arm64
Maintainer: Mobian project <mobian@localhost>
Depends: libc6, libgcc-s1, systemd
Section: utils
Priority: optional
Description: Battery diagnostics logger
 Records local battery samples and system suspension intervals.
EOF
cat > "$stage/logger/lib/systemd/system/battery-logger.service" <<'EOF'
[Unit]
Description=battery-diag : journalisation de la batterie et du noyau
After=default.target

[Service]
Type=simple
User=mobian
Environment=HOME=/home/mobian
Environment=XDG_DATA_HOME=/home/mobian/.local/share
WorkingDirectory=/home/mobian
ExecStart=/usr/bin/battery-logger
Restart=on-failure
RestartSec=30
Nice=10
IOSchedulingClass=idle

[Install]
WantedBy=multi-user.target
EOF
install -d "$stage/viewer/DEBIAN" "$stage/viewer/usr/bin" "$stage/viewer/usr/share/applications"
install -m 755 "$apps/battery-viewer/target/release/battery-viewer" "$stage/viewer/usr/bin/battery-viewer"
cat > "$stage/viewer/DEBIAN/control" <<'EOF'
Package: battery-viewer
Version: 0.1.13
Architecture: arm64
Maintainer: Mobian project <mobian@localhost>
Depends: battery-logger (>= 0.1.1), libc6, libgtk-4-1, libadwaita-1-0, libglib2.0-0t64, libcairo2
Section: utils
Priority: optional
Description: Graphical viewer for the battery logger
 Displays battery observations and suspension time without claiming that
 hardware deep sleep is measured.
EOF
cat > "$stage/viewer/usr/share/applications/battery-viewer.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Battery Diag
Name[fr]=Diagnostic batterie
Comment=Visualise les relevés de batterie
Exec=battery-viewer
Icon=battery-full-symbolic
Terminal=false
Categories=GTK;Utility;System;Monitor;
StartupNotify=true
StartupWMClass=org.battery_diag.Viewer
X-Purism-FormFactor=Workstation;Mobile;
EOF
dpkg-deb --build --root-owner-group "$stage/logger" "$out/battery-logger_0.1.1_arm64.deb"
dpkg-deb --build --root-owner-group "$stage/viewer" "$out/battery-viewer_0.1.13_arm64.deb"
sh "$apps/battery-sleep-boundaries/package-device.sh" "$out"
sha256sum "$out/battery-logger_0.1.1_arm64.deb" "$out/battery-viewer_0.1.13_arm64.deb" "$out/battery-sleep-boundaries_0.1.0_all.deb"
echo BATTERY_PACKAGES_BUILT_NOT_INSTALLED
