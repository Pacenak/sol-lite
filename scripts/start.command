#!/bin/zsh
set -e
ROOT="${0:A:h:h}"
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo 'SOL-Lite is not installed. Run ./scripts/setup.command first.'
  exit 1
fi
cd "$ROOT"
"$ROOT/.venv/bin/python" "$ROOT/scripts/preflight.py" || exit $?
exec "$ROOT/.venv/bin/python" -m sol_lite start "$@"
