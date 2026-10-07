# Model Failures

Use:

```text
python -m sol_lite diagnose
```

Check endpoint, API response and configured model names.

If the model emits tool-shaped ordinary text instead of a native structured call, the runtime must reject it rather than execute it.
