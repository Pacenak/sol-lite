from sol_lite.agents.repeat_guard import RepeatToolGuard
from sol_lite.agents.status import StatusTracker


def test_repeat_limit():
    g = RepeatToolGuard(3)
    results = [g.record("read_workspace_file", {"path": "a"}) for _ in range(10)]
    assert results[2]
    assert all(results[2:])

def test_round_ceiling():
    s = StatusTracker()
    s.begin("WORKSPACE DISCOVERY", "test")
    assert s.snapshot().max_rounds == 40
