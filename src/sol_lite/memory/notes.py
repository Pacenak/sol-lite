"""Workspace notes stored under the application data directory."""
from __future__ import annotations

import re
from pathlib import Path

_SAFE = re.compile(r"[^A-Za-z0-9._-]")
_NOTES_CAP = 2000


def notes_file(memory_root, workspace_id: str) -> Path:
    safe = _SAFE.sub("_", str(workspace_id or "default")) or "default"
    return Path(memory_root) / safe / "notes.md"


def read_notes(memory_root, workspace_id: str, limit: int = _NOTES_CAP) -> str:
    if not memory_root:
        return ""
    path = notes_file(memory_root, workspace_id)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")[:limit]


def write_notes(memory_root, workspace_id: str, content: str) -> Path:
    path = notes_file(memory_root, workspace_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(content), encoding="utf-8")
    return path
