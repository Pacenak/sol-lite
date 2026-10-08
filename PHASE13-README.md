# SOL-Lite Phase 13 — Provider Discovery and Model Routing

Phase 13 adds explicit provider discovery and capability-aware, local-first routing.

- Host-local Ollama is the default.
- Only explicitly configured network endpoints are probed.
- No arbitrary LAN scanning is performed.
- Non-host providers require explicit trust.
- Profiles can constrain locality and required capabilities.
- Credentials are not handled by discovery.

Validate with:

    python -m pytest -q tests/unit/test_model_gateway.py tests/unit/test_model_discovery.py tests/unit/test_model_routing.py
    python -m compileall -q src tests
    python -m pytest -q
    python -m ruff check src tests
