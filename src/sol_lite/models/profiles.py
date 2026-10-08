from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelProfile:
    name: str
    model: str
    temperature: float
    timeout_seconds: float
    locality: str = "host"
    capabilities: tuple[str, ...] = ()
    provider: str | None = None
    fallback: bool = True

    def requires(self, capability: str) -> bool:
        return capability in self.capabilities


def load_profiles(config):
    profiles = {}
    for name, data in config.get("profiles", {}).items():
        if not isinstance(data, dict):
            raise TypeError(f"Model profile '{name}' must be a mapping.")
        profiles[name] = ModelProfile(
            name=name, model=str(data["model"]),
            temperature=float(data.get("temperature", 0.2)),
            timeout_seconds=float(data.get("timeout_seconds", 300)),
            locality=str(data.get("locality", "host")).casefold(),
            capabilities=tuple(str(v) for v in data.get("capabilities", ())),
            provider=str(data["provider"]) if data.get("provider") is not None else None,
            fallback=bool(data.get("fallback", True)),
        )
    return profiles
