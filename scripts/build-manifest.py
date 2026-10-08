#!/usr/bin/env python3
"""Generate the deterministic SOL-Lite source-pack manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FORBIDDEN_PARTS = {
    ".git",
    ".hg",
    ".svn",
    ".pytest_cache",
    "__pycache__",
    ".ruff_cache",
    ".mypy_cache",
    ".tox",
    ".nox",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
}

FORBIDDEN_FILES = {
    ".env",
    ".DS_Store",
    "faults.json",
}

FORBIDDEN_PREFIXES = (
    "old-Script-version/",
    "data/state/",
    "src/sol_lite.egg-info/",
)


def is_forbidden(relative: Path) -> bool:
    """Return whether a relative path is outside the source-pack payload."""
    normalized = relative.as_posix()

    return (
        bool(set(relative.parts) & FORBIDDEN_PARTS)
        or relative.name in FORBIDDEN_FILES
        or any(
            normalized.startswith(prefix)
            for prefix in FORBIDDEN_PREFIXES
        )
    )


def payload_files(root: Path) -> list[Path]:
    """Return all files included in the deterministic source-pack payload."""
    return sorted(
        path.relative_to(root)
        for path in root.rglob("*")
        if (
            path.is_file()
            and not is_forbidden(path.relative_to(root))
        )
    )


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_project_version(root: Path) -> str:
    """Read the project version from pyproject.toml."""
    pyproject = root / "pyproject.toml"

    if not pyproject.is_file():
        raise FileNotFoundError(
            f"Required project file is missing: {pyproject}"
        )

    for line in pyproject.read_text(
        encoding="utf-8"
    ).splitlines():
        if line.startswith("version = "):
            parts = line.split('"')

            if len(parts) >= 2:
                return parts[1]

    raise ValueError(
        "Could not find a valid version = \"...\" entry in pyproject.toml."
    )


def main() -> int:
    """Generate BUILD_MANIFEST.json."""
    parser = argparse.ArgumentParser(
        description="Generate the deterministic SOL-Lite source-pack manifest."
    )

    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="SOL-Lite repository root.",
    )

    args = parser.parse_args()
    root = args.root.resolve()

    manifest_path = root / "BUILD_MANIFEST.json"

    entries = []

    for path in payload_files(root):
        if path.as_posix() == "BUILD_MANIFEST.json":
            continue

        entries.append(
            {
                "path": path.as_posix(),
                "sha256": sha256(root / path),
            }
        )

    version = read_project_version(root)

    manifest = {
        "format": 2,
        "project": "SOL-Lite",
        "version": version,
        "files": entries,
    }

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "Generated BUILD_MANIFEST.json "
        f"with {len(entries)} payload files."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
