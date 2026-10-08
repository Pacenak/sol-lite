from types import SimpleNamespace

from sol_lite.agents.runtime import AgentRuntime
from sol_lite.faults.log import FaultLog


def test_workspace_request_requires_native_workspace_tool(
    tmp_path,
):
    class Models:
        class Profile:
            model = "fake"
            temperature = 0.1
            timeout_seconds = 10

        def __init__(self):
            self.provider = SimpleNamespace(
                chat=lambda **kwargs: SimpleNamespace(
                    message=SimpleNamespace(
                        content=(
                            "I inspected the repository."
                        ),
                        tool_calls=[],
                    )
                )
            )

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

    class Tools:
        def ollama_schemas(self):
            return []

        def execute(
            self,
            name,
            arguments,
            context,
        ):
            raise AssertionError(
                "No native tool call should have been executed."
            )

    runner = AgentRuntime(
        Models(),
        Tools(),
        object(),
        FaultLog(
            tmp_path / "faults.json"
        ),
    )

    result = runner.run(
        profile="engineer",
        messages=[
            {
                "role": "user",
                "content": (
                    "Review this repository "
                    "and identify issues."
                ),
            }
        ],
    )

    assert result.stopped_reason == (
        "workspace_evidence_required"
    )