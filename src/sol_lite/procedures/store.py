"""Checklist progress lives under the SOL-Lite state directory, not the workspace."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def store_path(state_root, workspace_root) -> Path:
    digest = hashlib.sha256(str(Path(workspace_root).resolve()).encode("utf-8")).hexdigest()
    return Path(state_root) / "procedures" / f"{digest}.json"


def read_store(state_root, workspace_root) -> dict | None:
    if not state_root:
        return None
    path = store_path(state_root, workspace_root)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"corrupt": True}
    if not isinstance(payload, dict):
        return {"corrupt": True}
    return payload


def write_store(state_root, workspace_root, payload: dict) -> None:
    if not state_root:
        return
    path = store_path(state_root, workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
