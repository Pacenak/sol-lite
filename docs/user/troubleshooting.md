# Troubleshooting

## `No module named pytest` or `No module named ruff`

The active `.venv` does not contain development dependencies. Run the platform repair command rather than installing tools globally.

Windows:

```powershell
.\install\windows\repair.ps1
```

macOS:

```bash
./install/macos/repair.command
```

## Rich version check fails

Do not use `rich.__version__`. Use:

```text
python -c "import importlib.metadata; print(importlib.metadata.version('rich'))"
```

## Model emits `<function=...>`

This is model text, not a native tool call. SOL-Lite must not execute it. Inspect the runtime result and fault log.

## Agent says it ran a tool but audit has no native call

Treat the claim as unproven. Native structured tool calls and tool results are the authoritative evidence.

## Workspace appears wrong

Use `runtime_get_context` or `/workspace`. Do not infer the process working directory from Git state.
