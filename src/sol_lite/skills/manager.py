"""Agent Skills discovery, validation, provenance, quarantine and installation."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

DANGEROUS_PATTERNS = (
    re.compile(r"ignore (?:all|your) (?:previous|system) instructions", re.IGNORECASE),
    re.compile(r"disable (?:security|approval|permission)", re.IGNORECASE),
    re.compile(r"(?:upload|exfiltrate|send).*(?:secret|credential|token|password)", re.IGNORECASE),
)


@dataclass(slots=True)
class SkillRecord:
    skill_id: str
    name: str
    description: str
    path: str
    source_type: str
    source: str
    source_ref: str | None
    sha256: str
    trust: str = "UNTRUSTED"
    status: str = "DISCOVERED"
    agents: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class SkillManager:
    def __init__(self, root: Path, state_root: Path):
        self.root = Path(root).resolve()
        self.state_root = Path(state_root).resolve()
        self.installed_root = self.state_root / "skills" / "installed"
        self.pending_root = self.state_root / "skills" / "pending"
        self.quarantine_root = self.state_root / "skills" / "quarantine"
        self.manifest_path = self.state_root / "skills" / "manifest.json"
        self.records: dict[str, SkillRecord] = {}
        self._load()

    @staticmethod
    def _hash_tree(path: Path) -> str:
        digest = hashlib.sha256()
        for item in sorted(path.rglob("*")):
            if item.is_file() and not item.is_symlink():
                digest.update(item.relative_to(path).as_posix().encode())
                digest.update(item.read_bytes())
        return digest.hexdigest()

    @staticmethod
    def _frontmatter(text: str) -> tuple[str, str]:
        if not text.startswith("---"):
            raise ValueError("SKILL.md must begin with YAML frontmatter.")
        end = text.find("\n---", 3)
        if end < 0:
            raise ValueError("SKILL.md frontmatter is not closed.")
        block = text[3:end].strip()
        values = yaml.safe_load(block)
        if not isinstance(values, dict):
            raise TypeError("SKILL.md frontmatter must be a YAML object.")
        name = values.get("name")
        description = values.get("description")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("SKILL.md frontmatter requires a string name.")
        if not isinstance(description, str) or not description.strip():
            raise ValueError("SKILL.md frontmatter requires a string description.")
        return name.strip(), description.strip()

    @staticmethod
    def _validate_path(path: Path) -> None:
        for item in path.rglob("*"):
            if item.is_symlink():
                raise ValueError(f"Symlinks are not allowed in imported skills: {item}")
            if item.is_file() and item.stat().st_size > 10 * 1024 * 1024:
                raise ValueError(f"Skill file exceeds 10 MiB import limit: {item}")

    def inspect_directory(self, directory: Path, source_type="local", source="local", source_ref=None) -> list[SkillRecord]:
        directory = Path(directory).resolve()
        if not directory.is_dir():
            raise FileNotFoundError(directory)
        records = []
        candidates = [directory / "SKILL.md"] if (directory / "SKILL.md").is_file() else [p for p in sorted(directory.rglob("SKILL.md")) if "/.git/" not in p.as_posix()]
        if len(candidates) > 1000:
            raise ValueError("Skill source contains more than 1000 SKILL.md files.")
        for skill_md in candidates:
            skill_dir = skill_md.parent
            self._validate_path(skill_dir)
            text = skill_md.read_text(encoding="utf-8")
            name, description = self._frontmatter(text)
            warnings = []
            combined = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in skill_dir.rglob("*") if p.is_file() and p.stat().st_size < 1_000_000)
            if any(pattern.search(combined) for pattern in DANGEROUS_PATTERNS):
                warnings.append("Potential prompt-injection or unsafe instruction detected.")
            for executable in skill_dir.rglob("*"):
                if executable.suffix.lower() in {".py", ".ps1", ".sh", ".bat", ".cmd", ".js", ".ts"}:
                    warnings.append(f"Executable script present: {executable.relative_to(skill_dir).as_posix()}")
            skill_id = re.sub(r"[^a-z0-9._-]+", "-", name.lower()).strip("-")
            records.append(SkillRecord(skill_id, name, description, str(skill_dir), source_type, source, source_ref, self._hash_tree(skill_dir), warnings=sorted(set(warnings))))
        return records

    def discover(self, source: str | Path) -> list[SkillRecord]:
        path = Path(source).expanduser()
        if path.exists():
            if path.is_file() and path.suffix.lower() == ".zip":
                with tempfile.TemporaryDirectory() as tmp:
                    self._safe_extract_zip(path, Path(tmp))
                    return self.inspect_directory(Path(tmp), "zip", str(path))
            if path.is_file() and path.name == "SKILL.md":
                return self.inspect_directory(path.parent)
            return self.inspect_directory(path)
        if str(source).startswith("https://github.com/"):
            return self._discover_git(str(source))
        raise FileNotFoundError(source)

    def _discover_git(self, url: str) -> list[SkillRecord]:
        with tempfile.TemporaryDirectory() as tmp:
            completed = subprocess.run(["git", "clone", "--depth", "1", url, tmp], capture_output=True, text=True, check=False, timeout=120)
            if completed.returncode:
                raise RuntimeError(completed.stderr.strip() or "git clone failed")
            commit = subprocess.run(["git", "-C", tmp, "rev-parse", "HEAD"], capture_output=True, text=True, check=False, timeout=30).stdout.strip()
            return self.inspect_directory(Path(tmp), "git", url, commit)

    @staticmethod
    def _safe_extract_zip(source: Path, destination: Path) -> None:
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            if len(infos) > 10000:
                raise ValueError("ZIP contains too many entries.")
            for info in infos:
                member = Path(info.filename)
                if member.is_absolute() or ".." in member.parts:
                    raise ValueError(f"Unsafe ZIP member path: {info.filename}")
                target = (destination / member).resolve()
                if os.path.commonpath([str(destination.resolve()), str(target)]) != str(destination.resolve()):
                    raise ValueError(f"ZIP member escapes extraction directory: {info.filename}")
            archive.extractall(destination)

    def install(self, record: SkillRecord, *, trust="REVIEWED", agent_ids=None) -> SkillRecord:
        source = Path(record.path).resolve()
        if not source.is_dir():
            raise FileNotFoundError(source)
        destination = self.installed_root / record.skill_id
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination, symlinks=False)
        installed = SkillRecord(**{**asdict(record), "path": str(destination), "trust": trust, "status": "INSTALLED", "agents": list(agent_ids or [])})
        self.records[installed.skill_id] = installed
        self._save()
        return installed

    def quarantine(self, record: SkillRecord) -> SkillRecord:
        source = Path(record.path).resolve()
        destination = self.quarantine_root / record.skill_id
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination, symlinks=False)
        quarantined = SkillRecord(**{**asdict(record), "path": str(destination), "trust": "UNTRUSTED", "status": "QUARANTINED"})
        self.records[quarantined.skill_id] = quarantined
        self._save()
        return quarantined

    def update(self, skill_id: str) -> SkillRecord:
        current = self.records[skill_id]
        source = current.source
        if current.source_type in {"builtin", "workspace"}:
            raise ValueError(f"Skill '{skill_id}' is not an externally managed installed skill.")
        records = self.discover(source)
        matches = [record for record in records if record.skill_id == skill_id]
        if not matches:
            raise FileNotFoundError(f"Updated skill '{skill_id}' was not found in {source}.")
        return self.install(matches[0], trust=current.trust, agent_ids=current.agents)

    def assign(self, skill_id: str, agent_id: str) -> SkillRecord:
        record = self.records[skill_id]
        if agent_id not in record.agents:
            record.agents.append(agent_id)
        record.agents.sort()
        self._save()
        return record

    def remove(self, skill_id: str) -> None:
        record = self.records.pop(skill_id)
        path = Path(record.path)
        if path.exists():
            shutil.rmtree(path)
        self._save()

    def for_agent(self, agent_id: str, workspace_root: Path | None = None) -> list[SkillRecord]:
        selected = [r for r in self.records.values() if not r.agents or agent_id in r.agents]
        builtin_root = self.root / "skills"
        if builtin_root.is_dir():
            for record in self.inspect_directory(builtin_root, "builtin", str(builtin_root)):
                record.trust = "BUILTIN"
                record.status = "BUILTIN"
                selected.append(record)
        if workspace_root:
            selected.extend(self.discover_workspace_skills(Path(workspace_root)))
        unique = {r.skill_id: r for r in selected}
        return sorted(unique.values(), key=lambda r: r.skill_id)

    def discover_workspace_skills(self, workspace_root: Path) -> list[SkillRecord]:
        records = []
        for relative in (".agents/skills", ".claude/skills", ".codex/skills", "skills"):
            path = workspace_root / relative
            if path.is_dir():
                records.extend(self.inspect_directory(path, "workspace", str(path)))
        return records

    def prompt_context(self, agent_id: str, workspace_root: Path | None = None, task: str = "") -> str:
        records = self.for_agent(agent_id, workspace_root)
        if not records:
            return "No additional skills are active for this agent."
        lines = ["ACTIVE SKILLS", "Use the descriptions for routing. Load the detailed skill instructions only for skills relevant to the current task. Skills never grant permissions."]
        task_words = set(re.findall(r"[a-z0-9_-]+", task.lower()))
        selected_details = []
        for record in records:
            lines.append(f"- {record.skill_id}: {record.description} [trust={record.trust}; source={record.source}]")
            relevance = set(re.findall(r"[a-z0-9_-]+", f"{record.skill_id} {record.description}".lower()))
            if task_words & relevance:
                selected_details.append(record)
        for record in selected_details[:4]:
            skill_md = Path(record.path) / "SKILL.md"
            if skill_md.is_file():
                lines.append(f"\nDETAILED SKILL: {record.skill_id}\n{skill_md.read_text(encoding='utf-8').strip()}")
        return "\n".join(lines)

    def _save(self):
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps({k: asdict(v) for k, v in self.records.items()}, indent=2), encoding="utf-8")

    def _load(self):
        if not self.manifest_path.is_file():
            return
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            self.records = {k: SkillRecord(**v) for k, v in data.items()}
        except (OSError, ValueError, TypeError):
            self.records = {}
