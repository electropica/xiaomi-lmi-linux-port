#!/bin/sh
# Temporary, bounded diagnostic hook. No persistent policy opt-in.
[ "$2" = suspend ] || exit 0
case "$1" in
 pre) exec /usr/bin/python3 /var/tmp/lmi-l3-suspend-candidate31.py pre --state /var/tmp/lmi-l3-policy-trial31.json --managed-unit lmi-l3-policy-trial31.service ;;
 post) exec /usr/bin/python3 /var/tmp/lmi-l3-suspend-candidate31.py post --state /var/tmp/lmi-l3-policy-trial31.json ;;
esac
