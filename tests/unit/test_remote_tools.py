from types import SimpleNamespace

import pytest

from sol_lite.remote import RemoteNode, RemoteNodeManager, RemoteTransport
from sol_lite.tools.remote import _execute, _list_nodes


class Perm:
    def __init__(self):
        self.calls = []

    def check(self, *args, **kwargs):
        self.calls.append((args, kwargs))


class Audit:
    def record(self, *args, **kwargs):
        return None


def test_remote_list_and_execute_use_configured_nodes():
    perm = Perm()
    manager = RemoteNodeManager(perm, Audit(), [
        RemoteNode("lab", "10.0.0.5", "linux", RemoteTransport.SSH, username="dev"),
    ])
    manager._ssh = SimpleNamespace(run=lambda node, command, timeout=120: SimpleNamespace(
        command=command, exit_code=0, stdout="Linux", stderr="",
    ))
    ctx = SimpleNamespace(
        remote_manager=manager,
        permission_engine=perm,
        audit=Audit(),
        session_id="s1",
    )
    listed = _list_nodes(ctx, {})
    assert listed["count"] == 1
    assert listed["nodes"][0]["id"] == "lab"
    result = _execute(ctx, {"node_id": "lab", "command": "uname -a", "plan": "inspect host"})
    assert result["stdout"] == "Linux"
    assert perm.calls[-1][0][0] == "remote.execute"


def test_remote_execute_requires_plan_and_rejects_unconfigured_runtime():
    ctx = SimpleNamespace(
        remote_manager=None,
        permission_engine=Perm(),
        audit=Audit(),
        session_id="s1",
    )
    with pytest.raises(ValueError, match="required"):
        _execute(ctx, {"node_id": "lab", "command": "id", "plan": ""})
    with pytest.raises(RuntimeError, match="not configured"):
        _execute(ctx, {"node_id": "lab", "command": "id", "plan": "inspect"})
