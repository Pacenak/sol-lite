"""Provider-neutral model gateway with local-first routing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.exceptions import ModelError


@dataclass(frozen=True, slots=True)
class ModelRoute:
    provider_name: str
    model: str
    locality: str
    score: float


class ModelGateway:
    """Route inference requests by capability and locality.

    The gateway never silently changes locality. External providers must be
    explicitly configured and trusted; absent an eligible route, the request
    fails rather than leaving the local-first boundary.
    """

    def __init__(self, providers: dict[str, Any], profiles: dict[str, Any]):
        self.providers = dict(providers)
        self.profiles = dict(profiles)

    def profile(self, name):
        try:
            return self.profiles[name]
        except KeyError as exc:
            raise ModelError(f"Unknown model profile: {name}") from exc

    def routes(self, profile_name: str) -> list[ModelRoute]:
        profile = self.profile(profile_name)
        requested = getattr(profile, "locality", "host")
        preferred = {"host": 100.0, "network": 50.0, "external": 0.0}
        routes: list[ModelRoute] = []
        for name, provider in self.providers.items():
            endpoint = provider.endpoint()
            if endpoint.locality == "external" and requested != "external":
                continue
            score = preferred.get(endpoint.locality, -100.0)
            if endpoint.locality == requested:
                score += 100.0
            routes.append(ModelRoute(name, profile.model, endpoint.locality, score))
        return sorted(routes, key=lambda route: (-route.score, route.provider_name))

    def choose(self, profile_name: str) -> tuple[Any, Any]:
        routes = self.routes(profile_name)
        if not routes:
            raise ModelError(f"No eligible model provider for profile '{profile_name}'.")
        route = routes[0]
        return self.providers[route.provider_name], self.profile(profile_name)

    def chat(self, profile_name, messages, tools):
        provider, profile = self.choose(profile_name)
        return provider.chat(
            model=profile.model,
            messages=messages,
            tools=tools,
            temperature=profile.temperature,
            timeout=profile.timeout_seconds,
        )
