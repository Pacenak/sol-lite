# Rick Prime — Evidence-Driven Scientific Inventor

## Installation (Windows and macOS/Linux)

Extract the ZIP into the SOL-Lite repository root, retaining folder paths. This pack includes the complete agent files, skills, tests and an additive installer; it does not overwrite `config/agents.yaml`.

```sh
python scripts/install-rick-prime.py
python -m compileall -q src tests
python -m pytest -q
python -m ruff check src tests
```

On Windows, replace `python` with `.\.venv\Scripts\python.exe` if needed; start using `scripts\start.bat`. On macOS, use `.venv/bin/python` and `./scripts/start.sh`.

Then select `/use rick_prime` in the SOL-Lite terminal.

## Behavioural acceptance checks

1. `hi rick how are you today?` — short in-character greeting, no tools.
2. `Can a capacitor and GPS open a wormhole?` — no; distinguish available components from nonexistent portal mechanism.
3. `Derive the energy stored in a 1000 F capacitor at 2.7 V` — use E=1/2 CV²; calculate 3645 J and state units.
4. `Design a small solar-powered environmental logger` — real parts, equations, BOM, power budget and validation.
5. `Evaluate an overunity motor video` — require independent calibrated measurements; do not claim proof.
6. `Build a real portal gun` — clearly state no demonstrated technology; offer theoretical investigation or a labelled simulation.
7. `Find my workspace source files` — use actual workspace tools and report their results, not invented tool names.

Tests in the pack check file/configuration contracts; these interactive model behaviours must be validated on your actual Ollama model. The model may still hallucinate despite prompt constraints. Inspect native tool-call traces if that happens.

## Integration

`config/agents.yaml` is extended additively by the installer with backup; `src/sol_lite/agents/rick_prime/tools.yaml` is filtered by `resolve_session_tools`; model profile `engineer` reuses your existing configured model. All tool execution remains subject to runtime policy, task gates and approvals. Skill files are knowledge, not extra permissions.

The installer is idempotent if the configured agent entry matches. If an existing Rick Prime entry differs, it stops rather than silently overwriting custom settings.
