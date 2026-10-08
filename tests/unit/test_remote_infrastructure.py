from types import SimpleNamespace

import pytest

from sol_lite.remote import RemoteExecutionRequest, RemoteNode, RemoteNodeManager, RemoteTransport


class PermissionProbe:
    def __init__(self):
        self.calls = []

    def check(self, *args, **kwargs):
        self.calls.append((args, kwargs))


class AuditProbe:
    def __init__(self):
        self.records = []

    def record(self, event, **data):
        self.records.append((event, data))


def test_remote_execution_requires_network_permission_and_routes(monkeypatch):
    permissions = PermissionProbe()
    audit = AuditProbe()
    manager = RemoteNodeManager(permissions, audit, [
        RemoteNode("linux1", "10.0.0.5", "linux", RemoteTransport.SSH, username="dev")
    ])

    class FakeSSH:
        def run(self, node, command):
            return SimpleNamespace(command=command, exit_code=0, stdout="ok", stderr="")

    manager._ssh = FakeSSH()
    result = manager.execute(RemoteExecutionRequest("s1", "linux1", "uname -a", "inspect host", "approval"))
    assert result.stdout == "ok"
    assert permissions.calls[0][0][0] == "network"
    assert audit.records[0][0] == "remote.execute"


def test_unknown_node_is_rejected():
    manager = RemoteNodeManager(PermissionProbe(), AuditProbe())
    with pytest.raises(KeyError):
        manager.get("missing")
