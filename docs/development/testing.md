# Testing Development Changes

Required baseline:

```text
python -m compileall -q src tests
python -m pytest -q
python -m ruff check src tests
```

Battle tests additionally cover security, repeat limits, raw JSON/tool-like model output and recovery.

Live testing is separate because it requires a running Ollama service and a configured model.
