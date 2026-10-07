"""Model profiles."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelProfile:
    name: str
    model: str
    temperature: float
    timeout_seconds: float

def load_profiles(config):
    return {
        name: ModelProfile(
            name=name, model=str(data["model"]),
            temperature=float(data.get("temperature", 0.2)),
            timeout_seconds=float(data.get("timeout_seconds", 300)),
        )
        for name, data in config.get("profiles", {}).items()
    }
