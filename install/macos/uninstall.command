#!/bin/zsh
set -e
ROOT="${0:A:h:h:h}"
read -r "answer?Remove SOL-Lite runtime (.venv and data/state) from $ROOT? [y/N] "
if [[ "$answer" != "y" && "$answer" != "Y" ]]; then exit 0; fi
rm -rf "$ROOT/.venv"
rm -f "$ROOT/data/state/install.json"
rm -rf "$HOME/Applications/SOL-Lite.app"
echo 'SOL-Lite runtime installation removed. Source, configuration, skills and workspaces were retained.'
