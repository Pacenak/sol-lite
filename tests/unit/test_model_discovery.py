from sol_lite.models.discovery import classify_locality, discover_configured_endpoints


def test_locality_classification():
    assert classify_locality("http://127.0.0.1:11434") == "host"
    assert classify_locality("http://10.10.81.20:11434") == "network"
    assert classify_locality("https://example.com") == "external"

def test_discovery_is_configuration_driven():
    result = discover_configured_endpoints({"provider": {"endpoint": "http://127.0.0.1:1"}}, timeout=0.01)
    assert len(result) == 1 and result[0].endpoint == "http://127.0.0.1:1"

def test_manager_does_not_create_unconfigured_provider():
    from sol_lite.models.manager import ModelManager
    manager = ModelManager({"provider": {"endpoint": "http://127.0.0.1:1", "trusted": True}, "profiles": {"x": {"model": "m"}}}, "http://127.0.0.1:1")
    assert set(manager.providers) == {"ollama-local"}
