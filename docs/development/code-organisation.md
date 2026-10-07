# Code Organisation

Keep boundaries explicit:

- `app.py` parses commands and composes top-level execution.
- `bootstrap.py` composes runtime services.
- `core/` owns lifecycle/session/task primitives.
- `agents/` owns agent behaviour and the model/tool loop.
- `tools/` owns executable capabilities.
- `permissions/` owns authorization and approval.
- `security/` owns containment and command classification.
- `skills/` owns skill discovery and provenance.
- `terminal_ui.py` owns rendering only.

Do not move terminal strings into the runtime to solve a UI problem.
