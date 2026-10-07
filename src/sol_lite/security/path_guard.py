"""Filesystem containment."""

import os
from pathlib import Path

from ..core.exceptions import SecurityError


def is_within_directory(path, base_directory) -> bool:
    target = os.path.realpath(os.path.abspath(os.fspath(path)))
    base = os.path.realpath(os.path.abspath(os.fspath(base_directory)))
    try:
        return os.path.commonpath([target, base]) == base
    except ValueError:
        return False

def resolve_workspace_path(path, workspace_root, *, must_exist=False) -> Path:
    workspace = Path(workspace_root).resolve()
    raw = Path(path)
    candidate = raw if raw.is_absolute() else workspace / raw
    resolved = Path(os.path.realpath(os.path.abspath(os.fspath(candidate))))
    if not is_within_directory(resolved, workspace):
        raise SecurityError(f"Workspace path escapes workspace root: {path}")
    if must_exist and not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved
