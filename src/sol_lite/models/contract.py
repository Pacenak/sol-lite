"""Unified ChatContract for SOL-Lite model adapters.

Agents and the gateway keep provider-native chat() shapes for compatibility.
Adapters may use this contract internally and map to/from Ollama-shaped dicts
so protocol tests do not require a live GPU or Ollama.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: str
    content: str | None = None
    tool_calls: tuple[Any, ...] | None = None
    tool_call_id: str | None = None
    name: str | None = None
    tool_name: str | None = None


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Usage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class ChatRequest:
    model: str
    messages: tuple[ChatMessage, ...]
    tools: tuple[ToolSpec, ...] = ()
    temperature: float = 0.2
    timeout_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class ChatResponse:
    model: str
    message: ChatMessage
    finish_reason: str | None = None
    usage: Usage | None = None
    raw: Any = None


class ChatAdapter(ABC):
    """Internal adapter surface for contract-level golden tests."""

    @abstractmethod
    def complete(self, request: ChatRequest) -> ChatResponse:
        raise NotImplementedError


class MockChatAdapter(ChatAdapter):
    """Deterministic adapter keyed by the last user message content."""

    def __init__(self, replies: Mapping[str, ChatResponse]):
        self._replies = dict(replies)

    def complete(self, request: ChatRequest) -> ChatResponse:
        validate_chat_request(request)
        last_user = ""
        for message in request.messages:
            if message.role == "user" and message.content is not None:
                last_user = message.content
        try:
            return self._replies[last_user]
        except KeyError as exc:
            raise KeyError(f"No mock reply for user content {last_user!r}") from exc


def validate_chat_request(request: ChatRequest) -> None:
    if not request.model or not str(request.model).strip():
        raise ValueError("ChatRequest.model is required")
    if not request.messages:
        raise ValueError("ChatRequest.messages must be non-empty")


def _tool_spec_from_schema(item: Mapping[str, Any]) -> ToolSpec:
    if item.get("type") == "function" and isinstance(item.get("function"), Mapping):
        function = item["function"]
        return ToolSpec(
            name=str(function.get("name") or ""),
            description=str(function.get("description") or ""),
            parameters=dict(function.get("parameters") or {}),
        )
    return ToolSpec(
        name=str(item.get("name") or ""),
        description=str(item.get("description") or ""),
        parameters=dict(item.get("parameters") or {}),
    )


def chat_request_from_provider_args(
    *,
    model: str,
    messages: Sequence[Any],
    tools: Sequence[Any] | None,
    temperature: float,
    timeout: float | None,
) -> ChatRequest:
    normalized_messages: list[ChatMessage] = []
    for item in messages:
        if isinstance(item, ChatMessage):
            normalized_messages.append(item)
            continue
        if not isinstance(item, Mapping):
            raise TypeError(f"Unsupported message type: {type(item)!r}")
        tool_calls = item.get("tool_calls")
        normalized_messages.append(
            ChatMessage(
                role=str(item.get("role") or ""),
                content=item.get("content"),
                tool_calls=tuple(tool_calls) if tool_calls else None,
                tool_call_id=item.get("tool_call_id"),
                name=item.get("name"),
                tool_name=item.get("tool_name"),
            )
        )
    tool_specs = tuple(_tool_spec_from_schema(t) for t in (tools or ()) if isinstance(t, Mapping))
    return ChatRequest(
        model=str(model),
        messages=tuple(normalized_messages),
        tools=tool_specs,
        temperature=float(temperature),
        timeout_seconds=None if timeout is None else float(timeout),
    )


def ollama_shaped_response(response: ChatResponse) -> dict[str, Any]:
    """Map a contract response to the dict shape AgentRuntime already accepts."""
    message: dict[str, Any] = {
        "role": response.message.role or "assistant",
        "content": response.message.content or "",
    }
    if response.message.tool_calls:
        message["tool_calls"] = list(response.message.tool_calls)
    payload: dict[str, Any] = {
        "model": response.model,
        "message": message,
        "done": True,
    }
    if response.finish_reason is not None:
        payload["finish_reason"] = response.finish_reason
    if response.usage is not None:
        payload["usage"] = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
    return payload
