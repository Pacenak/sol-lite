from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.exceptions import ModelError

_LOCALITY_RANK = {
    "host": 300,
    "network": 200,
    "external": 100,
}


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
            locality = str(
                endpoint.locality
            ).casefold()

            if locality not in _LOCALITY_RANK:
                continue

            # Host-local endpoints are trusted by locality when a
            # lightweight endpoint implementation does not expose an
            # explicit trust attribute. Network and external endpoints
            # remain untrusted unless they explicitly opt in.
            trusted = bool(
                getattr(
                    endpoint,
                    "trusted",
                    locality == "host",
                )
            )

            if locality != "host" and not trusted:
                continue

            if profile.provider and name != profile.provider:
                continue

            if (
                profile.locality not in {"auto", "any"}
                and locality != profile.locality
            ):
                continue

            capabilities = getattr(
                endpoint,
                "capabilities",
                None,
            )

            missing = [
                capability
                for capability in profile.capabilities
                if not getattr(
                    capabilities,
                    capability,
                    False,
                )
            ]

            if missing:
                continue

            score = _LOCALITY_RANK[locality]

            if trusted:
                score += 25

            reasons = [
                f"locality={locality}",
            ]

            if trusted:
                reasons.append("trusted")

            if profile.provider:
                score += 1000
                reasons.append("profile-provider")

            candidates.append(
                RouteCandidate(
                    name,
                    profile.model,
                    locality,
                    score,
                    tuple(reasons),
                )
            )

        return sorted(
            candidates,
            key=lambda candidate: (
                -candidate.score,
                candidate.provider_name,
            ),
        )

    def choose(self, profile):
        candidates = self.candidates(profile)

        if not candidates:
            raise ModelError(
                f"No eligible model provider for profile "
                f"'{profile.name}'."
            )

        chosen = candidates[0]

        return (
            self.providers[
                chosen.provider_name
            ],
            chosen,
        )