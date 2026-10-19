import json
from pathlib import Path
from types import SimpleNamespace

from sol_lite.agents.runtime import _PROOF_TOOLS, AgentRuntime
from sol_lite.agents.task_fit import matching_tasks, permitted_tools
from sol_lite.agents.tool_allowlist import resolve_session_tools
from sol_lite.capabilities.risk import RiskClass
from sol_lite.faults.log import FaultLog
from sol_lite.mcp.security import MCPExposurePolicy
from sol_lite.tools import build_tool_registry
from sol_lite.workspace_pack.pack import Pack


def response(name=None, args=None, content=""):
    calls = (
        [] if not name else [SimpleNamespace(function=SimpleNamespace(name=name, arguments=args))]
    )
    return SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=calls))


class Models:
    def __init__(self, handler):
        self.handler = handler
        self.count = 0

    def profile(self, name):
        return SimpleNamespace(model="stub-local", temperature=0, timeout_seconds=5)

    def chat(self, profile, messages, tools):
        count = self.count
        self.count += 1
        return self.handler(count, messages, tools)


def test_real_registry_search_returns_exact_rendered_text(tool_context, tmp_path):
    ctx = tool_context
    ctx.agent_id = "sol_docs"
    (ctx.workspace_root / "facts.md").write_bytes(b"# Facts\r\nA precise documented statement.\r\n")
    emitted = []

    def chat(count, messages, tools):
        if count == 0:
            assert "search_knowledge_index" in {tool["function"]["name"] for tool in tools}
            return response("search_knowledge_index", {"query": "precise"})
        value = json.loads(messages[-1]["content"])
        emitted.append(value["results"][0]["rendered"])
        return response(content=emitted[0])

    registry = build_tool_registry()
    allowed = resolve_session_tools(
        Path(__file__).resolve().parents[2], ctx.agent_id, registry.names()
    )
    result = AgentRuntime(
        Models(chat), registry, ctx, FaultLog(tmp_path / "faults.json"), tool_names=allowed
    ).run(
        profile="reviewer",
        messages=[{"role": "user", "content": "What does the doc say about precise?"}],
    )
    assert result.content == emitted[0] and result.tool_calls == 1 and result.tool_failures == 0
    assert "**Lines:** 2-2" in result.content


def test_runtime_preview_apply_and_separate_approved_pack_log(tool_context, tmp_path):
    ctx = tool_context
    ctx.agent_id = "sol_pa"
    ctx.session_id = "indexing-e2e"
    (ctx.workspace_root / "inbox").mkdir()
    (ctx.workspace_root / "inbox/new.md").write_bytes(b"# Facts\nBrand new material\n")
    (ctx.workspace_root / "facts.md").write_bytes(b"# Facts\nOriginal information\n")
    pack = Pack(ctx.workspace_root)
    pack.minimal()
    pack.commit()
    base = {"source_file": "inbox/new.md", "target_file": "facts.md"}

    def chat(count, messages, tools):
        if count == 0:
            return response("consolidate_inbox_preview", base)
        value = json.loads(messages[-1]["content"])
        if count == 1:
            assert value["status"] == "ready"
            return response(
                "consolidate_inbox_apply",
                {
                    **base,
                    "expected_source_sha256": value["source_sha256"],
                    "expected_target_sha256": value["target_sha256"],
                    "plan": "Add the reviewed new material",
                    "approval_id": "",
                },
            )
        if count == 2:
            assert value["applied"]
            return response(
                "workspace_pack_append",
                {
                    "kind": "changelog",
                    "fields": {"changed": "Consolidated inbox additions", "files": ["facts.md"]},
                },
            )
        return response(content="Inbox additions applied and logged.")

    registry = build_tool_registry()
    approvals = []

    def approve(request):
        approvals.append(request.operation)
        return request.approval_id

    result = AgentRuntime(
        Models(chat),
        registry,
        ctx,
        FaultLog(tmp_path / "faults.json"),
        tool_names=registry.names(),
        approval_callback=approve,
    ).run(profile="fast", messages=[{"role": "user", "content": "Consolidate inbox"}])
    assert result.tool_failures == 0 and result.tool_calls == 3
    assert approvals == ["consolidate_inbox_apply", "workspace_pack_append"]
    assert (
        b"Original information\nBrand new material\n"
        in (ctx.workspace_root / "facts.md").read_bytes()
    )
    assert (
        "Consolidated inbox additions"
        in (ctx.workspace_root / "_workspace/CHANGELOG.md").read_text()
    )


def test_roles_task_fit_proof_and_mcp_policy():
    registry = build_tool_registry()
    root = Path(__file__).resolve().parents[2]
    for role in (
        "sol_pa",
        "sol_docs",
        "sol_engineer",
        "sol_business",
        "rick_prime",
        "sol_studio_admin",
    ):
        names = resolve_session_tools(root, role, registry.names())
        assert "search_knowledge_index" in names
        assert ("consolidate_inbox_apply" in names) == (role in {"sol_pa", "sol_docs"})
    assert "knowledge_retrieval" in matching_tasks("find in the docs")
    fitted = permitted_tools("merge inbox", frozenset(registry.names()))
    assert "consolidate_inbox_apply" in fitted and "google_email_read" not in fitted
    assert "consolidate_inbox_apply" in _PROOF_TOOLS
    assert MCPExposurePolicy().allows(registry.get("search_knowledge_index").as_capability())
    capability = registry.get("consolidate_inbox_apply").as_capability()
    assert not MCPExposurePolicy().allows(capability, authorized=True)
    policy = MCPExposurePolicy(allowed_risks=frozenset({RiskClass.MUTATING}))
    assert not policy.allows(capability)
    assert policy.allows(capability, authorized=True)
