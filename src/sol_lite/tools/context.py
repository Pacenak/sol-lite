"""Read-only runtime context tool."""
from __future__ import annotations

import platform
from pathlib import Path

from ..permissions.scopes import READ
from .base import ToolDefinition


def runtime_get_context(ctx, args):
    ctx.permission_engine.check(READ)
    workspace = Path(ctx.workspace_root).resolve()
    project = Path(ctx.project_root).resolve() if ctx.project_root else workspace
    if project == workspace and not (project / ".git").exists():
        for parent in (project, *project.parents):
            if (parent / ".git").exists():
                project = parent
                break
    return {
        "session_id": ctx.session_id,
        "platform": platform.system().lower(),
        "process_working_directory": str(Path.cwd().resolve()),
        "approved_workspace": str(workspace),
        "project_root": str(project),
        "workspace_exists": workspace.is_dir(),
        "available_shells": ctx.platform.available_shells(),
    }


def runtime_tools():
    return [ToolDefinition(
        "runtime_get_context",
        "Read the authoritative current SOL-Lite session, approved workspace, project root, process working directory, platform, and available shells.",
        {"type": "object", "properties": {}},
        runtime_get_context,
    )]
