"""Role file roots for SOL-Lite agents.

Writes under these roots run when filesystem.write is enabled (no human click).
A path outside the role still needs an exact approval for that file.
"""
from __future__ import annotations

ROLE_WRITE_PREFIXES = {
    "sol_pa": (
        "docs/", "notes/", "plans/", "inbox/", "coordination/", "network/", "configs/", "config/", "scripts/",
    ),
    "sol_business": (
        "docs/", "reports/", "plans/", "business/", "notes/", "configs/",
    ),
    "sol_docs": (
        "docs/", "notes/", "plans/", "presentations/", "spreadsheets/", "diagrams/", "content/", "configs/",
    ),
    "sol_engineer": (
        "src/", "tests/", "scripts/", "config/", "configs/", "docs/", "plans/", "notes/",
        "infrastructure/", "network/", "deploy/",
    ),
}


def path_in_role(agent_id: str | None, relative_path: str) -> bool:
    """True when this agent may write the workspace-relative path.

    Missing agent id means the caller did not bind a role, so the workspace
    approval gate remains the only check.
    """
    agent = str(agent_id or "").strip()
    if not agent:
        return True
    prefixes = ROLE_WRITE_PREFIXES.get(agent)
    if not prefixes:
        return True
    rel = str(relative_path or "").replace("\\", "/").lstrip("./")
    if not rel or rel.startswith("../"):
        return False
    return any(rel == prefix.rstrip("/") or rel.startswith(prefix) for prefix in prefixes)
