#!/usr/bin/env python3
"""Deterministic SOL-Lite installation/runtime preflight.

This checks contracts that must hold before the interactive shell is started.
It intentionally performs no network calls and makes no configuration changes.
"""
from __future__ import annotations

import importlib.metadata
import re
import sys
from io import StringIO
from pathlib import Path


def fail(message: str) -> None:
    print(f"PREFLIGHT FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    if sys.version_info < (3, 11):
        fail(f"Python 3.11 or newer is required; found {sys.version.split()[0]}")

    version_text = (root / "src" / "sol_lite" / "version.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', version_text)
    if not match:
        fail("src/sol_lite/version.py does not define __version__")
    version = match.group(1)

    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    config = (root / "config" / "sol-lite.yaml").read_text(encoding="utf-8")
    if f'version = "{version}"' not in pyproject:
        fail(f"pyproject.toml version does not match {version}")
    if f'version: "{version}"' not in config:
        fail(f"config/sol-lite.yaml version does not match {version}")

    terminal_ui = root / "src" / "sol_lite" / "terminal_ui.py"
    if "title_style=" in terminal_ui.read_text(encoding="utf-8"):
        fail("unsupported Rich Panel(title_style=...) API remains in terminal_ui.py")

    try:
        rich_version = importlib.metadata.version("rich")
    except importlib.metadata.PackageNotFoundError:
        fail("Rich is not installed in the active Python environment")

    from rich.console import Console
    from sol_lite.terminal_ui import TerminalUI

    console = Console(file=StringIO(), highlight=False)
    ui = TerminalUI(console=console)
    ui.user("preflight")
    ui.agent("preflight")
    ui.final_failure("preflight")

    skill_count = len(list((root / "skills").glob("*/SKILL.md")))
    if skill_count != 34:
        fail(f"expected 34 built-in skills, found {skill_count}")

    print(f"SOL-Lite preflight: PASS (version={version}, Rich={rich_version}, skills={skill_count})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
