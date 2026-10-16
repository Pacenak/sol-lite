#!/usr/bin/env bash
# Carry-mode: run SOL-Lite with data/workspace on this BRAIN stick.
set -euo pipefail
LAUNCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRAIN_ROOT="$(cd "$LAUNCH_DIR/.." && pwd)"

while IFS= read -r line; do
  case "$line" in
    *=*) export "$line" ;;
  esac
done < <(python3 "$LAUNCH_DIR/resolve_stick_root.py")

echo "SOL_DATA_ROOT=$SOL_DATA_ROOT"
echo "SOL_WORKSPACE_ROOT=$SOL_WORKSPACE_ROOT"

REPO_ROOT="${1:-${SOL_LITE_REPO:-}}"
if [[ -z "$REPO_ROOT" && -f "$BRAIN_ROOT/sol-lite-src/pyproject.toml" ]]; then
  REPO_ROOT="$BRAIN_ROOT/sol-lite-src"
fi

if [[ -n "$REPO_ROOT" ]]; then
  echo "SOL_LITE_REPO=$REPO_ROOT"
  cd "$REPO_ROOT"
  if [[ -x .venv/bin/sol-lite ]]; then
    exec .venv/bin/sol-lite start --workspace "$SOL_WORKSPACE_ROOT"
  elif [[ -x .venv/bin/python ]]; then
    exec .venv/bin/python -m sol_lite start --workspace "$SOL_WORKSPACE_ROOT"
  else
    exec python3 -m sol_lite start --workspace "$SOL_WORKSPACE_ROOT"
  fi
fi

echo "Set SOL_LITE_REPO to your PLG_Ai_Lite clone on SOLLITE (or legacy brain/sol-lite-src)"
echo "Env is set — run: sol-lite start --workspace \"\$SOL_WORKSPACE_ROOT\""
