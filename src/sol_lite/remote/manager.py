"""Remote infrastructure manager with explicit authorization boundaries."""
from __future__ import annotations

from dataclasses import dataclass

from ..core.exceptions import PermissionDenied
from ..permissions.scopes import NETWORK
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
        target = f"{node.id}@{node.hostname}"
        self.permission_engine.check(
            NETWORK,
            approval_id=request.approval_id,
            operation="remote_execute",
            target=target,
            arguments={"node_id": node.id, "command": request.command},
            plan=request.plan,
        )
        if node.transport is RemoteTransport.SSH:
            if self._ssh is None:
                self._ssh = SSHTransport()
            result = self._ssh.run(node, request.command)
        elif node.transport is RemoteTransport.POWERSHELL:
            if self._powershell is None:
                self._powershell = PowerShellTransport()
            result = self._powershell.run(node, request.command)
        else:
            raise NotImplementedError(f"Remote transport not implemented: {node.transport}")
        self.audit.record("remote.execute", node=node.id, command=request.command,
                          exit_code=result.exit_code, session_id=request.session_id)
        return result
