#!/bin/bash
set -euo pipefail
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec /usr/bin/python3 "$script_dir/acquire-m0-closure.py" "$@"
