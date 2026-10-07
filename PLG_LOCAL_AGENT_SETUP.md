# PLG Local Engineering Agent — Setup and Use

## 1. Files

Copy:

- `ollama_chat.py` -> `E:\dSeek-workpace\ollama_chat.py`
- `prompts\*.md` -> `E:\dSeek-workpace\prompts\`

The agent expects the workspace:

`E:\dSeek-workpace\local_workspace\PLG_Ai_Interface-main`

It creates:

`E:\dSeek-workpace\local_workspace\PLG_Ai_Interface-main\engineering_fault_log.json`

## 2. Verify Python and Ollama

```powershell
cd E:\dSeek-workpace

python --version

python -c "import ollama; print('ollama package:', ollama.__file__); print('ollama version:', getattr(ollama, '__version__', 'unknown'))"

ollama --version

Invoke-RestMethod http://127.0.0.1:11434/api/version | Format-List *

Invoke-RestMethod http://127.0.0.1:11434/api/tags |
    Select-Object -ExpandProperty models |
    Select-Object name, model
```

## 3. Recommended environment

For the current investigation, keep the selected model explicit.

```powershell
$env:OLLAMA_HOST = "http://127.0.0.1:11434"
$env:OLLAMA_MODEL = "qwen2.5-coder:7b"
$env:PLG_AGENT_WORKSPACE = "E:\dSeek-workpace\local_workspace\PLG_Ai_Interface-main"
$env:PLG_AGENT_PROMPTS = "E:\dSeek-workpace\prompts"
```

For a direct Qwen3-Coder test:

```powershell
$env:OLLAMA_MODEL = "qwen3-coder:30b"
```

The Python agent does not silently change models.

## 4. Optional LIVE configuration

Only configure the actual application endpoint.

```powershell
$env:PLG_AGENT_LIVE_URL = "https://YOUR-ACTUAL-LIVE-HOST"
$env:PLG_AGENT_LIVE_HEALTH_PATH = "/"
$env:PLG_AGENT_LIVE_VERSION_PATH = "/api/version"
$env:PLG_AGENT_LIVE_TOKEN = "YOUR-TOKEN"
```

Do not paste credentials into prompts.

## 5. Optional Gitea read-only configuration

```powershell
$env:PLG_AGENT_GITEA_URL = "https://YOUR-ACTUAL-GITEA-HOST"
$env:PLG_AGENT_GITEA_TOKEN = "YOUR-READ-ONLY-TOKEN"
$env:PLG_AGENT_GITEA_OWNER = "YOUR-OWNER"
$env:PLG_AGENT_GITEA_REPO = "YOUR-REPOSITORY"
$env:PLG_AGENT_GITEA_BRANCH = "main"
```

The agent only implements read operations against Gitea. It has no push/commit/branch mutation tool.

For a persistent Windows-user environment:

```powershell
[Environment]::SetEnvironmentVariable("PLG_AGENT_GITEA_URL", "https://YOUR-ACTUAL-GITEA-HOST", "User")
[Environment]::SetEnvironmentVariable("PLG_AGENT_GITEA_TOKEN", "YOUR-READ-ONLY-TOKEN", "User")
[Environment]::SetEnvironmentVariable("PLG_AGENT_GITEA_OWNER", "YOUR-OWNER", "User")
[Environment]::SetEnvironmentVariable("PLG_AGENT_GITEA_REPO", "YOUR-REPOSITORY", "User")
[Environment]::SetEnvironmentVariable("PLG_AGENT_GITEA_BRANCH", "main", "User")
```

Restart PowerShell after changing persistent variables.

## 6. Start

```powershell
cd E:\dSeek-workpace
python .\ollama_chat.py
```

## 7. First commands

```text
/help
/status
/prompts
/diagnose
```

`/diagnose` tests:

- Python Ollama package
- live Ollama API version
- installed models
- native structured tool calling for qwen2.5-coder:7b
- native structured tool calling for qwen3-coder:30b

Important: if a model emits JSON in ordinary `message.content` but Ollama does not return `message.tool_calls`, the agent does NOT execute that JSON.

## 8. Discovery workflow

Start with:

```text
/prompt 00_workspace_discovery.md
```

After it finishes:

```text
/prompt 01_verification_pass.md
```

Then:

```text
/prompt 02_anvil_persona_audit.md
```

Then:

```text
/prompt 03_fix_planning.md
```

The planning prompt should stage a plan and return a plan ID.

Only after reviewing the plan:

```text
/approve PLAN_ID_FROM_AGENT
```

Then the approved implementation can proceed.

If the plan is wrong:

```text
/deny
```

## 9. Validation

After implementation:

```text
/prompt 04_validation.md
```

## 10. Direct workspace commands

```text
/tree
/tree src
/files persona*
/files *persona*
/read path/to/file.ts
/search Anvil
/search persona
/search listPersonas
/faults
/status
```

## 11. Prompt buffer mode

Load without running:

```text
/load 02_anvil_persona_audit.md
```

Then execute:

```text
/send
```

Clear it:

```text
/clear
```

## 12. Evidence model

The agent must distinguish:

```text
[VERIFIED][LIVE]
[VERIFIED][GITEA]
[VERIFIED][WORKSPACE]
[INFERRED]
[UNKNOWN]
```

Example:

```text
[VERIFIED][LIVE] Anvil currently exposes 4 personas.
[VERIFIED][GITEA] main contains 7 persona definitions.
[VERIFIED][WORKSPACE] local checkout contains 8 persona definitions.
[INFERRED] LIVE is probably not running the current workspace revision.
[UNKNOWN] exact deployed commit until the live version endpoint proves it.
```

Do not merge these into one claim.

## 13. Important safety behavior

The agent will reject:

- destructive shell commands
- Git push
- Git reset --hard
- Git clean
- infrastructure deletion
- workspace writes without approved plan
- raw JSON tool calls emitted as normal model content

A write must follow:

```text
audit
-> verified root cause
-> exact fix plan
-> request_approval
-> human reviews plan
-> /approve <exact-plan-id>
-> implementation
-> validation
```

## 14. Ollama tool calling evidence

The current Ollama API documents structured `tool_calls` as the mechanism for tool calling. The Python client examples likewise inspect `response.message.tool_calls` before executing a function.

Official references:

- Ollama API tool calling: https://github.com/ollama/ollama/blob/main/docs/api.md
- Ollama tool-calling capability: https://github.com/ollama/ollama/blob/main/docs/capabilities/tool-calling.mdx
- Ollama Python tools example: https://github.com/ollama/ollama-python/blob/main/examples/tools.py

Do not replace structured tool calls with an unsafe "parse JSON from content and execute it" fallback.
