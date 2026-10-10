#!/bin/sh
# Temporary, bounded diagnostic hook. No persistent policy opt-in.
[ "$2" = suspend ] || exit 0
case "$1" in
 pre) exec /usr/bin/python3 /var/tmp/lmi-npu-suspend-lifecycle-candidate25.py pre --state /var/tmp/lmi-npu-bandwidth-trial25.json --managed-unit lmi-npu-bandwidth-trial25.service ;;
 post) exec /usr/bin/python3 /var/tmp/lmi-npu-suspend-lifecycle-candidate25.py post --state /var/tmp/lmi-npu-bandwidth-trial25.json ;;
esac
