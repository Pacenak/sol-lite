"""Compatibility model manager backed by the model gateway."""
from .gateway import ModelGateway
from .health import diagnose_ollama
from .ollama import OllamaProvider
from .profiles import load_profiles


class ModelManager:
    def __init__(self, config, host):
        self.profiles = load_profiles(config)
        self.provider = OllamaProvider(host)
        self.gateway = ModelGateway({"ollama-local": self.provider}, self.profiles)

    def profile(self, name):
        return self.profiles[name]

    def chat(self, profile, messages, tools):
        return self.gateway.chat(profile, messages, tools)

    def diagnose(self):
        return diagnose_ollama(
            self.provider.host, [p.model for p in self.profiles.values()]
        ).data
