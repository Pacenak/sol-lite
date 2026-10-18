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

from .catalogue_contract import Catalogue, MAX_RESOURCE_BYTES, safe_path

_SKILL_MATCH_STOPWORDS = frozenset({
    "the", "and", "for", "with", "from", "that", "this", "into", "using",
    "before", "without", "your", "you", "are", "not", "but", "its", "all",
    "any", "can", "may", "use", "used", "only", "than", "then", "when",
    "what", "who", "how", "why", "where", "which", "have", "has", "been",
    "will", "please", "current", "here", "there", "about", "after", "over",
    "under", "also", "such", "other", "each", "both", "some", "more",
    "very", "just", "like", "onto", "upon", "out", "our", "their", "them",
    "they", "does", "doing", "done", "make", "made", "need", "needs",
    "want", "tell", "show", "list", "full", "able",
})


def _skill_terms(text: str) -> set[str]:
    """Meaningful words for skill selection. Common words do not count as a match."""
    return {
        word
        for word in re.findall(r"[a-z0-9_-]+", (text or "").lower())
        if len(word) >= 4 and word not in _SKILL_MATCH_STOPWORDS
    }


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
    trigger_phrases: list[str] = field(default_factory=list)


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
        if directory == (self.root / "skills").resolve():
            candidates = [p for p in candidates if not p.is_relative_to(directory / "ecosystem")]
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
            if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", skill_id):
                raise ValueError("Skill name must produce a nonempty safe identifier.")
            values = yaml.safe_load(text[3:text.find("\n---", 3)])
            metadata = values.get("metadata", {})
            triggers = metadata.get("trigger-phrases", "") if isinstance(metadata, dict) else ""
            if not isinstance(triggers, str):
                raise TypeError("metadata.trigger-phrases must be a pipe-separated string.")
            phrases = [phrase.strip().casefold() for phrase in triggers.split("|") if phrase.strip()]
            records.append(SkillRecord(skill_id, name, description, str(skill_dir), source_type, source, source_ref, self._hash_tree(skill_dir), warnings=sorted(set(warnings)), trigger_phrases=phrases))
        return records

    def discover(self, source: str | Path) -> list[SkillRecord]:
        path = Path(source).expanduser()
        if path.exists():
            if path.is_file() and path.suffix.lower() == ".zip":
                with tempfile.TemporaryDirectory() as tmp:
                    self._safe_extract_zip(path, Path(tmp))
                    return self._stage(self.inspect_directory(Path(tmp), "zip", str(path)))
            if path.is_file() and path.name == "SKILL.md":
                return self.inspect_directory(path.parent, source=str(path.resolve()))
            return self.inspect_directory(path, source=str(path.resolve()))
        if str(source).startswith("https://github.com/"):
            return self._discover_git(str(source))
        raise FileNotFoundError(source)

    def _discover_git(self, url: str) -> list[SkillRecord]:
        with tempfile.TemporaryDirectory() as tmp:
            completed = subprocess.run(["git", "clone", "--depth", "1", url, tmp], capture_output=True, text=True, check=False, timeout=120)
            if completed.returncode:
                raise RuntimeError(completed.stderr.strip() or "git clone failed")
            commit = subprocess.run(["git", "-C", tmp, "rev-parse", "HEAD"], capture_output=True, text=True, check=False, timeout=30).stdout.strip()
            return self._stage(self.inspect_directory(Path(tmp), "git", url, commit))

    def _stage(self, records: list[SkillRecord]) -> list[SkillRecord]:
        """Retain inspected imports after extraction/clone temporary cleanup.

        Content-addressed directories keep later discoveries from replacing a
        previously inspected candidate. Pending content is never active.
        """
        for record in records:
            destination = self.pending_root / record.sha256 / record.skill_id
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(record.path, destination)
            record.path = str(destination)
        return records

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
        self._validate_path(source)
        if self._hash_tree(source) != record.sha256:
            raise ValueError("Skill content changed after inspection; discover and review it again.")
        destination = safe_path(self.installed_root, record.skill_id)
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
        destination = safe_path(self.quarantine_root, record.skill_id)
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
        if current.source_type == "catalogue":
            result = self.install_catalogue(skill_id, update=True)
            if result["status"] == "local_override":
                raise ValueError("Local skill edits must be reconciled before updating.")
            return self.records[skill_id]
        source = current.source
        if current.source_type in {"builtin", "workspace"}:
            raise ValueError(f"Skill '{skill_id}' is not an externally managed installed skill.")
        records = self.discover(source)
        matches = [record for record in records if record.skill_id == skill_id]
        if not matches:
            raise FileNotFoundError(f"Updated skill '{skill_id}' was not found in {source}.")
        if matches[0].warnings:
            raise ValueError("Updated skill has warnings; inspect and review it before importing again.")
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

    def _ecosystem_records(self) -> list[SkillRecord]:
        """Read the shared release metadata without hashing every asset each turn."""
        catalog_path = self.root / "config" / "sol-ecosystem-catalog.json"
        if not catalog_path.is_file():
            return []
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        if catalog.get("schema_version") != 1:
            raise ValueError("Unsupported SOL ecosystem catalog version")
        records = []
        base = (self.root / "skills" / "ecosystem").resolve()
        for row in catalog.get("skills", []):
            directory = (base / row["name"]).resolve()
            if not directory.is_relative_to(base) or directory == base:
                raise ValueError("Ecosystem skill path escapes its root")
            skill_md = directory / "SKILL.md"
            if not skill_md.is_file():
                continue
            text = skill_md.read_text(encoding="utf-8")
            name, description = self._frontmatter(text)
            records.append(SkillRecord(
                name, name, description, str(directory), "builtin",
                "https://github.com/" + row["repository"] if row["repository"] else "SOL source discovery adapter", row["commit"],
                hashlib.sha256(text.encode("utf-8")).hexdigest(),
                trust="BUILTIN", status="BUILTIN",
            ))
        return records

    @staticmethod
    def _prompt_skill_page(records: list[SkillRecord], task: str, required_names=None) -> list[SkillRecord]:
        """Keep all skills discoverable, but bound per-turn metadata and details."""
        words = _skill_terms(task)
        required_names = set(required_names or ())
        def rank(record):
            explicit = bool(re.search(r"(?<![\w-])\$" + re.escape(record.skill_id) + r"(?![\w-])", task, re.IGNORECASE))
            phrase = any(re.search(r"(?<!\w)" + r"\s+".join(map(re.escape, p.split())) + r"(?!\w)", task, re.I) for p in getattr(record, "trigger_phrases", []))
            terms = _skill_terms(record.skill_id.replace("-", " ") + " " + record.description)
            overlap = len(words & terms) / max(1, len(words))
            ecosystem = "ecosystem" in Path(record.path).parts
            return (-int(explicit), -int(phrase or record.skill_id in required_names), -overlap, int(ecosystem), record.skill_id)
        return sorted(records, key=rank)[:48]

    def for_agent(self, agent_id: str, workspace_root: Path | None = None) -> list[SkillRecord]:
        selected = [r for r in self.records.values()
                    if r.status == "INSTALLED" and (not r.agents or agent_id in r.agents)]
        catalogue = self.catalogue()
        if catalogue:
            baseline = [self._catalogue_record(entry) for entry in catalogue.entries.values()
                        if entry["default"] and agent_id in entry["agents"]]
            selected = baseline + selected
        builtin_root = self.root / "skills"
        if builtin_root.is_dir():
            for record in self.inspect_directory(builtin_root, "builtin", str(builtin_root)):
                record.trust = "BUILTIN"
                record.status = "BUILTIN"
                selected.append(record)
        selected.extend(self._ecosystem_records())
        if workspace_root:
            selected.extend(self.discover_workspace_skills(Path(workspace_root)))
        unique = {r.skill_id: r for r in selected}
        return sorted(unique.values(), key=lambda r: r.skill_id)

    def catalogue(self):
        folder = self.root / "skill_catalogue"
        manifest = folder / "catalogue.json"
        if not manifest.is_file():
            return None
        signature = (str(folder), manifest.stat().st_mtime_ns, manifest.stat().st_size)
        cached = getattr(self, "_catalogue_cache", None)
        if cached is None or cached[0] != signature:
            self._catalogue_cache = (signature, Catalogue(folder))
        return self._catalogue_cache[1]

    def _catalogue_record(self, entry, path=None):
        return SkillRecord(
            entry["name"], entry["name"], entry["description"],
            str(path or self.root / "skill_catalogue" / "packages" / entry["name"]),
            "catalogue", "sol-shared-catalogue", self.catalogue().data["release"],
            self._hash_tree(path or self.root / "skill_catalogue" / "packages" / entry["name"]),
            trust="REVIEWED", status="INSTALLED" if path else "BUILTIN",
            agents=list(entry["agents"]), trigger_phrases=entry["triggers"],
        )

    def install_catalogue(self, name, *, agent_id="", update=False):
        catalogue = self.catalogue()
        if catalogue is None:
            raise FileNotFoundError("No shared catalogue release is installed")
        entry = catalogue.entries[name]
        if agent_id and agent_id not in entry["agents"]:
            raise ValueError("Catalogue skill is not assigned to this agent role")
        result = catalogue.install(name, self.installed_root, self.state_root / "skills/catalogue", update=update)
        if result["status"] != "local_override":
            previous = self.records.get(name)
            record = self._catalogue_record(entry, self.installed_root / name)
            record.agents = list(previous.agents) if previous else ([agent_id] if agent_id else list(entry["agents"]))
            self.records[name] = record
            self._save()
        return result

    def rollback_catalogue(self, name):
        result = Catalogue.rollback(name, self.installed_root, self.state_root / "skills/catalogue")
        if name in self.records:
            self.records[name].sha256 = self._hash_tree(self.installed_root / name)
            receipt = json.loads((self.state_root / "skills/catalogue" / (name + ".json")).read_text(encoding="utf-8"))
            self.records[name].source_ref = receipt["release"]
            self._save()
        return result

    def read_resource(self, agent_id, skill_id, relative="SKILL.md", workspace_root=None):
        records = self.for_agent(agent_id, workspace_root)
        matches = [r for r in records if r.skill_id == skill_id and r.status != "QUARANTINED"]
        if not matches:
            raise FileNotFoundError("Skill is unavailable for this agent")
        record = matches[0]
        path = safe_path(Path(record.path), relative)
        if not path.is_file():
            raise FileNotFoundError(relative)
        if path.stat().st_size > MAX_RESOURCE_BYTES:
            raise ValueError("Skill resource exceeds context read limit")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _context_page(records, task, required_ids):
        """Bound discovery metadata; retain explicit and exact phrase routing."""
        words = _skill_terms(task)
        def rank(record):
            explicit = bool(re.search(r"(?<![\w-])\$" + re.escape(record.skill_id) + r"(?![\w-])", task, re.I))
            phrase = any(re.search(r"(?<!\w)" + r"\s+".join(map(re.escape, p.split())) + r"(?!\w)", task, re.I) for p in record.trigger_phrases)
            relevance = len(words & _skill_terms(record.skill_id.replace("-", " ") + " " + record.description))
            return (-int(explicit), -int(phrase or record.skill_id in required_ids), -relevance, record.skill_id)
        return sorted(records, key=rank)[:16]

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
        lines = ["ACTIVE SKILLS", "Use the descriptions for routing. Load the detailed skill instructions only for skills relevant to the current task. Skills never grant permissions. Workspace file and directory tools remain available."]
        task_words = _skill_terms(task)
        selected_details = []
        # Artifact workflows must not lose essential guidance to incidental keyword
        # matches or the generic four-skill cap.
        artifact_skills = set()
        groups = (
            ({"document", "documents", "docs", "docx", "pdf", "report", "reports"}, {"documentation-engineering", "document-layout"}),
            ({"presentation", "slides", "deck", "pptx", "powerpoint"}, {"presentation-design"}),
            ({"spreadsheet", "spreadsheets", "workbook", "workbooks", "xlsx", "excel"}, {"spreadsheet-reporting"}),
            ({"diagram", "diagrams", "mermaid", "flowchart", "sequence"}, {"diagram-design", "mermaid-diagrams"}),
            ({"odoo", "gst101a", "gather", "myir", "plg-odooacc"}, {"studio-odoo-import"}),
            (
                {
                    "toolbelt",
                    "solboot",
                    "sollite",
                    "solbrain",
                    "seccheck",
                    "lite-pen",
                    "litepen",
                    "pouch",
                    "e3531",
                    "mifi",
                    "athen",
                    "admin-stick",
                    "studio-admin",
                },
                {"studio-admin-toolbelt"},
            ),
        )
        specialist = set()
        for triggers, skills in groups:
            specialist.update(skills)
            if task_words & triggers:
                artifact_skills.update(skills)
        total_skills = len(records)
        records = self._prompt_skill_page(records, task, required_names=artifact_skills)
        records = self._context_page(records, task, artifact_skills)
        lines.append(f"Showing {len(records)} of {total_skills} skills, ranked for this task. "
                     "For more, read config/sol-ecosystem-catalog.json or use skill_discover on a source. "
                     "Invoke a specific skill with $skill-id. Inspect prerequisites before execution.")
        for record in records:
            lines.append(f"- {record.skill_id}: {record.description} [trust={record.trust}; source={record.source}; path={record.path}]")
            # Manifest phrases use whole-word boundaries and allow whitespace
            # between words. Explicit $skill-name invocation always selects it.
            explicit = re.search(r"(?<![\w-])\$" + re.escape(record.skill_id) + r"(?![\w-])", task, re.IGNORECASE)
            matched = any(
                re.search(r"(?<!\w)" + r"\s+".join(re.escape(word) for word in phrase.split()) + r"(?!\w)", task, re.IGNORECASE)
                for phrase in record.trigger_phrases
            )
            if explicit or matched:
                artifact_skills.add(record.skill_id)
            if record.trigger_phrases:
                continue
            if record.skill_id in specialist:
                continue
            relevance = _skill_terms(f"{record.skill_id} {record.description}")
            if task_words & relevance:
                selected_details.append(record)
        required = [r for r in records if r.skill_id in artifact_skills]
        optional = [r for r in selected_details if r.skill_id not in artifact_skills][:4]
        # Keep explicit catalogue requests ahead of automatic phrase matches;
        # the shared pack never consumes more than four procedure bodies.
        catalogue = self.catalogue()
        shared_selected = []
        if catalogue:
            eligible = [r.skill_id for r in records if r.source_type == "catalogue"]
            picked = {e["name"] for e in catalogue.select(task, runtime="lite", names=eligible)}
            shared_selected = [r for r in required + optional if r.skill_id in picked]
            required = [r for r in required if r.source_type != "catalogue"]
            optional = [r for r in optional if r.source_type != "catalogue"]
        for record in required + optional + shared_selected:
            skill_md = Path(record.path) / "SKILL.md"
            if skill_md.is_file():
                if record.source_type == "catalogue":
                    if record.status == "BUILTIN":
                        catalogue.verify(catalogue.entries[record.skill_id])
                    availability = catalogue.availability(catalogue.entries[record.skill_id])
                    lines.append("CATALOGUE PREREQUISITES: " + json.dumps(availability) + "; tool access remains runtime-gated.")
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
