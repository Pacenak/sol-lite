"""Model manager."""

from .health import diagnose_ollama
from .ollama import OllamaProvider
from .profiles import load_profiles


class ModelManager:
    def __init__(self, config, host):
        self.profiles = load_profiles(config)
        self.provider = OllamaProvider(host)

    def profile(self, name):
        return self.profiles[name]

    def diagnose(self):
        return diagnose_ollama(
            self.provider.host, [p.model for p in self.profiles.values()]
        ).data
