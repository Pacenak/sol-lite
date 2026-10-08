from dataclasses import dataclass

from sol_lite.models.gateway import ModelGateway
from sol_lite.models.profiles import load_profiles


@dataclass
class Provider:
    locality: str

    def endpoint(self):
        class Endpoint:
            def __init__(self, locality):
                self.locality = locality
        return Endpoint(self.locality)

    def chat(self, **kwargs):
        return kwargs


def test_profiles_default_to_host_locality():
    profiles = load_profiles({"profiles": {"engineer": {"model": "x"}}})
    assert profiles["engineer"].locality == "host"


def test_gateway_prefers_host_provider():
    profiles = load_profiles({"profiles": {"engineer": {"model": "x"}}})
    gateway = ModelGateway(
        {"network": Provider("network"), "host": Provider("host")}, profiles
    )
    provider, profile = gateway.choose("engineer")
    assert provider.locality == "host"
    assert profile.model == "x"
