#!/bin/zsh
set -euo pipefail

ROOT="${0:A:h}"
OVERLAY="$ROOT/updated-files"

if [[ ! -d "$OVERLAY" ]]; then
    print -u2 \
        "Replacement overlay directory was not found: $OVERLAY"
    exit 1
fi

while IFS= read -r source; do
    relative="${source#$OVERLAY/}"
    destination="$ROOT/$relative"

    mkdir -p "${destination:h}"

    cp "$source" "$destination"

    print "UPDATED $relative"
done < <(
    find "$OVERLAY" \
        -type f \
        -print
)

chmod +x \
    "$ROOT/updated-files/scripts/setup.command" \
    "$ROOT/updated-files/install/macos/install.command" \
    "$ROOT/updated-files/launcher/macos/SOL-Lite.app/Contents/MacOS/SOL-Lite"

print ""
print "Overlay applied."