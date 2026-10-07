"""Session and workspace state for concurrent agent conversations."""
from __future__ import annotations

import json
import os
import platform
import threading
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import time


@dataclass(slots=True)
class Workspace:
    workspace_id: str
    name: str
    root: str
    created_at: float = field(default_factory=time)
    last_used_at: float = field(default_factory=time)


@dataclass(slots=True)
class Session:
    session_id: str
    agent_id: str
    workspace_id: str
    workspace_root: str
    created_at: float = field(default_factory=time)
    last_used_at: float = field(default_factory=time)
    status: str = "IDLE"
    task: str = ""


class WorkspaceManager:
    """Persistent, named workspace registry with realpath normalization."""

    def __init__(self, state_path: Path):
        self.state_path = Path(state_path)
        self._lock = threading.RLock()
        self._workspaces: dict[str, Workspace] = {}
        self._load()

    @staticmethod
    def normalize_root(root: str | os.PathLike[str]) -> Path:
        return Path(os.path.realpath(os.path.abspath(os.fspath(Path(root).expanduser()))))

    def _load(self) -> None:
        if not self.state_path.is_file():
            return
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            for item in data.get("workspaces", []):
                workspace = Workspace(**item)
                self._workspaces[workspace.workspace_id] = workspace
        except (OSError, ValueError, TypeError, KeyError):
            self._workspaces = {}

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps({"workspaces": [asdict(w) for w in self._workspaces.values()]}, indent=2), encoding="utf-8")
        os.replace(tmp, self.state_path)

    def register(self, root: str | os.PathLike[str], name: str | None = None) -> Workspace:
        resolved = self.normalize_root(root)
        if not resolved.exists() or not resolved.is_dir():
            raise FileNotFoundError(f"Workspace directory does not exist: {resolved}")
        with self._lock:
            for workspace in self._workspaces.values():
                if self.normalize_root(workspace.root) == resolved:
                    workspace.last_used_at = time()
                    if name:
                        workspace.name = name
                    self._save()
                    return workspace
            workspace = Workspace(str(uuid.uuid4()), name or resolved.name or str(resolved), str(resolved))
            self._workspaces[workspace.workspace_id] = workspace
            self._save()
            return workspace

    def list(self) -> list[Workspace]:
        with self._lock:
            return sorted(self._workspaces.values(), key=lambda w: w.last_used_at, reverse=True)

    def get(self, workspace_id: str) -> Workspace:
        with self._lock:
            return self._workspaces[workspace_id]

    def recent(self) -> list[Workspace]:
        return self.list()


class SessionManager:
    """Tracks independent agent conversations and their workspace boundaries."""

    def __init__(self, workspace_manager: WorkspaceManager):
        self.workspace_manager = workspace_manager
        self._sessions: dict[str, Session] = {}
        self._lock = threading.RLock()

    def create(self, agent_id: str, workspace: Workspace) -> Session:
        session = Session(str(uuid.uuid4()), agent_id, workspace.workspace_id, workspace.root)
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Session:
        with self._lock:
            return self._sessions[session_id]

    def update(self, session_id: str, **changes) -> Session:
        with self._lock:
            session = self._sessions[session_id]
            for key, value in changes.items():
                if not hasattr(session, key):
                    raise AttributeError(key)
                setattr(session, key, value)
            session.last_used_at = time()
            return session

    def list(self) -> list[Session]:
        with self._lock:
            return sorted(self._sessions.values(), key=lambda s: s.last_used_at, reverse=True)

    def context(self, session_id: str) -> dict[str, object]:
        session = self.get(session_id)
        return {
            "session_id": session.session_id,
            "agent_id": session.agent_id,
            "workspace_id": session.workspace_id,
            "workspace_root": session.workspace_root,
            "platform": platform.system().lower(),
            "process_working_directory": os.getcwd(),
        }
