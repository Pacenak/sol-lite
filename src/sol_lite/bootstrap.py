"""SOL-Lite bootstrap and service composition."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from .agents.registry import AgentRegistry
from .audit.logger import AuditLogger
from .core.runtime import Runtime, RuntimeConfig
from .core.session import SessionManager, WorkspaceManager
from .faults.log import FaultLog
from .models.manager import ModelManager
from .permissions.approvals import ApprovalManager
from .permissions.engine import PermissionEngine
from .permissions.policy import PermissionPolicy
from .platform import get_platform_adapter
from .skills.manager import SkillManager
from .tools import ToolContext, build_tool_registry


@dataclass(slots=True)
class LoadedConfig:
    application: dict[str, Any]
    permissions: dict[str, Any]
    agents: dict[str, Any]
    models: dict[str, Any]
    schedules: dict[str, Any]
    logging: dict[str, Any]
    searxng: dict[str, Any]


def application_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise TypeError(f"Configuration must contain a YAML object: {path}")
    return data


def load_config(root: Path | None = None) -> LoadedConfig:
    root = (root or application_root()).resolve()
    load_dotenv(root / ".env")
    c = root / "config"
    return LoadedConfig(
        application=load_yaml(c / "sol-lite.yaml"), permissions=load_yaml(c / "permissions.yaml"),
        agents=load_yaml(c / "agents.yaml"), models=load_yaml(c / "models.yaml"),
        schedules=load_yaml(c / "schedules.yaml"), logging=load_yaml(c / "logging.yaml"),
        searxng=load_yaml(c / "searxng.yaml"),
    )


def build_runtime_config(c: LoadedConfig) -> RuntimeConfig:
    application = c.application
    workspace = dict(application.get("workspace", {})); data = dict(application.get("data", {}))
    if os.environ.get("SOL_WORKSPACE_ROOT"):
        workspace["root"] = os.environ["SOL_WORKSPACE_ROOT"]
    if os.environ.get("SOL_DATA_ROOT"):
        data["root"] = os.environ["SOL_DATA_ROOT"]
    return RuntimeConfig(
        application=dict(application.get("application", {})), runtime=dict(application.get("runtime", {})),
        workspace=workspace, data=data, logging=dict(application.get("logging", {})),
        background=dict(application.get("background", {})), macos=dict(application.get("macos", {})),
        nas=dict(application.get("nas", {})), bridge=dict(application.get("bridge", {})),
        windows=dict(application.get("windows", {})),
    )


def bootstrap(root: Path | None = None) -> Runtime:
    root = (root or application_root()).resolve()
    config = load_config(root)
    runtime = Runtime(build_runtime_config(config), root)
    models = ModelManager(config.models, os.environ.get("SOL_OLLAMA_URL", config.models.get("provider", {}).get("endpoint", "http://127.0.0.1:11434")))
    agents = AgentRegistry(config.agents)
    approvals = ApprovalManager()
    permissions = PermissionEngine(PermissionPolicy(config.permissions), approvals)
    log_setting = config.logging.get("logging", config.logging)
    audit = AuditLogger(root / (log_setting.get("file", "./logs/sol-lite-audit.jsonl") if isinstance(log_setting, dict) else "logs/sol-lite-audit.jsonl"))
    faults = FaultLog(root / "data" / "faults" / "faults.json")
    platform_adapter = get_platform_adapter()
    skill_manager = SkillManager(runtime.root, runtime.data_root)
    tools = build_tool_registry()
    search_config = dict(config.searxng.get("searxng", config.searxng))
    if os.environ.get("SOL_SEARXNG_URL"):
        search_config["url"] = os.environ["SOL_SEARXNG_URL"]
    if os.environ.get("SOL_SEARXNG_ENABLED"):
        search_config["enabled"] = os.environ["SOL_SEARXNG_ENABLED"].casefold() in {"1", "true", "yes", "on"}
    context = ToolContext(runtime.workspace_root, permissions, audit, faults, platform_adapter, project_root=runtime.workspace_root, skill_manager=skill_manager, search_config=search_config)
    workspace_manager = WorkspaceManager(runtime.data_root / "state" / "workspaces.json")
    session_manager = SessionManager(workspace_manager)
    runtime.models = models; runtime.agents = agents; runtime.approvals = approvals
    runtime.permissions = permissions; runtime.audit = audit; runtime.fault_log = faults
    runtime.tools = tools; runtime.tool_context = context; runtime.platform = platform_adapter
    runtime.workspace_manager = workspace_manager; runtime.session_manager = session_manager
    runtime.skill_manager = skill_manager
    return runtime
