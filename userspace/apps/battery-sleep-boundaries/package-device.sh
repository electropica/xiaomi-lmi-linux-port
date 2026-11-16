#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
out=${1:?output directory required}
mkdir -p "$out"
out=$(CDPATH= cd -- "$out" && pwd)
package="$out/battery-sleep-boundaries_0.1.0_all.deb"
[ ! -e "$package" ] || { echo "Refusing to overwrite $package" >&2; exit 1; }
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
chmod 0755 "$stage"
install -d "$stage/DEBIAN" "$stage/usr/libexec" "$stage/usr/lib/systemd/system-sleep"
install -m 755 "$here/battery-sleep-boundaries.py" "$stage/usr/libexec/battery-sleep-boundaries.py"
install -m 755 "$here/95-battery-sleep-boundaries" "$stage/usr/lib/systemd/system-sleep/95-battery-sleep-boundaries"
cat > "$stage/DEBIAN/control" <<'EOF'
Package: battery-sleep-boundaries
Version: 0.1.0
Architecture: all
Maintainer: Mobian project <mobian@localhost>
Depends: python3, coreutils
Section: utils
Priority: optional
Description: Local battery snapshots at system suspend boundaries
 Records battery values before and after system sleep without periodic wakeups.
EOF
cat > "$stage/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
getent group mobian >/dev/null
install -d -o root -g mobian -m 2750 /var/lib/battery-diag
EOF
chmod 755 "$stage/DEBIAN/postinst"
dpkg-deb --build --root-owner-group "$stage" "$package"
sha256sum "$package"
