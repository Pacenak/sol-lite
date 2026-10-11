from types import SimpleNamespace

from sol_lite.agents.runtime import AgentRuntime
from sol_lite.agents.status import StatusTracker
from sol_lite.core.exceptions import ApprovalRequired, ShellCommandInterrupt
from sol_lite.faults.log import FaultLog


class FakeProvider:
    def __init__(self):
        self.calls = 0

    def chat(self, **kwargs):
        self.calls += 1

        if self.calls == 1:
            return SimpleNamespace(
                message=SimpleNamespace(
                    content="",
                    tool_calls=[
                        SimpleNamespace(
                            function=SimpleNamespace(
                                name="mutate",
                                arguments={
                                    "plan": "change one"
                                },
                            )
                        )
                    ],
                )
            )

        return SimpleNamespace(
            message=SimpleNamespace(
                content="done",
                tool_calls=[],
            )
        )


class FakeModels:
    class Profile:
        model = "fake"
        temperature = 0.1
        timeout_seconds = 10

    def __init__(self):
        self.provider = FakeProvider()

    def profile(self, name):
        return self.Profile()

    def chat(
        self,
        profile,
        messages,
        tools,
    ):
        profile_obj = self.profile(profile)

        return self.provider.chat(
            model=profile_obj.model,
            messages=messages,
            tools=tools,
            temperature=profile_obj.temperature,
            timeout=profile_obj.timeout_seconds,
        )


class FakeTools:
    def __init__(self):
        self.calls = []

    def ollama_schemas(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "mutate",
                    "description": "test",
                    "parameters": {},
                },
            }
        ]

    def execute(
        self,
        name,
        arguments,
        context,
    ):
        self.calls.append(arguments)

        if "approval_id" not in arguments:
            raise ApprovalRequired(
                "approval",
                request=SimpleNamespace(
                    approval_id="a1"
                ),
            )

        return {
            "ok": True
        }


def test_agent_runtime_can_use_exact_approval_callback(
    tmp_path,
):
    tools = FakeTools()

    faults = FaultLog(
        tmp_path / "faults.json"
    )

    runner = AgentRuntime(
        FakeModels(),
        tools,
        object(),
        faults,
        status=StatusTracker(
            heartbeat_interval=0.01
        ),
        approval_callback=(
            lambda request:
            request.approval_id
        ),
    )

    result = runner.run(
        profile="engineer",
        messages=[
            {
                "role": "user",
                "content": "go",
            }
        ],
    )

    assert result.content == "done"

    assert tools.calls == [
        {
            "plan": "change one"
        },
        {
            "plan": "change one",
            "approval_id": "a1",
        },
    ]


def test_slash_command_during_approval_cancels_before_another_model_turn(tmp_path):
    def interrupt(_request):
        raise ShellCommandInterrupt("/settings")

    tools = FakeTools()
    runner = AgentRuntime(
        FakeModels(),
        tools,
        object(),
        FaultLog(tmp_path / "faults.json"),
        approval_callback=interrupt,
    )
    result = runner.run(
        profile="engineer",
        messages=[{"role": "user", "content": "go"}],
    )
    assert result.cancelled is True
    assert result.shell_command == "/settings"
    assert result.stopped_reason == "shell_command"
    assert runner.model_manager.provider.calls == 1
    assert len(tools.calls) == 1


def test_approval_callback_error_does_not_stop_the_turn(tmp_path):
    def boom(_request):
        raise RuntimeError("prompt failed")

    tools = FakeTools()
    runner = AgentRuntime(
        FakeModels(),
        tools,
        object(),
        FaultLog(tmp_path / "faults.json"),
        approval_callback=boom,
    )
    result = runner.run(
        profile="engineer",
        messages=[{"role": "user", "content": "go"}],
    )
    assert result.stopped_reason is None
    assert result.content == "done"


def test_second_approval_requirement_stays_inside_the_tool_loop(tmp_path):
    class AlwaysRequired(FakeTools):
        def execute(self, name, arguments, context):
            self.calls.append(arguments)
            raise ApprovalRequired(
                "Approval required for jira_status targeting Jira.",
                request=SimpleNamespace(approval_id="a1"),
            )

    tools = AlwaysRequired()
    runner = AgentRuntime(
        FakeModels(),
        tools,
        object(),
        FaultLog(tmp_path / "faults.json"),
        approval_callback=lambda request: request.approval_id,
    )
    result = runner.run(
        profile="engineer",
        messages=[{"role": "user", "content": "go"}],
    )
    assert result.stopped_reason is None
    assert result.content == "done"
    assert len(tools.calls) == 2