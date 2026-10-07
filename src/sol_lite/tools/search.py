"""Search and structural drift tools."""

import os
from pathlib import Path

from ..permissions.scopes import READ
from ..security.path_guard import resolve_workspace_path
from .base import ToolDefinition


def search_codebase(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    target = resolve_workspace_path(args.get("path", "."), root, must_exist=True)
    query = str(args["query"])
    limit = int(args.get("max_results", 100))
    ctx.permission_engine.check(READ)
    candidates = [target] if target.is_file() else []
    if target.is_dir():
        for current_root, dirs, names in os.walk(target, followlinks=False):
            current = Path(current_root)
            dirs[:] = sorted(d for d in dirs if not (current / d).is_symlink())
            candidates.extend(current / n for n in sorted(names))
    results = []
    for path in candidates:
        if len(results) >= limit:
            break
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if query.casefold() in line.casefold():
                results.append({"path": path.relative_to(root).as_posix(),
                                "line": number, "text": line})
                if len(results) >= limit:
                    break
    return {"query": query, "results": results, "count": len(results)}

def analyze_architecture_drift(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    ctx.permission_engine.check(READ)
    checks = []
    for item in ["README.md", "pyproject.toml", "package.json", "requirements.txt", "src", "tests"]:
        path = root / item
        checks.append({"path": item, "exists": path.exists(),
                        "type": "directory" if path.is_dir() else "file" if path.is_file() else "missing"})
    return {"status": "baseline", "checks": checks,
            "note": "Structural checks only; semantic claims require workspace evidence."}

def search_tools():
    return [
        ToolDefinition("search_codebase", "Search UTF-8 text in workspace.",
                        {"type": "object", "properties": {
                            "query": {"type": "string"}, "path": {"type": "string"},
                            "max_results": {"type": "integer", "minimum": 1, "maximum": 1000}},
                         "required": ["query"]}, search_codebase),
        ToolDefinition("analyze_architecture_drift",
                        "Perform conservative structural architecture checks.",
                        {"type": "object", "properties": {}}, analyze_architecture_drift),
    ]
