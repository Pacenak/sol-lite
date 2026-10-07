# macOS Installation

## Requirements

- macOS.
- Python 3.11 or newer available as `python3`.
- Ollama for agent operation.

## Install once

```bash
chmod +x scripts/*.command install/macos/*.command
./scripts/setup.command
```

The installer reuses an existing `.venv` and repairs dependencies instead of recreating it on every launch.

## Start normally

Open:

```text
~/Applications/SOL-Lite.app
```

The application opens a Terminal session for the SOL-Lite interactive runtime.

The repository-local launcher is also available:

```bash
./scripts/start.command
```

## Repair and uninstall

```bash
./install/macos/repair.command
./install/macos/uninstall.command
```

## Optional SearXNG web search

1. Configure your private SearXNG instance to return JSON from `/search`.
2. Set `SOL_SEARXNG_URL` in `.env`, or edit `config/searxng.yaml`.
3. Set `SOL_SEARXNG_ENABLED=true`.
4. Verify the endpoint with:

```bash
curl "http://YOUR-SEARXNG/search?q=SOL-Lite&format=json"
```

5. Start SOL-Lite. The agents will have the `searxng_search` tool. The default network policy still requires approval for the external request.

See `docs/integrations/searxng.md` for the complete configuration and troubleshooting procedure.

## Validate the installation

```bash
./scripts/battle-test.command
```

For a live Ollama smoke test:

```bash
.venv/bin/python -m sol_lite battle-test --live --agent sol_engineer
```


## Complete beginner sequence

Use [Full Setup and First Run](full-setup-first-run.md) for the full prerequisite → install → Ollama → SearXNG → workspace → first-agent → battle-test procedure.
