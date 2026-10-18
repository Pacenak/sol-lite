#!/usr/bin/env python3
"""Validate SOL-Lite source-pack invariants."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

VERSION_RE = re.compile(
    r'^version = "([^"]+)"$',
    re.MULTILINE,
)

FORBIDDEN_PARTS = {
    ".work",
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

# Local runtime output. These directories are gitignored and must not
# enter the source pack, or a voice cache or log fails every battle test.
FORBIDDEN_PREFIXES = (
    "portable-stick/brain/workspace/",
    "old-Script-version/",
    "src/sol_lite.egg-info/",
    "workspace/",
    "logs/",
    "data/state/",
    "data/logs/",
    "data/audit/",
    "data/faults/",
    "data/tasks/",
    "data/tts/",
    "data/memory/",
    "data/rag/",
    "data/indexes/",
    "skills/installed/",
    "skills/pending/",
    "skills/quarantine/",
)


def is_forbidden(relative: Path) -> bool:
    normalized = relative.as_posix()

    return (
        bool(set(relative.parts) & FORBIDDEN_PARTS)
        or relative.name in FORBIDDEN_FILES
        or any(normalized.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
    )


def payload_files(root: Path) -> list[Path]:
    files = []
    for current, directories, names in os.walk(root, followlinks=False):
        folder = Path(current)
        directories[:] = [
            name
            for name in directories
            if not (folder / name).is_symlink()
            and not is_forbidden((folder / name).relative_to(root) / "_")
        ]
        for name in names:
            path = folder / name
            relative = path.relative_to(root)
            if path.is_file() and not path.is_symlink() and not is_forbidden(relative):
                files.append(relative)
    return sorted(files)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )

    args = parser.parse_args()
    root = args.root.resolve()

    errors = []

    manifest_path = root / "BUILD_MANIFEST.json"

    if not manifest_path.is_file():
        errors.append("BUILD_MANIFEST.json is missing.")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            listed = {
                entry["path"]
                for entry in manifest.get(
                    "files",
                    [],
                )
            }

            actual = {
                path.as_posix()
                for path in payload_files(root)
                if path.as_posix() != "BUILD_MANIFEST.json"
            }

            if listed != actual:
                if actual - listed:
                    errors.append("Manifest missing files: " + ", ".join(sorted(actual - listed)))

                if listed - actual:
                    errors.append(
                        "Manifest contains absent files: " + ", ".join(sorted(listed - actual))
                    )

            for entry in manifest.get(
                "files",
                [],
            ):
                path = root / entry["path"]

                if path.is_file():
                    try:
                        if sha256(path) != entry["sha256"]:
                            errors.append(f"Manifest hash mismatch: {entry['path']}")
                    except OSError as exc:
                        errors.append(f"Cannot read source file {entry['path']}: {exc}")

        except (
            OSError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
        ):
            errors.append("BUILD_MANIFEST.json is invalid.")

    pyproject = root / "pyproject.toml"

    if pyproject.is_file():
        match = VERSION_RE.search(pyproject.read_text(encoding="utf-8"))

        if match:
            version = match.group(1)

            version_file = root / "src/sol_lite/version.py"

            config = root / "config/sol-lite.yaml"

            readme = root / "README.md"

            if version_file.is_file() and (
                f'__version__ = "{version}"' not in version_file.read_text(encoding="utf-8")
            ):
                errors.append("src/sol_lite/version.py does not match pyproject.toml.")

            if config.is_file() and (
                f'version: "{version}"' not in config.read_text(encoding="utf-8")
            ):
                errors.append("config/sol-lite.yaml does not match pyproject.toml.")

            if readme.is_file() and not readme.read_text(encoding="utf-8").startswith(
                f"# SOL-Lite v{version}"
            ):
                errors.append("README.md version heading does not match pyproject.toml.")

    if errors:
        for error in errors:
            print(f"AUDIT ERROR: {error}")

        return 1

    print("SOL-Lite pack audit: PASS")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
