"""Model profiles."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelProfile:
    name: str
    model: str
    temperature: float
    timeout_seconds: float
    locality: str = "host"
    capabilities: tuple[str, ...] = ()


def load_profiles(config):
    return {
        name: ModelProfile(
            name=name,
            model=str(data["model"]),
            temperature=float(data.get("temperature", 0.2)),
            timeout_seconds=float(data.get("timeout_seconds", 300)),
            locality=str(data.get("locality", "host")),
            capabilities=tuple(data.get("capabilities", ())),
        )
        for name, data in config.get("profiles", {}).items()
    }
