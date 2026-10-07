from sol_lite.agents.repeat_guard import RepeatToolGuard


def test_repeat_detection():
    g = RepeatToolGuard(3)
    assert not g.record("tool", {"a": 1})
    assert not g.record("tool", {"a": 1})
    assert g.record("tool", {"a": 1})
