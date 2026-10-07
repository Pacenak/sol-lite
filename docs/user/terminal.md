# Terminal UI

SOL-Lite uses Rich for Markdown agent replies, panels and live activity.

Normal mode keeps runtime activity in one updating panel. It does not print heartbeat lines repeatedly.

Modes:

- `/normal` — concise activity.
- `/verbose` — rounds, tool counts and expanded activity.
- `/debug` — runtime diagnostics.

Agent replies are rendered as Markdown. User messages and agent replies are separated into panels.

Runtime semantics:

- `◐ WORKING`
- `◌ SLOW`
- `⚠ STALLED`
- `✓ COMPLETED`
- `✕ FAILED`
- `CANCELLED`

The visual palette is centralized in `src/sol_lite/ui/theme.py` and documented in `docs/design/colour-system.md`.
