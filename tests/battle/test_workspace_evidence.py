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


def test_successful_repository_mutation_does_not_satisfy_inspection_requirement(
    tmp_path,
):
    from types import SimpleNamespace

    class Models:
        class Profile:
            model = "fake"
            temperature = 0.1
            timeout_seconds = 10

        def __init__(self):
            self.calls = 0

        def profile(self, name):
            return self.Profile()

        def chat(self, profile, messages, tools):
            self.calls += 1
            if self.calls == 1:
                message = SimpleNamespace(
                    content="",
                    tool_calls=[
                        SimpleNamespace(
                            function=SimpleNamespace(
                                name="repository_commit",
                                arguments={},
                            )
                        )
                    ],
                )
            else:
                message = SimpleNamespace(
                    content="I reviewed the repository.",
                    tool_calls=[],
                )
            return SimpleNamespace(message=message)

    class Tools:
        def ollama_schemas(self):
            return []

        def execute(self, name, arguments, context):
            return {"ok": True}

    result = AgentRuntime(
        Models(),
        Tools(),
        object(),
        FaultLog(tmp_path / "faults.json"),
    ).run(
        profile="engineer",
        messages=[
            {"role": "user", "content": "Review this repository."}
        ],
    )

    assert result.stopped_reason == "workspace_evidence_required"


def test_repository_mutations_and_terminal_commands_do_not_establish_evidence():
    from sol_lite.agents.runtime import AgentRuntime

    assert not AgentRuntime._workspace_tool_was_used({"repository_commit"})
    assert not AgentRuntime._workspace_tool_was_used({"repository_push"})
    assert not AgentRuntime._workspace_tool_was_used({"execute_terminal_command"})


def test_successful_empty_workspace_inspection_still_establishes_evidence():
    from sol_lite.agents.runtime import AgentRuntime

    assert AgentRuntime._workspace_tool_was_used({"inventory_workspace"})
    assert AgentRuntime._workspace_tool_was_used({"read_workspace_file"})
