"""Per-agent tool allowlists declared beside each agent prompt."""
from __future__ import annotations

from pathlib import Path

import yaml

_CORE_FALLBACK = (
    "inventory_workspace",
    "list_workspace_directories",
    "list_project_structure",
    "execute_terminal_command",
)


def resolve_session_tools(root, agent_id, available) -> tuple[str, ...]:
    """Return the tools this agent may see, limited to tools that exist."""
    available_names = set(available or [])
    folder = str(agent_id).removeprefix("sol_")
    path = Path(root) / "src" / "sol_lite" / "agents" / folder / "tools.yaml"
    if not path.is_file():
        return tuple(name for name in _CORE_FALLBACK if name in available_names)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tools = data.get("tools") if isinstance(data, dict) else None
    if not isinstance(tools, list):
        return tuple(name for name in _CORE_FALLBACK if name in available_names)
    selected = []
    for name in tools:
        if isinstance(name, str) and name and name in available_names and name not in selected:
            selected.append(name)
    return tuple(selected)
