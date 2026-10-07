"""Pacen / PLG-derived visual tokens for the SOL-Lite terminal UI."""
from __future__ import annotations

from dataclasses import dataclass

from rich.theme import Theme


@dataclass(frozen=True, slots=True)
class TerminalPalette:
    """Centralized terminal colours derived from the approved Pacen / PLG palette."""

    pacen_orange: str = "#d87818"
    live_sol_orange: str = "#e85d2c"
    noc_cyan: str = "#3ec6e0"
    core_cyan: str = "#2a8fa3"
    command_gold: str = "#f5a623"
    outpost_coral: str = "#e06c75"
    ai_purple: str = "#7c6a9a"

    # Semantic colours are deliberately separate from brand identity.
    success: str = "#5fb36a"
    warning: str = "#f0b429"
    error: str = "#d9534f"

    # Low-saturation neutrals should dominate the interface.
    neutral: str = "#c7c3bd"
    neutral_dim: str = "#817c74"
    neutral_border: str = "#5e5a54"
    neutral_panel: str = "#25231f"
    neutral_panel_alt: str = "#211f1b"


PALETTE = TerminalPalette()


SOL_LITE_THEME = Theme(
    {
        "sol_identity": f"bold {PALETTE.pacen_orange}",
        "sol_identity_dim": f"{PALETTE.pacen_orange}",
        "sol_core": f"{PALETTE.core_cyan}",
        "sol_core_bold": f"bold {PALETTE.core_cyan}",
        "sol_command": f"{PALETTE.command_gold}",
        "sol_success": f"bold {PALETTE.success}",
        "sol_warning": f"bold {PALETTE.warning}",
        "sol_error": f"bold {PALETTE.error}",
        "sol_neutral": f"{PALETTE.neutral}",
        "sol_dim": f"{PALETTE.neutral_dim}",
        "sol_border": PALETTE.neutral_border,
        "sol_prompt": f"bold {PALETTE.pacen_orange}",
        "sol_debug": f"{PALETTE.neutral_dim}",
        # Rich Markdown style hooks.
        "markdown.h1": f"bold {PALETTE.pacen_orange}",
        "markdown.h2": f"bold {PALETTE.core_cyan}",
        "markdown.h3": f"{PALETTE.core_cyan}",
        "markdown.item.bullet": PALETTE.core_cyan,
        "markdown.link": PALETTE.core_cyan,
        "markdown.code": f"{PALETTE.neutral}",
        "markdown.code_block": f"{PALETTE.neutral}",
        "markdown.block_quote": f"{PALETTE.neutral_dim}",
    }
)
