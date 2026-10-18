"""Scripted model plus real registry, guards, approvals and disk writes."""

from types import SimpleNamespace

from sol_lite.agents.runtime import AgentRuntime
from sol_lite.faults.log import FaultLog
from sol_lite.tools import build_tool_registry
from sol_lite.workspace_pack.pack import QUESTIONS


def test_model_tool_intake_initialization_and_orientation(tool_context, tmp_path):
    ctx = tool_context
    ctx.agent_id = "sol_pa"
    ctx.session_id = "workspace-pack-e2e"
    operations = (
        [("workspace_pack_status", {})]
        + [
            (
                "workspace_pack_intake",
                {"question_id": key, "answer": f"Recorded user answer: {key}"},
            )
            for key in QUESTIONS
        ]
        + [("workspace_pack_init", {})]
    )

    class Models:
        def __init__(self):
            self.calls = 0
            self.messages = []

        def profile(self, name):
            return SimpleNamespace(model="stub-local-model", temperature=0, timeout_seconds=5)

        def chat(self, profile, messages, tools):
            self.messages = messages
            index = self.calls
            self.calls += 1
            if index < len(operations):
                name, arguments = operations[index]
                assert name in {row["function"]["name"] for row in tools}
                return SimpleNamespace(
                    message=SimpleNamespace(
                        content="",
                        tool_calls=[
                            SimpleNamespace(
                                function=SimpleNamespace(name=name, arguments=arguments)
                            )
                        ],
                    )
                )
            return SimpleNamespace(message=SimpleNamespace(content="Pack created.", tool_calls=[]))

    models = Models()
    registry = build_tool_registry()
    approvals = []

    def approve(request):
        approvals.append(request)
        return request.approval_id

    runtime = AgentRuntime(
        models,
        registry,
        ctx,
        FaultLog(tmp_path / "runtime-faults.json"),
        max_tool_rounds=14,
        approval_callback=approve,
        tool_names=registry.names(),
    )
    result = runtime.run(
        profile="fast", messages=[{"role": "user", "content": "Set up the workspace starter pack"}]
    )
    assert result.tool_failures == 0
    assert result.tool_calls == 9
    assert len(approvals) == 8
    assert (ctx.workspace_root / "_workspace/PLAN.md").is_file()
    assert "Recorded user answer: purpose" in (
        ctx.workspace_root / "_workspace/README.md"
    ).read_text(encoding="utf-8")
    # A later turn receives pack data before asking the model for any work.
    models.calls = len(operations)
    runtime.run(
        profile="fast",
        messages=[
            {"role": "system", "content": "Trusted policy"},
            {"role": "user", "content": "Hello"},
        ],
    )
    assert models.messages[0] == {"role": "system", "content": "Trusted policy"}
    material = models.messages[1]
    assert material["role"] == "user" and "UNTRUSTED" in material["content"]
    assert material["content"].index("_workspace/INDEX.md") < material["content"].index(
        "_workspace/README.md"
    )
