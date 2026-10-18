"""Backward-compatible notes names backed by the shared workspace pack."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..memory.notes import notes_file
from ..security.path_guard import resolve_workspace_path
from ..workspace_pack.pack import stamp
from .base import ToolDefinition
from .workspace_pack import mutate, pack_for


def _migrate(pack, ctx):
    memory_root = getattr(ctx, "memory_root", None)
    if not memory_root:
        message = "Legacy notes location unavailable; migration skipped"
        if message not in pack.read("_workspace/CHANGELOG.md"):
            pack.change(message, ["_workspace/CONVERSATIONS.md"])
        return
    path = notes_file(Path(memory_root).resolve(), getattr(ctx, "workspace_id", None) or "default")
    path = resolve_workspace_path(path, memory_root)
    if not path.is_file():
        return
    try:
        content = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as exc:
        pack.errors.append({"path": str(path), "reason": str(exc)})
        return
    marker = "<!-- legacy-notes:" + hashlib.sha256(str(path).encode()).hexdigest() + " -->"
    name = "_workspace/CONVERSATIONS.md"
    if marker in pack.read(name):
        return
    lines = ["> " + line for line in content.splitlines()]
    lines.insert(0, marker)
    for offset in range(0, len(lines), 5):
        pack.append_file(
            name,
            f"\n## {stamp()} | {pack.agent} | migrated\n"
            + "\n".join(lines[offset : offset + 5])
            + "\n",
        )


def workspace_notes_read(ctx, args):
    pack = pack_for(ctx, "workspace_notes_read")
    content = "\n\n".join(
        pack.read("_workspace/" + name) for name in ("README.md", "CONVERSATIONS.md")
    )
    ctx.audit.record("workspace.notes.read", bytes=len(content.encode("utf-8")))
    return {"content": content, "bytes": len(content.encode("utf-8"))}


def workspace_notes_write(ctx, args):
    content = args.get("content")
    if not isinstance(content, str) or not content.strip() or "\x00" in content:
        raise ValueError("content must be non-empty text")
    if len(content) > 64000:
        raise ValueError("Notes exceed 64,000 characters")

    def build(pack):
        pack.minimal()
        _migrate(pack, ctx)
        name = "_workspace/README.md"
        current = pack.read(name)
        heading = "## What this is and how to edit it"
        if current.splitlines().count(heading) != 1:
            raise ValueError("README notes section is missing or ambiguous; file left unchanged")
        quoted = "\n".join("> " + line for line in content.splitlines())
        position = current.index(heading) + len(heading)
        pack.put(name, current[:position] + "\n\n" + quoted + "\n" + current[position:])
        lines = quoted.splitlines()
        for offset in range(0, len(lines), 5):
            pack.append_file(
                "_workspace/CONVERSATIONS.md",
                f"\n## {stamp()} | {pack.agent} | tip\n"
                + "\n".join(lines[offset : offset + 5])
                + "\n",
            )
        return {"path": name, "bytes": len(content.encode("utf-8"))}

    return mutate(ctx, args, "workspace_notes_write", build)


def notes_tools():
    return [
        ToolDefinition(
            "workspace_notes_read",
            "Read the shared workspace pack notes.",
            {"type": "object", "properties": {}},
            workspace_notes_read,
            permissions=("filesystem.read",),
            risk=("READ_ONLY",),
        ),
        ToolDefinition(
            "workspace_notes_write",
            "Save workspace description and editing notes in the pack README and shared tips, "
            "after approval. Creates a minimal pack when missing.",
            {
                "type": "object",
                "properties": {"content": {"type": "string"}},
                "required": ["content"],
            },
            workspace_notes_write,
            permissions=("filesystem.read", "filesystem.write"),
            risk=("MUTATING",),
            mutability=True,
        ),
    ]
