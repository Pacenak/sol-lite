from sol_lite.agents.runtime import AgentRuntime


def test_raw_json_classifier():
    assert AgentRuntime._looks_like_raw_tool_json(
        '{"name":"inventory_workspace","arguments":{}}'
    )
    assert not AgentRuntime._looks_like_raw_tool_json(
        'Use {"name":"inventory_workspace"} as an example.'
    )
