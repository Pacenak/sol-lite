"""Ollama provider using the official Python client."""

from ..core.exceptions import ModelError
from .base import ModelProvider


class OllamaProvider(ModelProvider):
    def __init__(self, host):
        self.host = host.rstrip("/")
        self.client = None

    def _client(self):
        if self.client is None:
            try:
                import ollama
            except ImportError as exc:
                raise ModelError("The 'ollama' Python package is not installed.") from exc
            self.client = ollama.Client(host=self.host)
        return self.client

    def chat(self, model, messages, tools, temperature, timeout):
        try:
            return self._client().chat(
                model=model, messages=messages, tools=tools,
                options={"temperature": temperature},
            )
        except ModelError:
            raise
        except Exception as exc:
            raise ModelError(f"Ollama chat failed: {exc}") from exc
