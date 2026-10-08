#!/bin/zsh
set -u

ROOT="${0:A:h:h:h}"

cd "$ROOT" || exit 1

PY="$(command -v python3 || true)"

if [[ -z "$PY" ]]; then
    print -u2 "Python 3.11 or newer was not found."
    exit 1
fi

PY_OK="$(
    "$PY" -c \
    'import sys; print(int(sys.version_info >= (3, 11)))'
)"

if [[ "$PY_OK" != "1" ]]; then
    print -u2 "Python 3.11 or newer is required."
    exit 1
fi

"$PY" install/common/install.py

status=$?

if (( status != 0 )); then
    print -u2 \
        "SOL-Lite installation failed with exit code $status."
    exit "$status"
fi

mkdir -p "$HOME/Applications"

rm -rf \
    "$HOME/Applications/SOL-Lite.app"

cp -R \
    launcher/macos/SOL-Lite.app \
    "$HOME/Applications/SOL-Lite.app"

chmod +x \
    "$HOME/Applications/SOL-Lite.app/Contents/MacOS/SOL-Lite"

mkdir -p \
    "$HOME/Applications/SOL-Lite.app/Contents/Resources"

printf '%s\n' "$ROOT" > \
    "$HOME/Applications/SOL-Lite.app/Contents/Resources/install-root.txt"

print \
    "SOL-Lite installed to $HOME/Applications/SOL-Lite.app"