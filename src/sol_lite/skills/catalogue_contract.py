"""SOL shared skill release contract, v1. Standard library only.

Canonical copy: SOL-Lite. Exported byte-for-byte to SOL-Full by
scripts/build-skill-catalogue.py. No network or execution during loading.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath

SCHEMA_VERSION = 1
MAX_RESOURCE_BYTES = 64 * 1024
MAX_BODY_CHARS = 16000
MAX_SELECTED = 4
SAFE_NAME = re.compile(r"sol-[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
COMMIT = re.compile(r"[a-f0-9]{40}\Z")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_digest(value) -> str:
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def safe_path(root: Path, relative: str) -> Path:
    """Reject absolute paths, traversal, Windows drive/ADS paths and symlinks."""
    if not isinstance(relative, str) or "\\" in relative or ":" in relative:
        raise ValueError("Invalid package path")
    parts = PurePosixPath(relative)
    if not relative or parts.is_absolute() or any(p in {".", ".."} for p in relative.split("/")):
        raise ValueError("Invalid package path")
    root = Path(root).resolve()
    target = root
    for part in parts.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError("Symlinks are not package resources")
    if not target.resolve().is_relative_to(root):
        raise ValueError("Package path escapes its root")
    return target


def file_hashes(root: Path) -> dict[str, str]:
    if root.is_symlink():
        raise ValueError("Symlink package root")
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlink in package")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = digest(path.read_bytes())
    return result


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".catalogue-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Catalogue:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.data = json.loads((self.root / "catalogue.json").read_text(encoding="utf-8"))
        if self.data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Unsupported skill catalogue schema")
        unsigned = {k: v for k, v in self.data.items() if k != "release_sha256"}
        if self.data.get("release_sha256") != json_digest(unsigned):
            raise ValueError("Catalogue release hash mismatch")
        for relative, expected in self.data.get("evidence_files", {}).items():
            if digest(safe_path(self.root, relative).read_bytes()) != expected:
                raise ValueError("Licence or evidence content hash mismatch")
        self.entries = {}
        sources = {source["repository"]: source for source in self.data["sources"]}
        if len(sources) != len(self.data["sources"]):
            raise ValueError("Duplicate catalogue source")
        for entry in self.data["skills"]:
            name = entry["name"]
            if not SAFE_NAME.fullmatch(name) or entry["id"] != "sol/" + name.removeprefix("sol-"):
                raise ValueError("Invalid namespaced skill ID")
            if name in self.entries:
                raise ValueError("Duplicate catalogue skill")
            if not entry.get("license") or not entry.get("description") or not entry.get("sectors"):
                raise ValueError("Missing package metadata")
            if entry.get("default") and entry["pack"] != "engineering":
                raise ValueError("Only the engineering baseline is active by default")
            if not set(entry["runtimes"]) <= {"lite", "full"}:
                raise ValueError("Unsupported package runtime")
            for upstream in entry["upstream"]:
                if upstream["repository"] not in sources or not COMMIT.fullmatch(upstream["commit"]):
                    raise ValueError("Unpinned upstream source")
                if not SHA256.fullmatch(upstream["sha256"]):
                    raise ValueError("Invalid upstream evidence hash")
                evidence = safe_path(self.root, upstream["evidence"])
                if digest(evidence.read_bytes()) != upstream["sha256"]:
                    raise ValueError("Upstream evidence hash mismatch")
            self.verify(entry)
            self.entries[name] = entry

    def package(self, entry) -> Path:
        return safe_path(self.root, "packages/" + entry["name"])

    def verify(self, entry) -> None:
        files = entry["files"]
        if "SKILL.md" not in files or any(not SHA256.fullmatch(h) for h in files.values()):
            raise ValueError("Invalid package file manifest")
        for relative in files:
            safe_path(self.package(entry), relative)
        if file_hashes(self.package(entry)) != files:
            raise ValueError("Package content hash mismatch: " + entry["name"])
        if json_digest(files) != entry["sha256"]:
            raise ValueError("Package tree hash mismatch")

    def resource(self, name: str, relative="SKILL.md") -> str:
        entry = self.entries[name]
        self.verify(entry)
        if relative not in entry["files"]:
            raise FileNotFoundError("Resource is not in the reviewed package")
        path = safe_path(self.package(entry), relative)
        if path.stat().st_size > MAX_RESOURCE_BYTES:
            raise ValueError("Resource exceeds context read limit")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def availability(entry, *, tools=None, check_dependencies=True):
        missing = []
        if tools is not None:
            # Capabilities are adapter-neutral; adapters supply the capabilities
            # actually present in their native tool registry.
            missing += ["tool:" + name for name in entry["requires_tools"] if name not in tools]
        if check_dependencies:
            for module in entry["requires_python"]:
                try:
                    present = importlib.util.find_spec(module) is not None
                except (ImportError, ValueError, ModuleNotFoundError):
                    present = False
                if not present:
                    missing.append("python:" + module)
            missing += ["command:" + cmd for cmd in entry["requires_commands"] if not shutil.which(cmd)]
        return {"available": not missing and tools is not None, "missing": missing,
                "tools_checked": tools is not None, "permissions_verified": False,
                "execution_verified": False}

    def select(self, task: str, *, runtime: str, names=None, sector=None):
        explicit, automatic = [], []
        allowed = set(self.entries if names is None else names)
        for entry in self.entries.values():
            if entry["name"] not in allowed or runtime not in entry["runtimes"]:
                continue
            if sector is not None and sector not in entry["sectors"]:
                continue
            name = re.escape(entry["name"])
            if re.search(r"(?<![\w/-])[$/]" + name + r"(?![\w-])", task, re.I):
                explicit.append(entry)
            elif any(re.search(r"(?<!\w)" + r"\s+".join(map(re.escape, phrase.split())) + r"(?!\w)", task, re.I) for phrase in entry["triggers"]):
                automatic.append(entry)
        return (explicit + automatic)[:MAX_SELECTED]

    def install(self, name, destination_root: Path, state_root: Path, *, update=False):
        """Install a reviewed release, preserving unknown or locally edited files.

        Updates snapshot the complete previous package. Never execute package
        scripts. Assignment, ownership and scope remain the adapter's concern.
        """
        entry = self.entries[name]
        self.verify(entry)
        destination_root, state_root = Path(destination_root).resolve(), Path(state_root).resolve()
        target = safe_path(destination_root, name)
        receipt_path = safe_path(state_root, name + ".json")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.is_file() else None
        if target.exists():
            current = file_hashes(target)
            if current == entry["files"]:
                return {"status": "unchanged", "name": name}
            if not update or not receipt or current != receipt["files"]:
                return {"status": "local_override", "name": name}
        destination_root.mkdir(parents=True, exist_ok=True)
        state_root.mkdir(parents=True, exist_ok=True)
        previous = None
        if target.exists():
            previous = {"files": receipt["files"], "release": receipt["release"], "sha256": json_digest(receipt["files"])}
            backup = safe_path(state_root, "history/" + name + "/" + previous["sha256"])
            if backup.exists() and file_hashes(backup) != previous["files"]:
                raise ValueError("Rollback snapshot was modified")
            if not backup.exists():
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(target, backup)
        with tempfile.TemporaryDirectory(dir=destination_root, prefix=".catalogue-") as temporary:
            stage = Path(temporary) / name
            shutil.copytree(self.package(entry), stage)
            if file_hashes(stage) != entry["files"]:
                raise ValueError("Staged package changed")
            old = Path(temporary) / "previous"
            if target.exists():
                os.replace(target, old)
            try:
                os.replace(stage, target)
                _write_json(receipt_path, {"name": name, "release": self.data["release"], "files": entry["files"], "previous": previous})
            except Exception:
                if target.exists():
                    shutil.rmtree(target)
                if old.exists():
                    os.replace(old, target)
                raise
        return {"status": "updated" if previous else "installed", "name": name}

    @staticmethod
    def rollback(name, destination_root: Path, state_root: Path):
        if not SAFE_NAME.fullmatch(name):
            raise ValueError("Invalid catalogue skill")
        target = safe_path(destination_root, name)
        receipt_path = safe_path(state_root, name + ".json")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        previous = receipt.get("previous")
        if not previous:
            raise ValueError("No prior release is available")
        if file_hashes(target) != receipt["files"]:
            raise ValueError("Local edits prevent rollback")
        backup = safe_path(state_root, "history/" + name + "/" + previous["sha256"])
        if file_hashes(backup) != previous["files"]:
            raise ValueError("Rollback snapshot hash mismatch")
        with tempfile.TemporaryDirectory(dir=destination_root, prefix=".catalogue-") as temporary:
            staged = Path(temporary) / "restored"
            shutil.copytree(backup, staged)
            old = Path(temporary) / "previous"
            os.replace(target, old)
            try:
                os.replace(staged, target)
                _write_json(receipt_path, {"name": name, "release": previous["release"], "files": previous["files"], "previous": None})
            except Exception:
                if target.exists():
                    shutil.rmtree(target)
                os.replace(old, target)
                raise
        return {"status": "rolled_back", "name": name}
