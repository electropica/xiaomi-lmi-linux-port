#!/bin/sh
# Configure the Debian and Mobian APT repositories for the clean Linux 7 image.
#
# The exact configuration used by the working handset is reproduced here:
#
#   /etc/apt/sources.list
#     deb http://deb.debian.org/debian trixie main
#     deb http://security.debian.org/debian-security trixie-security main
#   /etc/apt/sources.list.d/mobian.sources
#     Types: deb
#     URIs: https://repo.mobian.org/
#     Suites: trixie
#     Components: main
#     Signed-By: /usr/share/keyrings/mobian-archive-keyring.gpg
#   /etc/apt/preferences.d/00-mobian-priority
#     Package: *
#     Pin: release o=Mobian
#     Pin-Priority: 700
#
# The priority is what makes the Mobian builds of alsa-ucm-conf, libgtk-3 and
# gnome-clocks win over the Debian ones. Losing it silently degrades the
# headset.
set -eu

DEBIAN_SUITE=$1
SUITE=$2

[ -n "$DEBIAN_SUITE" ] || { echo 'debian suite required' >&2; exit 1; }
[ -n "$SUITE" ] || { echo 'mobian suite required' >&2; exit 1; }

# The Mobian repository ships a deb822 file. Rewrite only the suite, and fail
# loudly if the expected key is absent, instead of silently producing an
# unconfigured repository.
MOBIAN_SOURCES=/etc/apt/sources.list.d/mobian.sources
[ -f "$MOBIAN_SOURCES" ] || { echo "missing $MOBIAN_SOURCES" >&2; exit 1; }
grep -q '^Suites:' "$MOBIAN_SOURCES" || { echo "no Suites: key in $MOBIAN_SOURCES" >&2; exit 1; }
sed -i "s/^Suites:.*/Suites: ${SUITE}/" "$MOBIAN_SOURCES"
grep -q "^Suites: ${SUITE}\$" "$MOBIAN_SOURCES" || { echo "suite rewrite failed" >&2; exit 1; }

# security.debian.org serves the security suite under the /debian-security
# prefix for trixie and later. The bare host is the pre-trixie layout and
# does not serve trixie-security.
#
# The -updates suite is mandatory, not cosmetic: tzdata 2026f-0+deb13u1 only
# exists in trixie-updates, and the image verification requires it. Without
# this line the build fails the tzdata check at the very end.
case "$DEBIAN_SUITE" in
    bullseye|bookworm|trixie)
        printf 'deb http://deb.debian.org/debian %s main\n' "$DEBIAN_SUITE" > /etc/apt/sources.list
        printf 'deb http://deb.debian.org/debian %s-updates main\n' "$DEBIAN_SUITE" >> /etc/apt/sources.list
        printf 'deb http://security.debian.org/debian-security %s-security main\n' "$DEBIAN_SUITE" >> /etc/apt/sources.list
        ;;
    *)
        printf 'deb http://deb.debian.org/debian %s main\n' "$DEBIAN_SUITE" > /etc/apt/sources.list
        ;;
esac

install -d -m 0755 /etc/apt/preferences.d
cat > /etc/apt/preferences.d/00-mobian-priority <<'EOF'
Package: *
Pin: release o=Mobian
Pin-Priority: 700
EOF

echo "APT_SOURCES_READY debian=${DEBIAN_SUITE} mobian=${SUITE}"
