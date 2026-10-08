from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from ..core.exceptions import ModelError

_LOCALITY_RANK = {"host": 300, "network": 200, "external": 100}

@dataclass(frozen=True, slots=True)
class RouteCandidate:
    provider_name: str
    model: str
    locality: str
    score: int
    reasons: tuple[str, ...] = ()

class ModelRouter:
    def __init__(self, providers: dict[str, Any]):
        self.providers = dict(providers)

    def candidates(self, profile) -> list[RouteCandidate]:
        candidates = []
        for name, provider in self.providers.items():
            endpoint = provider.endpoint()
            locality = str(endpoint.locality).casefold()
            if locality not in _LOCALITY_RANK or (locality != "host" and not endpoint.trusted):
                continue
            if profile.provider and name != profile.provider:
                continue
            if profile.locality not in {"auto", "any"} and locality != profile.locality:
                continue
            missing = [c for c in profile.capabilities if not getattr(endpoint.capabilities, c, False)]
            if missing:
                continue
            score = _LOCALITY_RANK[locality] + (25 if endpoint.trusted else 0)
            reasons = [f"locality={locality}"]
            if endpoint.trusted: reasons.append("trusted")
            if profile.provider: score += 1000; reasons.append("profile-provider")
            candidates.append(RouteCandidate(name, profile.model, locality, score, tuple(reasons)))
        return sorted(candidates, key=lambda x: (-x.score, x.provider_name))

    def choose(self, profile):
        candidates = self.candidates(profile)
        if not candidates:
            raise ModelError(f"No eligible model provider for profile '{profile.name}'.")
        chosen = candidates[0]
        return self.providers[chosen.provider_name], chosen
