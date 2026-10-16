"""Admin-only studio unlock for portable admin / sec tools.

``sol_studio_admin`` is an **admin-only feature**. It activates only when:

1. Admin feature is on: ``SOL_STUDIO_ADMIN_FEATURE=1`` or ``features.studio_admin`` in config, and
2. ``SOL_STUDIO_OWNER=1`` (or true/yes/on), and
3. Unlock file under data state **or** BRAIN ``sec/I_OWN_THIS_LAB`` contains ``I OWN THIS LAB``, and
4. Optional ``SOL_STUDIO_OWNER_ID`` matches ``owner_id:`` in that file (binds stick to you).

Normal PA/engineer sessions never see the agent without both the feature flag and unlock.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

_OWNER_ID_RE = re.compile(r"(?im)^\s*owner_id\s*:\s*(\S+)\s*$")


def _truthy(raw: str | None) -> bool:
    return str(raw or "").strip().lower() in {"1", "true", "yes", "on"}


def admin_feature_enabled(application_config: dict[str, Any] | None = None) -> bool:
    """True when admin-only studio tools may be offered (still need owner unlock)."""
    if _truthy(os.environ.get("SOL_STUDIO_ADMIN_FEATURE")):
        return True
    app = application_config or {}
    features = app.get("features") if isinstance(app, dict) else None
    if isinstance(features, dict) and features.get("studio_admin"):
        return True
    # Nested under application.application in some merges
    inner = app.get("application") if isinstance(app, dict) else None
    if isinstance(inner, dict):
        feats = inner.get("features")
        if isinstance(feats, dict) and feats.get("studio_admin"):
            return True
    return False


def find_unlock_file(data_root: Path | None, workspace_root: Path | None) -> Optional[Path]:
    candidates: list[Path] = []
    if data_root:
        candidates.append(Path(data_root) / "state" / "studio_owner.unlock")
    if workspace_root:
        ws = Path(workspace_root)
        candidates.append(ws.parent / "sec" / "I_OWN_THIS_LAB")
        candidates.append(ws / "sec" / "I_OWN_THIS_LAB")
    for path in candidates:
        if path.is_file():
            return path
    return None


def parse_owner_id(text: str) -> str:
    match = _OWNER_ID_RE.search(text or "")
    return (match.group(1) if match else "").strip()


def studio_owner_unlocked(
    *,
    data_root: Path | str | None = None,
    workspace_root: Path | str | None = None,
) -> bool:
    if not _truthy(os.environ.get("SOL_STUDIO_OWNER")):
        return False
    unlock = find_unlock_file(
        Path(data_root) if data_root else None,
        Path(workspace_root) if workspace_root else None,
    )
    if unlock is None:
        return False
    try:
        text = unlock.read_text(encoding="utf-8")
    except OSError:
        return False
    upper = text.upper()
    if "I OWN THIS LAB" not in upper and "I_OWN_THIS_LAB" not in upper:
        return False
    expected = (os.environ.get("SOL_STUDIO_OWNER_ID") or "").strip()
    if expected:
        file_id = parse_owner_id(text)
        if file_id.casefold() != expected.casefold():
            return False
    return True


def admin_unlocked(
    *,
    data_root: Path | str | None = None,
    workspace_root: Path | str | None = None,
    application_config: dict[str, Any] | None = None,
) -> bool:
    """Admin-only feature + personal unlock both required."""
    if not admin_feature_enabled(application_config):
        return False
    return studio_owner_unlocked(data_root=data_root, workspace_root=workspace_root)


def require_studio_owner(
    *,
    data_root: Path | str | None = None,
    workspace_root: Path | str | None = None,
    application_config: dict[str, Any] | None = None,
) -> None:
    if not admin_unlocked(
        data_root=data_root,
        workspace_root=workspace_root,
        application_config=application_config,
    ):
        raise PermissionError(
            "Admin-only feature locked: enable SOL_STUDIO_ADMIN_FEATURE=1 (or "
            "features.studio_admin), set SOL_STUDIO_OWNER=1, and create "
            "data/state/studio_owner.unlock or BRAIN sec/I_OWN_THIS_LAB with "
            "'I OWN THIS LAB' (match SOL_STUDIO_OWNER_ID to owner_id: if set)."
        )
