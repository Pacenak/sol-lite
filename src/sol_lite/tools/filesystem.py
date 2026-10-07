"""Workspace filesystem tools."""

import fnmatch
import os
from pathlib import Path

from ..permissions.scopes import READ, WRITE
from ..security.path_guard import resolve_workspace_path
from .base import ToolDefinition


def _rel(path, root):
    return path.relative_to(root).as_posix()

def inventory_workspace(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    ctx.permission_engine.check(READ)
    files = []
    for current_root, dirs, names in os.walk(root, followlinks=False):
        current = Path(current_root)
        dirs[:] = sorted(d for d in dirs if not (current / d).is_symlink())
        for name in sorted(names):
            path = current / name
            if not path.is_symlink():
                files.append(_rel(path, root))
    ctx.audit.record("workspace.inventory", count=len(files))
    return {"root": str(root), "files": files, "count": len(files)}

def list_project_structure(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    target = resolve_workspace_path(args.get("path", "."), root, must_exist=True)
    ctx.permission_engine.check(READ)
    if not target.is_dir():
        raise NotADirectoryError(target)
    max_depth = int(args.get("max_depth", 4))
    base = len(target.parts)
    output = []
    for current_root, dirs, names in os.walk(target, followlinks=False):
        current = Path(current_root)
        depth = len(current.parts) - base
        if depth >= max_depth:
            dirs[:] = []
        dirs[:] = sorted(d for d in dirs if not (current / d).is_symlink())
        indent = "  " * depth
        output.extend(f"{indent}{d}/" for d in dirs)
        output.extend(f"{indent}{n}" for n in sorted(names))
    return {"path": _rel(target, root), "tree": output}

def find_workspace_files(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    pattern = str(args["pattern"])
    ctx.permission_engine.check(READ)
    matches = []
    for current_root, dirs, names in os.walk(root, followlinks=False):
        current = Path(current_root)
        dirs[:] = sorted(d for d in dirs if not (current / d).is_symlink())
        for name in sorted(names):
            rel = _rel(current / name, root)
            if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(name, pattern):
                matches.append(rel)
    return {"pattern": pattern, "files": matches, "count": len(matches)}

def read_workspace_file(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    path = resolve_workspace_path(args["path"], root, must_exist=True)
    ctx.permission_engine.check(READ)
    if not path.is_file():
        raise IsADirectoryError(path)
    text = path.read_text(encoding="utf-8")
    return {"path": _rel(path, root), "content": text, "bytes": path.stat().st_size}

def read_workspace_files(ctx, args):
    return {"files": [read_workspace_file(ctx, {"path": p}) for p in args["paths"]]}

def get_workspace_file_metadata(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    path = resolve_workspace_path(args["path"], root, must_exist=True)
    ctx.permission_engine.check(READ)
    stat = path.stat()
    return {"path": _rel(path, root), "size": stat.st_size, "is_file": path.is_file(),
            "is_dir": path.is_dir(), "modified_ns": stat.st_mtime_ns}

def write_workspace_file(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    path = resolve_workspace_path(args["path"], root)
    content = str(args.get("content", ""))
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    ctx.permission_engine.check(
        WRITE,
        approval_id=approval_id,
        operation="write_workspace_file",
        target=str(path),
        arguments={"path": str(path), "content": content},
        plan=plan,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    ctx.audit.record("workspace.write", path=str(path), bytes=len(content.encode("utf-8")))
    return {"path": _rel(path, root), "bytes": len(content.encode("utf-8"))}

def filesystem_tools():
    return [
        ToolDefinition("inventory_workspace", "Recursively inventory approved workspace.",
                        {"type": "object", "properties": {}}, inventory_workspace),
        ToolDefinition("list_project_structure", "List a bounded workspace tree.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"},
                            "max_depth": {"type": "integer", "minimum": 0, "maximum": 20},
                        }}, list_project_structure),
        ToolDefinition("find_workspace_files", "Find files by glob-like pattern.",
                        {"type": "object", "properties": {
                            "pattern": {"type": "string"}}, "required": ["pattern"]},
                        find_workspace_files),
        ToolDefinition("read_workspace_file", "Read one UTF-8 workspace file.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}}, "required": ["path"]},
                        read_workspace_file),
        ToolDefinition("read_workspace_files", "Read multiple UTF-8 workspace files.",
                        {"type": "object", "properties": {
                            "paths": {"type": "array", "items": {"type": "string"}}},
                         "required": ["paths"]}, read_workspace_files),
        ToolDefinition("get_workspace_file_metadata", "Get workspace path metadata.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}}, "required": ["path"]},
                        get_workspace_file_metadata),
        ToolDefinition("write_workspace_file", "Write a file after exact human approval.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                            "plan": {"type": "string"},
                            "approval_id": {"type": "string"}},
                         "required": ["path", "content", "plan", "approval_id"]},
                        write_workspace_file),
    ]
