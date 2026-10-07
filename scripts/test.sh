#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -x .venv/bin/python || { echo "Run ./scripts/install.sh first."; exit 1; }
.venv/bin/python -m pytest -q
