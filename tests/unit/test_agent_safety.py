from types import SimpleNamespace

from sol_lite.agents.runtime import AgentRuntime
from sol_lite.agents.status import StatusTracker
from sol_lite.faults.log import FaultLog


class FakeProvider:
    def __init__(self, response):
        self.response = response

    def chat(self, **kwargs):
        return self.response


class FakeModels:
    class P:
        model = "fake"
        temperature = 0.1
        timeout_seconds = 10

    provider = None

    def profile(self, name):
        return self.P()

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


class EmptyTools:
    def ollama_schemas(self):
        return []

    def execute(self, *args):
        raise AssertionError(
            "tool must not execute"
        )


def test_raw_json_is_not_executed(
    tmp_path,
):
    response = SimpleNamespace(
        message=SimpleNamespace(
            content=(
                '{"name":"inventory_workspace",'
                '"arguments":{}}'
            ),
            tool_calls=[],
        )
    )

    models = FakeModels()

    models.provider = FakeProvider(
        response
    )

    faults = FaultLog(
        tmp_path / "faults.json"
    )

    runtime = AgentRuntime(
        models,
        EmptyTools(),
        None,
        faults,
        StatusTracker(),
    )

    result = runtime.run(
        profile="engineer",
        messages=[
            {
                "role": "user",
                "content": "test",
            }
        ],
    )

    assert result.content.startswith(
        "{"
    )

    assert any(
        fault["code"]
        == "RAW_JSON_IN_CONTENT"
        for fault in faults.get_all()
    )