# Engineering execution fixes

The engineer prompt, tool declarations, and per-agent allowlist are retained.
Existing Git, Jira, Studio, remote, artifact, and skill integrations remain in place.

Task classification now recognizes repair, upgrade, configuration updates, and
file/test creation as engineering work. The existing local classification edits
also recognize documentation research and common validation commands. Tool
selection still intersects the agent allowlist and preserves integration gates.

The runtime now reads native tool calls and final text from dictionary responses
as well as Ollama message objects. Successful `edit_workspace_file` calls count
as completion evidence. Nonzero terminal exit codes are reported to the model as
failed results and cannot serve as successful validation evidence; the model can
then correct the problem and run another command within the existing round limit.

SearXNG now uses `searxng.engines` unless a tool call overrides it. An explicitly
empty override allows the server's default engines.

## Install and verify

From the repository root with Python 3.11 or later:

```text
python -m pip install -e ".[dev]"
python -m pytest tests/unit/test_task_fidelity.py tests/unit/test_searxng.py -q
python -m pytest -q
```

Use a writable pytest `--basetemp` outside any Git working tree if the default
temporary folder is restricted. A temporary workspace inside this repository can
trigger the shell's intentional Git-root selection prompt during tests.

The targeted tests passed. The full Windows sandbox run on 17 October 2026
reported 369 passed, 11 skipped, 9 failed, and 3 setup errors. Outstanding failures
include platform/environment restrictions, local Git transport, optional skill
resources, and help output; the full suite is not green. Live Ollama execution
has not been verified by these scripted regression tests.

## Enable research

The configured `http://10.10.40.10:30053/` server returned HTTP 403 for
`/search?q=SOL-Lite&format=json` during verification. `config/searxng.yaml` remains
disabled. Check the server's JSON search/access configuration and verify that
this endpoint returns JSON with a `results` array from the SOL-Lite host. Then
change only `searxng.enabled` to `true`, or set `SOL_SEARXNG_ENABLED=true`, and
restart SOL-Lite. Existing network permission checks still apply.

The discussion's remaining sections identify areas to investigate, but do not
specify a new persistence schema, replacement runtime, or deployment target.
Those components have not been replaced solely to match the outline.
