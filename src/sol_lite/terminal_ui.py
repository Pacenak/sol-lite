"""Rich terminal presentation layer for the SOL-Lite runtime."""
from __future__ import annotations

import time
from contextlib import contextmanager

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .ui.theme import SOL_LITE_THEME


class TerminalUI:
    """Presentation-only terminal UI.

    Runtime state and events remain outside this class. The UI renders that state
    using the Pacen / PLG colour system and deliberately keeps terminal output low-noise.
    """

    def __init__(self, *, console=None, verbose=False, debug=False):
        if console is None:
            self.console = Console(highlight=False, theme=SOL_LITE_THEME)
        else:
            self.console = console
            self.console.push_theme(SOL_LITE_THEME, inherit=True)
        self.verbose = verbose
        self.debug = debug
        self._live = None

    @property
    def live_active(self):
        return self._live is not None

    @staticmethod
    def _status_style(status: str) -> str:
        return {
            "WORKING": "sol_core_bold",
            "SLOW": "sol_warning",
            "STALLED": "sol_error",
            "COMPLETED": "sol_success",
            "FAILED": "sol_error",
            "CANCELLED": "sol_warning",
            "IDLE": "sol_dim",
        }.get(status, "sol_neutral")

    @staticmethod
    def _status_symbol(status: str) -> str:
        return {
            "WORKING": "◐",
            "SLOW": "◌",
            "STALLED": "⚠",
            "COMPLETED": "✓",
            "FAILED": "✕",
            "CANCELLED": "■",
            "IDLE": "○",
        }.get(status, "•")

    def _status_renderable(self, tracker):
        activity = tracker.snapshot()
        status = tracker.state()
        table = Table.grid(padding=(0, 1), expand=True)
        table.add_row(Text("Status", style="sol_dim"), Text(f"{self._status_symbol(status)} {status}", style=self._status_style(status)))
        table.add_row(Text("Phase", style="sol_dim"), Text(activity.phase, style="sol_neutral"))
        table.add_row(Text("Activity", style="sol_dim"), Text(activity.activity, style="sol_neutral"))
        if self.verbose:
            table.add_row(Text("Round", style="sol_dim"), Text(f"{activity.round_number}/{activity.max_rounds}", style="sol_core"))
            table.add_row(Text("Tools", style="sol_dim"), Text(f"{activity.tools_completed}/{activity.tool_calls}", style="sol_core"))
        if self.debug:
            now = time.monotonic()
            elapsed = 0 if activity.started_at is None else now - activity.started_at
            idle = 0 if activity.last_activity_at is None else now - activity.last_activity_at
            table.add_row(Text("Elapsed", style="sol_dim"), Text(f"{elapsed:.1f}s", style="sol_neutral"))
            table.add_row(Text("Idle", style="sol_dim"), Text(f"{idle:.1f}s", style="sol_neutral"))
            table.add_row(Text("Current tool", style="sol_dim"), Text(activity.current_tool or "none", style="sol_neutral"))
            table.add_row(Text("Current command", style="sol_dim"), Text(activity.current_command or "none", style="sol_neutral"))
            table.add_row(Text("Errors", style="sol_dim"), Text(str(activity.errors), style="sol_error" if activity.errors else "sol_neutral"))
        return Panel(
            table,
            title="Activity",
            title_align="left",
            border_style="sol_border",
            padding=(0, 1),
        )

    @contextmanager
    def live_status(self, tracker):
        live = Live(
            self._status_renderable(tracker),
            console=self.console,
            refresh_per_second=4,
            transient=True,
        )
        self._live = live
        live.start(refresh=True)
        try:
            yield live
        finally:
            live.stop()
            self._live = None

    def update_live_status(self, tracker):
        if self._live is not None:
            self._live.update(self._status_renderable(tracker), refresh=True)

    def banner(self, agent, workspace, model, shells):
        body = Text()
        body.append("SOL-Lite\n", style="sol_identity")
        body.append("Local-first multi-agent engineering runtime\n", style="sol_dim")
        body.append(f"{agent.name} · {workspace.name}\n", style="bold sol_neutral")
        body.append(str(workspace.root), style="sol_dim")
        body.append("\n")
        body.append("Model ", style="sol_dim")
        body.append(model, style="sol_core")
        body.append(" · Shells ", style="sol_dim")
        body.append(", ".join(shells) or "none", style="sol_neutral")
        self.console.print(Panel(body, border_style="sol_border", padding=(0, 1)))

    def user(self, content):
        self.console.print(
            Panel(
                Markdown(content),
                title=Text("You", style="sol_identity"),
                title_align="left",
                border_style="sol_identity_dim",
                padding=(0, 1),
            )
        )

    def agent(self, content, title="SOL Engineer"):
        self.console.print(
            Panel(
                Markdown(content),
                title=Text(title, style="sol_core_bold"),
                title_align="left",
                border_style="sol_border",
                padding=(0, 1),
            )
        )

    def status(self, tracker):
        self.console.print(self._status_renderable(tracker))

    def completed(self, result, elapsed):
        if result.cancelled:
            label = f"{self._status_symbol('CANCELLED')} Cancelled"
            style = "sol_warning"
        elif result.stopped_reason:
            label = f"{self._status_symbol('FAILED')} Failed"
            style = "sol_error"
        else:
            label = f"{self._status_symbol('COMPLETED')} Completed"
            style = "sol_success"
        extra = f" · {result.rounds} rounds · {result.tool_calls} tools · {elapsed:.1f}s"
        self.console.print(Text(label + extra, style=style))

    def approval(self, request):
        table = Table.grid(padding=(0, 1))
        table.add_row(Text("Operation", style="sol_dim"), Text(request.operation, style="sol_neutral"))
        table.add_row(Text("Target", style="sol_dim"), Text(request.target, style="sol_neutral"))
        table.add_row(Text("Arguments", style="sol_dim"), Text(repr(request.arguments), style="sol_neutral"))
        table.add_row(Text("Plan hash", style="sol_dim"), Text(request.plan_hash, style="sol_core"))
        self.console.print(
            Panel(
                table,
                title=Text("Approval Required", style="sol_command"),
                title_align="left",
                border_style="sol_command",
                padding=(0, 1),
            )
        )
        try:
            answer = self.console.input("[sol_command]Approve this exact operation? [y/N] ❯ [/sol_command]").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        return request.approval_id if answer in {"y", "yes"} else None

    def final_failure(self, reason):
        self.console.print(Panel(reason, title=Text("Agent stopped", style="sol_error"), border_style="sol_error"))

    def set_mode(self, mode):
        self.verbose = mode == "verbose"
        self.debug = mode == "debug"

    def print_help(self):
        table = Table("Command", "Purpose", border_style="sol_border", header_style="sol_core_bold")
        rows = [
            ("/help", "Show commands"),
            ("/agents", "List agents"),
            ("/use <agent>", "Select agent"),
            ("/new", "Start a new chat/session"),
            ("/workspace [path|number|new]", "Show or switch workspace"),
            ("/workspaces", "List named workspaces"),
            ("/sessions", "List active sessions"),
            ("/skills", "List/manage active skills"),
            ("/tools", "List tools"),
            ("/status", "Show current status"),
            ("/background <prompt>", "Run a task concurrently and keep chatting"),
            ("/tasks", "List background tasks"),
            ("/tasks cancel <id>", "Cancel a queued background task"),
            ("/verbose", "Expanded activity"),
            ("/debug", "Runtime diagnostics"),
            ("/normal", "Normal display"),
            ("/doctor", "Ollama/runtime diagnostics"),
            ("/quit", "Exit"),
        ]
        for command, purpose in rows:
            table.add_row(Text(command, style="sol_identity"), Text(purpose, style="sol_neutral"))
        self.console.print(table)

    def prompt(self, agent_id: str, workspace_name: str) -> str:
        """Return the styled input prompt while keeping user input separate from output."""
        return f"[sol_prompt]{agent_id}[/sol_prompt] [sol_dim]·[/sol_dim] [sol_core]{workspace_name}[/sol_core] [sol_prompt]❯[/sol_prompt] "

    def message(self, text, style="sol_neutral"):
        self.console.print(Text(text, style=style))
