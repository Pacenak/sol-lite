from sol_lite.agents.status import StatusTracker


def test_status_line():
    s = StatusTracker()
    s.begin("ROOT CAUSE INVESTIGATION", "reading files")
    s.set_round(2)
    s.tool_start("read_workspace_file")
    s.tool_complete("read_workspace_file")
    line = s.format_line()
    assert "ROOT CAUSE INVESTIGATION" in line
    assert "round 2/40" not in line
