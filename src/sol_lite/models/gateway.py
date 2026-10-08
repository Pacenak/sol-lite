from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.exceptions import ModelError
from .routing import ModelRouter


@dataclass(frozen=True, slots=True)
class ModelRoute:
    provider_name: str
    model: str
    locality: str
    score: float
    reasons: tuple[str, ...] = ()

class ModelGateway:
    def __init__(self, providers: dict[str, Any], profiles: dict[str, Any]):
        self.providers = dict(providers)
        self.profiles = dict(profiles)
        self.router = ModelRouter(self.providers)

    def profile(self, name):
        try: return self.profiles[name]
        except KeyError as exc: raise ModelError(f"Unknown model profile: {name}") from exc

    def routes(self, profile_name: str) -> list[ModelRoute]:
        return [ModelRoute(x.provider_name, x.model, x.locality, float(x.score), x.reasons) for x in self.router.candidates(self.profile(profile_name))]

    def choose(self, profile_name: str):
        profile = self.profile(profile_name)
        provider, _ = self.router.choose(profile)
        return provider, profile

    def chat(self, profile_name, messages, tools):
        provider, profile = self.choose(profile_name)
        return provider.chat(model=profile.model, messages=messages, tools=tools, temperature=profile.temperature, timeout=profile.timeout_seconds)
