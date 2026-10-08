#!/bin/zsh
set -u

ROOT="${0:A:h:h}"
INSTALLER="$ROOT/install/macos/install.command"

if [[ ! -f "$INSTALLER" ]]; then
    print -u2 "SOL-Lite installer not found: $INSTALLER"
    print -u2 "Run this from a complete SOL-Lite source tree."
    read "?Press Return to close..."
    exit 1
fi

"$INSTALLER"
status=$?

if (( status != 0 )); then
    print -u2 ""
    print -u2 "SOL-Lite setup failed with exit code $status."
    read "?Press Return to close..."
    exit "$status"
fi

print ""
print "SOL-Lite setup completed."
print "Launcher: ~/Applications/SOL-Lite.app"
read "?Press Return to close..."