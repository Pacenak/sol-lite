# Terminal UI Architecture

The terminal UI is presentation-only. It renders:

- banner
- user panel
- agent Markdown panel
- live activity/status panel
- approval panel
- completion/failure state

The Pacen/PLG colour system is centralized in `src/sol_lite/ui/theme.py`.
