#!/bin/zsh
set -e
ROOT="${0:A:h:h:h}"
cd "$ROOT"
PY="$(command -v python3 || true)"
if [[ -z "$PY" ]]; then echo 'Python 3.11 or newer was not found.'; exit 1; fi
"$PY" install/common/install.py --repair
mkdir -p "$HOME/Applications"
rm -rf "$HOME/Applications/SOL-Lite.app"
cp -R launcher/macos/SOL-Lite.app "$HOME/Applications/SOL-Lite.app"
printf '%s\n' "$ROOT" > "$HOME/Applications/SOL-Lite.app/Contents/Resources/install-root.txt"
echo "SOL-Lite repaired and launcher refreshed."
