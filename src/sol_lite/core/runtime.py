"""SOL-Lite runtime lifecycle."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .event_bus import Event, EventBus
from .health import HealthResult
from .lifecycle import RuntimeState
from .tasks import TaskManager


@dataclass(slots=True)
class RuntimeConfig:
    application: dict[str, Any]
    runtime: dict[str, Any]
    workspace: dict[str, Any]
    data: dict[str, Any]
    logging: dict[str, Any]
    background: dict[str, Any]
    macos: dict[str, Any]
    nas: dict[str, Any]
    bridge: dict[str, Any]
    windows: dict[str, Any]

class Runtime:
    def __init__(self, config: RuntimeConfig, root: Path):
        self.config = config
        self.root = root.resolve()
        self.state = RuntimeState.CREATED
        self.events = EventBus()
        self.tasks = TaskManager(int(config.runtime.get("max_concurrent_agents", 4)))

    @property
    def application_name(self):
        return str(self.config.application.get("name", ""))

    @property
    def application_version(self):
        return str(self.config.application.get("version", ""))

    @property
    def workspace_root(self):
        return (self.root / self.config.workspace.get("root", "./workspace")).resolve()

    @property
    def data_root(self):
        return (self.root / self.config.data.get("root", "./data")).resolve()

    def _create_directories(self):
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.data_root.mkdir(parents=True, exist_ok=True)
        for rel in self.config.workspace.get("directories", {}).values():
            (self.root / rel).mkdir(parents=True, exist_ok=True)
        for rel in self.config.data.get("directories", {}).values():
            (self.root / rel).mkdir(parents=True, exist_ok=True)
        log_file = self.config.logging.get("file")
        if log_file:
            (self.root / Path(log_file).parent).mkdir(parents=True, exist_ok=True)

    def start(self):
        if self.state not in {RuntimeState.CREATED, RuntimeState.STOPPED}:
            return
        self.state = RuntimeState.STARTING
        self.events.publish(Event("runtime.starting", "runtime"))
        try:
            self._create_directories()
        except Exception:
            self.state = RuntimeState.FAILED
            self.events.publish(Event("runtime.failed", "runtime"))
            raise
        self.state = RuntimeState.RUNNING
        self.events.publish(Event("runtime.running", "runtime"))

    def stop(self):
        if self.state not in {RuntimeState.RUNNING, RuntimeState.FAILED}:
            return
        self.state = RuntimeState.STOPPING
        self.events.publish(Event("runtime.stopping", "runtime"))
        self.tasks.shutdown()
        self.state = RuntimeState.STOPPED
        self.events.publish(Event("runtime.stopped", "runtime"))

    def health_check(self):
        errors, warnings = [], []
        if not self.application_name:
            errors.append("Application name is missing.")
        if not self.application_version:
            errors.append("Application version is missing.")
        try:
            self.workspace_root.mkdir(parents=True, exist_ok=True)
            self.data_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            errors.append(f"Runtime roots are not usable: {exc}")
        if self.config.bridge.get("enabled"):
            warnings.append("Bridge is configured but is not implemented in v0.2.5.")
        return HealthResult.failure(errors, warnings) if errors else HealthResult.success(warnings)
