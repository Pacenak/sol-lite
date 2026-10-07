from types import SimpleNamespace

from sol_lite.agents.runtime import AgentRuntime
from sol_lite.agents.status import StatusTracker
from sol_lite.faults.log import FaultLog


class FakeProvider:
    def __init__(self, response): self.response = response
    def chat(self, **kwargs): return self.response

class FakeModels:
    class P:
        model = "fake"; temperature = 0.1; timeout_seconds = 10
    provider = None
    def profile(self, name): return self.P()

class EmptyTools:
    def ollama_schemas(self): return []
    def execute(self, *args): raise AssertionError("tool must not execute")

def test_raw_json_is_not_executed(tmp_path):
    response = SimpleNamespace(
        message=SimpleNamespace(
            content='{"name":"inventory_workspace","arguments":{}}',
            tool_calls=[],
        )
    )
    models = FakeModels()
    models.provider = FakeProvider(response)
    faults = FaultLog(tmp_path / "faults.json")
    runtime = AgentRuntime(models, EmptyTools(), None, faults, StatusTracker())
    result = runtime.run(profile="engineer", messages=[{"role": "user", "content": "test"}])
    assert result.content.startswith("{")
    assert any(f["code"] == "RAW_JSON_IN_CONTENT" for f in faults.get_all())
