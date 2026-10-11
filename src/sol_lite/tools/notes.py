"""Read and write SOL-Lite workspace notes outside the user project."""
from __future__ import annotations

from ..memory.notes import read_notes, write_notes
from .base import ToolDefinition


def _roots(ctx):
    memory_root = getattr(ctx, "memory_root", None)
    workspace_id = getattr(ctx, "workspace_id", None) or "default"
    if not memory_root:
        return None, workspace_id
    return memory_root, workspace_id


def workspace_notes_read(ctx, args):
    memory_root, workspace_id = _roots(ctx)
    if memory_root is None:
        return {
            "ok": False,
            "error": "Workspace notes storage is not configured.",
            "tool": "workspace_notes_read",
        }
    content = read_notes(memory_root, workspace_id)
    ctx.audit.record("workspace.notes.read", workspace_id=workspace_id, bytes=len(content))
    return {"content": content, "bytes": len(content.encode("utf-8"))}


def workspace_notes_write(ctx, args):
    memory_root, workspace_id = _roots(ctx)
    if memory_root is None:
        return {
            "ok": False,
            "error": "Workspace notes storage is not configured.",
            "tool": "workspace_notes_write",
        }
    content = str(args.get("content") or "")
    path = write_notes(memory_root, workspace_id, content)
    ctx.audit.record(
        "workspace.notes.write",
        workspace_id=workspace_id,
        bytes=len(content.encode("utf-8")),
    )
    return {
        "path": str(path),
        "bytes": len(content.encode("utf-8")),
    }


def notes_tools():
    return [
        ToolDefinition(
            "workspace_notes_read",
            "Read the notes SOL-Lite saved for this workspace. Notes are outside the user project.",
            {"type": "object", "properties": {}},
            workspace_notes_read,
        ),
        ToolDefinition(
            "workspace_notes_write",
            "Save notes about what this workspace is and how to edit it. Notes stay outside the user project.",
            {
                "type": "object",
                "properties": {"content": {"type": "string"}},
                "required": ["content"],
            },
            workspace_notes_write,
        ),
    ]
