# Upgrading

1. Replace/update the SOL-Lite source tree using your normal source-control workflow.
2. Run the platform repair command once.
3. Run the battle test.
4. Start normally.

Windows:

```powershell
.\install\windows\repair.ps1
.\scripts\battle-test.bat
.\launcher\windows\SOL-Lite.cmd
```

macOS:

```bash
./install/macos/repair.command
./scripts/battle-test.command
open "$HOME/Applications/SOL-Lite.app"
```

Do not delete `.venv` unless intentionally performing a development reset.
