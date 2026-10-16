"""Session/workspace state with task-scoped explicit resource bindings."""
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
    workspace_id:str; name:str; root:str; created_at:float=field(default_factory=time); last_used_at:float=field(default_factory=time); jira_projects:list[str]=field(default_factory=list); studio_root:str=""
@dataclass(slots=True)
class Session:
    session_id:str; agent_id:str; workspace_id:str; workspace_root:str; created_at:float=field(default_factory=time); last_used_at:float=field(default_factory=time); status:str="IDLE"; task:str=""; authorized_resource_ids:set[str]=field(default_factory=set); transcript:list=field(default_factory=list)
class WorkspaceManager:
    def __init__(self,state_path:Path): self.state_path=Path(state_path); self._lock=threading.RLock(); self._workspaces={}; self._load()
    @staticmethod
    def normalize_root(root): return Path(os.path.realpath(os.path.abspath(os.fspath(Path(root).expanduser()))))
    def _load(self):
        if not self.state_path.is_file(): return
        try:
            for item in json.loads(self.state_path.read_text(encoding="utf-8")).get("workspaces",[]):
                w=Workspace(**item); self._workspaces[w.workspace_id]=w
        except (OSError,ValueError,TypeError,KeyError): self._workspaces={}
    def _save(self):
        self.state_path.parent.mkdir(parents=True,exist_ok=True); tmp=self.state_path.with_suffix(self.state_path.suffix+".tmp"); tmp.write_text(json.dumps({"workspaces":[asdict(w) for w in self._workspaces.values()]},indent=2),encoding="utf-8"); os.replace(tmp,self.state_path)
    def register(self,root,name=None):
        resolved=self.normalize_root(root)
        if not resolved.exists() or not resolved.is_dir(): raise FileNotFoundError(f"Workspace directory does not exist: {resolved}")
        with self._lock:
            for w in self._workspaces.values():
                if self.normalize_root(w.root)==resolved: w.last_used_at=time(); w.name=name or w.name; self._save(); return w
            w=Workspace(str(uuid.uuid4()),name or resolved.name or str(resolved),str(resolved)); self._workspaces[w.workspace_id]=w; self._save(); return w
    def list(self):
        with self._lock: return sorted(self._workspaces.values(),key=lambda w:w.last_used_at,reverse=True)
    def recent(self): return self.list()
    def get(self,workspace_id): return self._workspaces[workspace_id]
    def set_jira_projects(self, workspace_id, projects):
        keys = [str(project).strip().upper() for project in projects or [] if str(project).strip()]
        with self._lock:
            workspace = self._workspaces[workspace_id]
            workspace.jira_projects = keys
            self._save()
            return list(workspace.jira_projects)
    def set_studio_root(self, workspace_id, studio_root):
        path = str(studio_root or "").strip()
        with self._lock:
            workspace = self._workspaces[workspace_id]
            workspace.studio_root = path
            self._save()
            return workspace.studio_root
class SessionManager:
    def __init__(self,workspace_manager): self.workspace_manager=workspace_manager; self._sessions={}; self._lock=threading.RLock()
    def create(self,agent_id,workspace):
        s=Session(str(uuid.uuid4()),agent_id,workspace.workspace_id,workspace.root)
        with self._lock: self._sessions[s.session_id]=s
        return s
    def get(self,session_id): return self._sessions[session_id]
    def remember_turn(self, session_id, user_text, assistant_text):
        with self._lock:
            session = self._sessions[session_id]
            session.transcript.append({
                "user": str(user_text),
                "assistant": str(assistant_text),
            })
            del session.transcript[:-6]
            session.last_used_at = time()
            return session
    def update(self,session_id,**changes):
        with self._lock:
            s=self._sessions[session_id]
            for k,v in changes.items():
                if not hasattr(s,k): raise AttributeError(k)
                setattr(s,k,v)
            s.last_used_at=time(); return s
    def bind_resource(self,session_id,resource_id):
        with self._lock: self._sessions[session_id].authorized_resource_ids.add(resource_id)
    def unbind_resource(self,session_id,resource_id):
        with self._lock: before=len(self._sessions[session_id].authorized_resource_ids); self._sessions[session_id].authorized_resource_ids.discard(resource_id); return len(self._sessions[session_id].authorized_resource_ids) < before
    def list(self):
        with self._lock: return sorted(self._sessions.values(),key=lambda s:s.last_used_at,reverse=True)
    def context(self,session_id):
        s=self.get(session_id); return {"session_id":s.session_id,"agent_id":s.agent_id,"workspace_id":s.workspace_id,"workspace_root":s.workspace_root,"authorized_resource_ids":sorted(s.authorized_resource_ids),"platform":platform.system().lower(),"process_working_directory":os.getcwd()}
