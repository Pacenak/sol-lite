from sol_lite.agents.runtime import AgentRuntime


def test_function_markup_is_never_treated_as_native_tool_call():
    assert AgentRuntime._looks_like_tool_like_content("<function=repository_get_working_dir>\n</function>")
    assert AgentRuntime._looks_like_tool_like_content("<tool_call>foo</tool_call>")
