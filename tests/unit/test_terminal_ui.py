from io import StringIO

from rich.console import Console

from sol_lite.terminal_ui import TerminalUI
from sol_lite.ui.theme import PALETTE


def test_terminal_palette_matches_pacen_plg_reference():
    assert PALETTE.pacen_orange == "#d87818"
    assert PALETTE.core_cyan == "#2a8fa3"
    assert PALETTE.noc_cyan == "#3ec6e0"
    assert PALETTE.command_gold == "#f5a623"
    assert PALETTE.outpost_coral == "#e06c75"
    assert PALETTE.ai_purple == "#7c6a9a"


def test_terminal_ui_applies_theme_to_supplied_console():
    console = Console(file=StringIO(), highlight=False)
    ui = TerminalUI(console=console)
    ui.print_help()
    ui.message("theme smoke")
    assert "Command" in console.file.getvalue()


def test_terminal_ui_renders_user_and_agent_panels_with_rich_15():
    console = Console(file=StringIO(), highlight=False)
    ui = TerminalUI(console=console)
    ui.user("Hello **SOL-Lite**")
    ui.agent("Agent response")
    ui.final_failure("test failure")
    output = console.file.getvalue()
    assert "You" in output
    assert "SOL Engineer" in output
    assert "Agent stopped" in output
