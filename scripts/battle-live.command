#!/bin/zsh
set -e
cd "$(dirname "$0")/.."
.venv/bin/python -m sol_lite battle-test --live --agent sol_engineer
