#!/usr/bin/env bash
# Stop carry-mode Lite processes; remind to unmount before unplug.
set -euo pipefail
pkill -f 'sol_lite|sol-lite' 2>/dev/null || true
echo "Lite stop requested. Unmount the BRAIN volume before unplugging."
echo "Do not hot-unplug while models or git are writing to data/."
