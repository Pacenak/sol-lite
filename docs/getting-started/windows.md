# Windows Installation

## Requirements

- Windows 10/11.
- Python 3.11 or newer available as `py` or `python`.
- Ollama is required for agent operation, but not for the offline unit test suite.

## Install once

From the SOL-Lite repository root:

```powershell
.\scripts\setup.bat
```

The installer is idempotent. If `.venv` already exists it is reused and dependencies are validated/repaired. It does not delete the environment as part of ordinary setup.

## Start normally

```powershell
.\launcher\windows\SOL-Lite.cmd
```

No venv activation or package installation is required on subsequent starts.

## Diagnose

```powershell
.\launcher\windows\SOL-Lite-Doctor.cmd
```

## Repair

```powershell
.\install\windows\repair.ps1
```

## Uninstall runtime

```powershell
.\install\windows\uninstall.ps1
```

Uninstall removes the runtime environment and installation state but intentionally retains source, configuration, skills and workspaces.

## Optional SearXNG web search

1. Configure your private SearXNG instance to return JSON from `/search`.
2. Set `SOL_SEARXNG_URL` in `.env`, or edit `config/searxng.yaml`.
3. Set `SOL_SEARXNG_ENABLED=true`.
4. Verify the endpoint with:

```powershell
curl.exe "http://YOUR-SEARXNG/search?q=SOL-Lite&format=json"
```

5. Start SOL-Lite. The agents will have the `searxng_search` tool. The default network policy still requires approval for the external request.

See `docs/integrations/searxng.md` for the complete configuration and troubleshooting procedure.

## Validate the installation

```powershell
.\scripts\battle-test.bat
```

For a live Ollama smoke test:

```powershell
.\.venv\Scripts\python.exe -m sol_lite battle-test --live --agent sol_engineer
```


## Complete beginner sequence

Use [Full Setup and First Run](full-setup-first-run.md) for the full prerequisite → install → Ollama → SearXNG → workspace → first-agent → battle-test procedure.
