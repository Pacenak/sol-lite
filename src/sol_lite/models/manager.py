from __future__ import annotations

from .discovery import discover_configured_endpoints
from .gateway import ModelGateway
from .health import diagnose_ollama
from .ollama import OllamaProvider
from .profiles import load_profiles

class ModelManager:
    def __init__(self, config, host):
        self.config = dict(config)
        self.profiles = load_profiles(self.config)
        self.provider = OllamaProvider(host)
        providers = {"ollama-local": self.provider}
        for endpoint in discover_configured_endpoints(self.config):
            if endpoint.name != "ollama-local" and endpoint.reachable:
                providers[endpoint.name] = OllamaProvider(endpoint.endpoint)
        self.providers = providers
        self.gateway = ModelGateway(self.providers, self.profiles)

    def profile(self, name): return self.profiles[name]
    def routes(self, name): return self.gateway.routes(name)
    def chat(self, profile, messages, tools): return self.gateway.chat(profile, messages, tools)
    def discover(self): return discover_configured_endpoints(self.config)
    def diagnose(self): return diagnose_ollama(self.provider.host, [p.model for p in self.profiles.values()]).data
