"""Workspace filesystem tools."""

import fnmatch
import os
from collections import Counter
from pathlib import Path

from ..core.exceptions import PermissionDenied, ToolExecutionError
from ..permissions.scopes import READ, WRITE
from ..security.path_guard import resolve_workspace_path
from ..security.role_files import path_in_role
from ..studio.gate import snapshot_untracked
from .base import ToolDefinition

_OVERVIEW_CAP = 200
_MANIFEST_DEPTH = 3
_MANIFEST_NAMES = frozenset({
    "readme",
    "readme.md",
    "readme.txt",
    "readme.rst",
    "package.json",
    "pyproject.toml",
    "cargo.toml",
    "go.mod",
    "composer.json",
    "gemfile",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "cmakelists.txt",
    "makefile",
    "setup.py",
    "setup.cfg",
})
_MANIFEST_SUFFIXES = (".sln", ".csproj", ".fsproj")
_TRUNCATION_NOTE = (
    "File list omitted because count exceeds "
    f"{_OVERVIEW_CAP}. Use list_project_structure with a path, "
    "find_workspace_files, or read_workspace_file to inspect a part of the tree."
)


def _rel(path, root):
    return path.relative_to(root).as_posix()


def _is_manifest(rel):
    parts = rel.split("/")
    if len(parts) - 1 > _MANIFEST_DEPTH:
        return False
    name = parts[-1].casefold()
    return name in _MANIFEST_NAMES or name.endswith(_MANIFEST_SUFFIXES)


def inventory_workspace(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    ctx.permission_engine.check(READ)
    count = 0
    sample = []
    extensions = Counter()
    manifests = []
    top_level = []
    for current_root, dirs, names in os.walk(root, followlinks=False):
        current = Path(current_root)
        dirs[:] = sorted(d for d in dirs if not (current / d).is_symlink())
        file_names = []
        for name in sorted(names):
            path = current / name
            if path.is_symlink():
                continue
            rel = _rel(path, root)
            count += 1
            if len(sample) < _OVERVIEW_CAP:
                sample.append(rel)
            suffix = Path(name).suffix.lower() or "(none)"
            extensions[suffix] += 1
            if len(manifests) < 40 and _is_manifest(rel):
                manifests.append(rel)
            file_names.append(name)
        if current == root:
            top_level = sorted(dirs + file_names)
    truncated = count > _OVERVIEW_CAP
    result = {
        "root": str(root),
        "count": count,
        "top_level": top_level,
        "truncated": truncated,
        "extensions": dict(extensions.most_common(20)),
        "manifests": manifests,
    }
    if truncated:
        result["note"] = _TRUNCATION_NOTE
    else:
        result["files"] = sample
    ctx.audit.record("workspace.inventory", count=count, truncated=truncated)
    return result


def list_workspace_directories(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    target = resolve_workspace_path(args.get("path", "."), root, must_exist=True)
    ctx.permission_engine.check(READ)
    if not target.is_dir():
        raise NotADirectoryError(target)
    max_depth = max(1, min(int(args.get("max_depth", 2)), 8))
    levels = {depth: [] for depth in range(1, max_depth + 1)}
    for current_root, dirs, _names in os.walk(target, followlinks=False):
        current = Path(current_root)
        dirs[:] = sorted(name for name in dirs if not (current / name).is_symlink())
        depth_here = len(current.relative_to(target).parts)
        if depth_here >= max_depth:
            dirs[:] = []
            continue
        for name in dirs:
            levels[depth_here + 1].append(_rel(current / name, root))
    directories = []
    truncated = False
    for depth in range(1, max_depth + 1):
        rows = sorted(levels[depth])
        room = _OVERVIEW_CAP - len(directories)
        if room <= 0:
            truncated = True
            break
        if len(rows) > room:
            directories.extend(rows[:room])
            truncated = True
            break
        directories.extend(rows)
    ctx.audit.record("workspace.directories", count=len(directories), truncated=truncated)
    return {
        "root": str(root),
        "directories": directories,
        "count": len(directories),
        "truncated": truncated,
        "max_depth": max_depth,
    }

def list_project_structure(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    target = resolve_workspace_path(args.get("path", "."), root, must_exist=True)
    ctx.permission_engine.check(READ)
    if not target.is_dir():
        raise NotADirectoryError(target)
    max_depth = int(args.get("max_depth", 2))
    base = len(target.parts)
    output = []
    truncated = False
    for current_root, dirs, names in os.walk(target, followlinks=False):
        current = Path(current_root)
        depth = len(current.parts) - base
        if depth >= max_depth:
            dirs[:] = []
        dirs[:] = sorted(d for d in dirs if not (current / d).is_symlink())
        indent = "  " * depth
        lines = [f"{indent}{d}/" for d in dirs]
        lines.extend(f"{indent}{n}" for n in sorted(names))
        for line in lines:
            if len(output) >= _OVERVIEW_CAP:
                truncated = True
                break
            output.append(line)
        if truncated:
            break
    return {"path": _rel(target, root), "tree": output, "truncated": truncated}

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

def _approve_workspace_write(ctx, path, root, *, operation, arguments, plan, approval_id):
    """Role-path writes run when filesystem.write is enabled.

    Paths outside the agent role still need an exact approval (or stay blocked
    until the human says yes). Unbound tool contexts (no agent_id) keep the
    approval gate so ad-hoc callers are not wide open.
    """
    try:
        rel = _rel(path.resolve(), root.resolve())
    except ValueError:
        rel = str(path)
    agent_id = getattr(ctx, "agent_id", None)
    in_role = bool(agent_id) and path_in_role(agent_id, rel)
    if in_role:
        rule = ctx.permission_engine.policy.rule(*WRITE.split("."))
        if not rule.enabled:
            raise PermissionDenied(f"Permission scope disabled: {WRITE}")
        return
    ctx.permission_engine.check(
        WRITE,
        approval_id=approval_id,
        operation=operation,
        target=str(path),
        arguments=arguments,
        plan=plan,
        session_id=getattr(ctx, "session_id", None),
        agent_id=agent_id,
        allow_session=bool(agent_id) and path_in_role(agent_id, rel),
    )


def write_workspace_file(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    path = resolve_workspace_path(args["path"], root)
    content = str(args.get("content", ""))
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    _approve_workspace_write(
        ctx,
        path,
        root,
        operation="write_workspace_file",
        arguments={"path": str(path), "content": content},
        plan=plan,
        approval_id=approval_id,
    )
    snapshot = snapshot_untracked(ctx, path) if path.is_file() else None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    ctx.audit.record("workspace.write", path=str(path), bytes=len(content.encode("utf-8")))
    result = {"path": _rel(path, root), "bytes": len(content.encode("utf-8"))}
    if snapshot:
        result["snapshot"] = snapshot
    return result


def edit_workspace_file(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    path = resolve_workspace_path(args["path"], root, must_exist=True)
    if not path.is_file():
        raise IsADirectoryError(path)
    old = str(args.get("old_string", ""))
    new = str(args.get("new_string", ""))
    if not old:
        raise ToolExecutionError("edit_workspace_file: old_string is required")
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count == 0:
        raise ToolExecutionError("edit_workspace_file: old_string was not found")
    replace_all = bool(args.get("replace_all"))
    if count > 1 and not replace_all:
        raise ToolExecutionError(
            "edit_workspace_file: old_string matched more than once; pass replace_all or a longer snippet"
        )
    updated = text.replace(old, new) if replace_all else text.replace(old, new, 1)
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    _approve_workspace_write(
        ctx,
        path,
        root,
        operation="edit_workspace_file",
        arguments={"path": str(path), "old_string": old, "new_string": new},
        plan=plan,
        approval_id=approval_id,
    )
    snapshot = snapshot_untracked(ctx, path)
    path.write_text(updated, encoding="utf-8")
    ctx.audit.record("workspace.edit", path=str(path), replacements=count if replace_all else 1)
    result = {"path": _rel(path, root), "replacements": count if replace_all else 1}
    if snapshot:
        result["snapshot"] = snapshot
    return result

def filesystem_tools():
    return [
        ToolDefinition("inventory_workspace", "Summarize the approved workspace: file count, top-level names, and manifest paths. The full file list is included only for a small tree. Use this first when asked what a workspace or its files are.",
                        {"type": "object", "properties": {}}, inventory_workspace),
        ToolDefinition("list_workspace_directories", "List the approved workspace folders and their immediate subfolders, one level at a time. Does not walk into a folder before its siblings are listed. Pass path to open one folder, and max_depth to go deeper than 2.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"},
                            "max_depth": {"type": "integer", "minimum": 1, "maximum": 8},
                        }}, list_workspace_directories),
        ToolDefinition("list_project_structure", "Browse one folder in the approved workspace, up to 200 lines. path is relative to the workspace root; do not request paths outside it.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"},
                            "max_depth": {"type": "integer", "minimum": 0, "maximum": 20},
                        }}, list_project_structure),
        ToolDefinition("find_workspace_files", "Find files by glob-like pattern.",
                        {"type": "object", "properties": {
                            "pattern": {"type": "string"}}, "required": ["pattern"]},
                        find_workspace_files),
        ToolDefinition("read_workspace_file", "Read one UTF-8 file inside the approved workspace. path is relative to the workspace root.",
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
        ToolDefinition(
            "write_workspace_file",
            "Create or overwrite a workspace file when the user asks. "
            "Paths under this agent's role (docs/, plans/, notes/, src/, …) "
            "run without a human click. Paths outside the role need approval "
            "of that exact file. Use a short plan describing the change.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "plan": {"type": "string"},
                    "approval_id": {"type": "string"},
                },
                "required": ["path", "content"],
            },
            write_workspace_file,
        ),
        ToolDefinition(
            "edit_workspace_file",
            "Edit an existing workspace file by exact text replacement. "
            "Use write_workspace_file to create a file. Role paths run without "
            "a human click; outside-role paths need approval of that exact file.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_string": {"type": "string"},
                    "new_string": {"type": "string"},
                    "replace_all": {"type": "boolean"},
                    "plan": {"type": "string"},
                    "approval_id": {"type": "string"},
                },
                "required": ["path", "old_string", "new_string"],
            },
            edit_workspace_file,
        ),
    ]
