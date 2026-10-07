"""Model provider interface."""

from abc import ABC, abstractmethod


class ModelProvider(ABC):
    @abstractmethod
    def chat(self, model, messages, tools, temperature, timeout):
        raise NotImplementedError
