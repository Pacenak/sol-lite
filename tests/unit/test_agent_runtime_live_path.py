from types import SimpleNamespace

from sol_lite.agents.runtime import AgentRuntime
from sol_lite.agents.status import StatusTracker
from sol_lite.core.event_bus import EventBus
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
                                name="inventory_workspace",
                                arguments={},
                            )
                        )
                    ],
                )
            )

        return SimpleNamespace(
            message=SimpleNamespace(
                content="Inventory completed.",
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
                    "name": "inventory_workspace",
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
        self.calls.append(
            (
                name,
                arguments,
            )
        )

        return {
            "root": "workspace",
            "count": 0,
            "files": [],
        }


def test_agent_runtime_executes_native_tool_call_and_returns_final_text(
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
    )

    result = runner.run(
        profile="engineer",
        messages=[
            {
                "role": "user",
                "content": "inventory",
            }
        ],
    )

    assert result.content == (
        "Inventory completed."
    )

    assert result.tool_calls == 1

    assert tools.calls == [
        (
            "inventory_workspace",
            {},
        )
    ]

    assert result.stopped_reason is None


def test_agent_runtime_emits_structured_events(
    tmp_path,
):
    tools = FakeTools()

    faults = FaultLog(
        tmp_path / "faults.json"
    )

    events = EventBus()
    seen = []

    events.subscribe(
        "agent.started",
        lambda event: seen.append(
            event.type
        ),
    )

    events.subscribe(
        "model.waiting",
        lambda event: seen.append(
            event.type
        ),
    )

    events.subscribe(
        "model.responded",
        lambda event: seen.append(
            event.type
        ),
    )

    events.subscribe(
        "tool.requested",
        lambda event: seen.append(
            event.type
        ),
    )

    events.subscribe(
        "tool.started",
        lambda event: seen.append(
            event.type
        ),
    )

    events.subscribe(
        "tool.completed",
        lambda event: seen.append(
            event.type
        ),
    )

    events.subscribe(
        "agent.completed",
        lambda event: seen.append(
            event.type
        ),
    )

    runner = AgentRuntime(
        FakeModels(),
        tools,
        object(),
        faults,
        status=StatusTracker(
            heartbeat_interval=0.01
        ),
        event_bus=events,
    )

    result = runner.run(
        profile="engineer",
        messages=[
            {
                "role": "user",
                "content": "inventory",
            }
        ],
    )

    assert result.stopped_reason is None

    assert seen == [
        "agent.started",
        "model.waiting",
        "model.responded",
        "tool.requested",
        "tool.started",
        "tool.completed",
        "model.waiting",
        "model.responded",
        "agent.completed",
    ]