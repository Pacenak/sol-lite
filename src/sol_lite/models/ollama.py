"""Ollama provider using the official Python client."""
from __future__ import annotations

from ..core.exceptions import ModelError
from .base import ModelCapabilities, ModelEndpoint, ModelProvider


class OllamaProvider(ModelProvider):
    def __init__(self, host):
        self.host = host.rstrip("/")
        self._clients = {}

    @staticmethod
    def _client_key(timeout):
        return None if timeout is None else float(timeout)

    def _client(self, timeout):
        key = self._client_key(timeout)
        if key not in self._clients:
            try:
                import ollama
            except ImportError as exc:
                raise ModelError("The 'ollama' Python package is not installed.") from exc
            kwargs = {"host": self.host}
            if timeout is not None:
                kwargs["timeout"] = timeout
            self._clients[key] = ollama.Client(**kwargs)
        return self._clients[key]

    def endpoint(self):
        locality = "host" if self.host in {"http://127.0.0.1:11434", "http://localhost:11434"} else "network"
        return ModelEndpoint(
            provider="ollama",
            endpoint=self.host,
            locality=locality,
            trusted=locality == "host",
            capabilities=ModelCapabilities(tool_calling=True, coding=True, reasoning=True),
        )

    def chat(self, model, messages, tools, temperature, timeout):
        try:
            return self._client(timeout).chat(
                model=model,
                messages=messages,
                tools=tools,
                options={"temperature": temperature},
            )
        except ModelError:
            raise
        except Exception as exc:
            raise ModelError(f"Ollama chat failed: {exc}") from exc
