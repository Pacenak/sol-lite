from dataclasses import dataclass
from sol_lite.models.base import ModelCapabilities, ModelEndpoint
from sol_lite.models.profiles import load_profiles
from sol_lite.models.routing import ModelRouter

@dataclass
class Provider:
    locality: str
    trusted: bool = True
    def endpoint(self):
        return ModelEndpoint("test", "http://test", self.locality, self.trusted, ModelCapabilities(tool_calling=True, coding=True, reasoning=True))

def test_router_prefers_host():
    profiles = load_profiles({"profiles": {"engineer": {"model": "x", "capabilities": ["tool_calling"]}}})
    router = ModelRouter({"network": Provider("network"), "host": Provider("host")})
    assert router.candidates(profiles["engineer"])[0].locality == "host"

def test_network_requires_explicit_trust():
    profiles = load_profiles({"profiles": {"engineer": {"model": "x", "locality": "network", "capabilities": ["tool_calling"]}}})
    assert ModelRouter({"network": Provider("network", False)}).candidates(profiles["engineer"]) == []
