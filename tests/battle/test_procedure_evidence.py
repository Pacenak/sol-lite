from types import SimpleNamespace

from sol_lite.agents.runtime import AgentRuntime
from sol_lite.faults.log import FaultLog


class _Models:
    class Profile:
        model = "fake"
        temperature = 0.1
        timeout_seconds = 10

    def __init__(self, replies):
        self.replies = list(replies)

    def profile(self, name):
        return self.Profile()

    def chat(self, profile, messages, tools):
        message = self.replies.pop(0)
        return SimpleNamespace(message=message)


class _Tools:
    def __init__(self):
        self.executed = []

    def ollama_schemas(self, names=None):
        return []

    def execute(self, name, arguments, context):
        self.executed.append(name)
        return {"ok": True}


def _call(name):
    return SimpleNamespace(
        function=SimpleNamespace(name=name, arguments={}),
    )


def _run(tmp_path, replies, user, procedure_session=None):
    tools = _Tools()
    result = AgentRuntime(
        _Models(replies),
        tools,
        SimpleNamespace(procedure_session=procedure_session),
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="engineer",
        messages=[{"role": "user", "content": user}],
    )
    return result, tools


def test_completion_claim_requires_a_verified_procedure(tmp_path):
    reply = SimpleNamespace(
        content="The procedure is complete.",
        tool_calls=[],
    )
    result, tools = _run(
        tmp_path,
        [reply],
        "Follow this studio procedure and confirm it is complete.",
    )

    assert result.stopped_reason == "procedure_not_verified"
    assert tools.executed == []


def test_completion_claim_is_allowed_when_every_required_row_is_verified(tmp_path):
    reply = SimpleNamespace(
        content="The procedure is complete.",
        tool_calls=[],
    )
    session = SimpleNamespace(status=lambda: {"complete": True})
    result, _tools = _run(
        tmp_path,
        [reply],
        "Follow this studio procedure and confirm it is complete.",
        procedure_session=session,
    )

    assert result.stopped_reason is None


def test_active_procedure_rejects_terminal_write_and_remote(tmp_path):
    calls = [
        _call("execute_terminal_command"),
        _call("write_workspace_file"),
        _call("remote_execute"),
    ]
    replies = [
        SimpleNamespace(content="", tool_calls=calls),
        SimpleNamespace(content="The current row is still open.", tool_calls=[]),
    ]
    session = SimpleNamespace(status=lambda: {"complete": False})
    result, tools = _run(
        tmp_path,
        replies,
        "Continue.",
        procedure_session=session,
    )

    assert tools.executed == []
    assert result.stopped_reason is None
