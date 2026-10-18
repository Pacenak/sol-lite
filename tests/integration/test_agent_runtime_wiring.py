from sol_lite.bootstrap import bootstrap
from sol_lite.platform.windows import WindowsAdapter


def test_bootstrap_wires_agent_harness(monkeypatch):
    monkeypatch.setattr("sol_lite.bootstrap.get_platform_adapter", lambda: WindowsAdapter())
    runtime = bootstrap()
    assert runtime.agents.names() == ["rick_prime", "sol_business", "sol_docs", "sol_engineer", "sol_pa"]
    assert "inventory_workspace" in runtime.tools.names()
    assert "remote_execute" in runtime.tools.names()
    assert runtime.tool_context.remote_manager is not None
    assert runtime.models.profile("engineer").model == "qwen3-coder:30b"
