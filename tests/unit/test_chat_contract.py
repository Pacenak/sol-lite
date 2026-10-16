"""Golden tests for the unified ChatContract (no GPU / no live server)."""
from __future__ import annotations

import pytest

from sol_lite.models.contract import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    MockChatAdapter,
    ToolSpec,
    Usage,
    chat_request_from_provider_args,
    ollama_shaped_response,
    validate_chat_request,
)


def test_validate_chat_request_requires_model_and_messages():
    with pytest.raises(ValueError, match="model"):
        validate_chat_request(
            ChatRequest(model="", messages=(ChatMessage(role="user", content="hi"),))
        )
    with pytest.raises(ValueError, match="messages"):
        validate_chat_request(ChatRequest(model="m", messages=()))


def test_mock_adapter_returns_contract_response():
    adapter = MockChatAdapter(
        replies={
            "hello": ChatResponse(
                model="mock-1",
                message=ChatMessage(role="assistant", content="world"),
                finish_reason="stop",
                usage=Usage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
            )
        }
    )
    request = ChatRequest(
        model="mock-1",
        messages=(ChatMessage(role="user", content="hello"),),
        temperature=0.1,
    )
    response = adapter.complete(request)
    assert response.message.content == "world"
    assert response.usage is not None
    assert response.usage.total_tokens == 2


def test_mock_adapter_tool_call_fixture():
    adapter = MockChatAdapter(
        replies={
            "use tool": ChatResponse(
                model="mock-1",
                message=ChatMessage(
                    role="assistant",
                    content="",
                    tool_calls=(
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "list_workspace_directories",
                                "arguments": {"path": "."},
                            },
                        },
                    ),
                ),
                finish_reason="tool_calls",
            )
        }
    )
    response = adapter.complete(
        ChatRequest(
            model="mock-1",
            messages=(ChatMessage(role="user", content="use tool"),),
            tools=(
                ToolSpec(
                    name="list_workspace_directories",
                    description="list dirs",
                    parameters={"type": "object", "properties": {}},
                ),
            ),
        )
    )
    assert response.finish_reason == "tool_calls"
    assert response.message.tool_calls[0]["function"]["name"] == "list_workspace_directories"


def test_provider_args_round_trip_to_ollama_shape():
    request = chat_request_from_provider_args(
        model="qwen",
        messages=[{"role": "user", "content": "hi"}],
        tools=[{"type": "function", "function": {"name": "t", "parameters": {}}}],
        temperature=0.2,
        timeout=30.0,
    )
    response = ChatResponse(
        model="qwen",
        message=ChatMessage(role="assistant", content="ok"),
        finish_reason="stop",
    )
    shaped = ollama_shaped_response(response)
    assert shaped["message"]["role"] == "assistant"
    assert shaped["message"]["content"] == "ok"
    assert request.model == "qwen"
    assert request.tools[0].name == "t"
