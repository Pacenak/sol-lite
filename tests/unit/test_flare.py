from io import StringIO

from rich.console import Console

from sol_lite.agents.flare import flare_note
from sol_lite.terminal_ui import TerminalUI
from tests.unit.test_shell_commands import _shell

PRECEDENCE = (
    "Facts, tool results, numbers, and the safety rules",
    "The work leads.",
    "You are still this agent.",
)


def test_each_agent_has_a_character_tone():
    notes = {
        "sol_pa": ("Murray", "yeah, look", "I'll pop that on the list"),
        "sol_business": ("Fred Dagg", "It's a bit of a muddle"),
        "sol_docs": ("Viago", "I do apologise"),
        "sol_engineer": ("Mark Watney", "Okay. So the problem is this."),
    }

    for agent_id, markers in notes.items():
        note = flare_note(agent_id)
        for marker in (*markers, *PRECEDENCE):
            assert marker in note, agent_id


def test_unknown_agent_gets_no_flare_note():
    assert flare_note("sol_unknown") == ""


def test_flare_is_off_until_the_session_command(tmp_path, capsys):
    shell = _shell(tmp_path)

    assert shell.flare is False
    assert "Flare is on" not in shell._system_prompt()
    assert shell.handle_command("/flare") == "handled"
    assert "Flare is off." in capsys.readouterr().out


def test_flare_on_adds_the_active_agents_tone(tmp_path, capsys):
    shell = _shell(tmp_path)

    assert shell.handle_command("/flare on") == "handled"
    assert "Flare is on for this sitting." in capsys.readouterr().out

    prompt = shell._system_prompt()
    assert "Mark Watney" in prompt
    assert "The work leads." in prompt
    assert "Murray" not in prompt

    shell.handle_command("/use sol_pa")
    prompt = shell._system_prompt()
    assert "yeah, look" in prompt
    assert "Mark Watney" not in prompt


def test_flare_off_removes_the_tone(tmp_path, capsys):
    shell = _shell(tmp_path)
    shell.handle_command("/flare on")
    capsys.readouterr()

    assert shell.handle_command("/flare off") == "handled"
    assert "Flare is off." in capsys.readouterr().out
    assert "Flare is on" not in shell._system_prompt()


def test_flare_rejects_an_unknown_argument(tmp_path, capsys):
    shell = _shell(tmp_path)
    assert shell.handle_command("/Flare bananas") == "handled"
    assert "Usage: /flare [on|off]" in capsys.readouterr().out
    assert shell.flare is False


def test_new_session_keeps_flare(tmp_path):
    shell = _shell(tmp_path)
    shell.handle_command("/flare on")
    shell._select_workspace = lambda path: shell.workspace

    shell._new_session()

    assert shell.flare is True
    assert "Mark Watney" in shell._system_prompt()


def test_help_lists_flare():
    console = Console(file=StringIO(), highlight=False)
    TerminalUI(console=console).print_help()
    output = console.file.getvalue()
    assert "/flare [on|off]" in output
    assert "character manner" in output
