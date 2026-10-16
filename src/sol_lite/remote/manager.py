"""Remote infrastructure manager with explicit authorization boundaries."""
from __future__ import annotations

from dataclasses import dataclass

from ..core.exceptions import PermissionDenied
from ..permissions.scopes import REMOTE_EXECUTE, REMOTE_LIST
from ..security.command_guard import classify_command, validate_command
from .nodes import RemoteNode, RemoteTransport
from .powershell import PowerShellTransport
from .ssh import RemoteCommandResult, SSHTransport


@dataclass(frozen=True, slots=True)
class RemoteExecutionRequest:
    session_id: str
    node_id: str
    command: str
    plan: str
    approval_id: str | None = None
    timeout_seconds: float = 120.0
    audit_command: str | None = None
    rendered_command: str | None = None


class RemoteNodeManager:
    def __init__(self, permission_engine, audit, nodes=()):
        self.permission_engine = permission_engine
        self.audit = audit
        self.nodes: dict[str, RemoteNode] = {node.id: node for node in nodes}
        self._ssh: SSHTransport | None = None
        self._powershell: PowerShellTransport | None = None

    def register(self, node: RemoteNode) -> None:
        if node.id in self.nodes:
            raise ValueError(f"Duplicate remote node: {node.id}")
        self.nodes[node.id] = node

    def get(self, node_id: str) -> RemoteNode:
        try:
            node = self.nodes[node_id]
        except KeyError as exc:
            raise KeyError(f"Unknown remote node: {node_id}") from exc
        if not node.enabled:
            raise PermissionDenied(f"Remote node is disabled: {node_id}")
        return node

    def execute(self, request: RemoteExecutionRequest) -> RemoteCommandResult:
        node = self.get(request.node_id)
        rendered = request.rendered_command or request.command
        visible = request.audit_command or request.command
        self._guard_model_command(node, rendered)
        target = f"{node.id}@{node.hostname}"
        self.permission_engine.check(
            REMOTE_EXECUTE,
            approval_id=request.approval_id,
            operation="remote_execute",
            target=target,
            arguments={"node_id": node.id, "command": visible},
            plan=request.plan,
        )
        timeout = float(request.timeout_seconds or 120.0)
        result = self._transport(node, rendered, timeout)
        self.audit.record(
            "remote.execute",
            node=node.id,
            command=visible,
            exit_code=result.exit_code,
            session_id=request.session_id,
        )
        return result

    def run_prepared(self, node_id: str, command: str, *, audit_command: str, session_id: str = "",
                     timeout: float = 120.0) -> RemoteCommandResult:
        """Run a command the runtime built. Callers check the studio rule first."""
        node = self.get(node_id)
        self.permission_engine.check(
            REMOTE_LIST,
            operation="studio_inspect",
            target=f"{node.id}@{node.hostname}",
            arguments={"node_id": node.id},
            plan=audit_command,
        )
        result = self._transport(node, command, timeout)
        self.audit.record(
            "remote.prepared",
            node=node.id,
            command=audit_command,
            exit_code=result.exit_code,
            session_id=session_id,
        )
        return result

    def _guard_model_command(self, node: RemoteNode, command: str) -> None:
        policy = getattr(self.permission_engine, "policy", None)
        allowed, blocked = [], []
        if policy is not None and hasattr(policy, "terminal_lists"):
            allowed, blocked = policy.terminal_lists()
        validate_command(command, allowed, blocked)
        if classify_command(command) != "read" and node.environment != "lab":
            raise PermissionDenied(
                f"Remote node {node.id} accepts read-only checks until environment is lab."
            )

    def _transport(self, node: RemoteNode, command: str, timeout: float) -> RemoteCommandResult:
        if node.transport is RemoteTransport.SSH:
            if self._ssh is None:
                self._ssh = SSHTransport()
            return self._ssh.run(node, command, timeout=timeout)
        if node.transport is RemoteTransport.POWERSHELL:
            if self._powershell is None:
                self._powershell = PowerShellTransport()
            return self._powershell.run(node, command, timeout=timeout)
        raise NotImplementedError(f"Remote transport not implemented: {node.transport}")
