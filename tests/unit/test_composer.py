"""Chat composer key mapping. Enter sends; Shift+Enter and Shift+Return edit."""
from sol_lite.ui.composer import (
    ENHANCED_KEY,
    SHIFT_PRESSED,
    VK_RETURN,
    Composer,
    EscapeDecoder,
    KeyAction,
    action_from_windows_key,
    cursor_cell,
    read_message,
)


def _type(actions: list[KeyAction]) -> str:
    editor = Composer()
    for action in actions:
        if editor.apply(action):
            return editor.text
    raise AssertionError("message was not sent")


def _decode(text: str) -> list[str]:
    decoder = EscapeDecoder()
    actions: list[KeyAction] = []
    for char in text:
        actions.extend(decoder.feed(char))
    actions.extend(decoder.flush())
    return [action.kind if action.kind != "insert" else action.text for action in actions]


def test_enter_sends_without_adding_a_break():
    assert _type([
        KeyAction("insert", "hello"),
        KeyAction("submit"),
    ]) == "hello"


def test_shift_enter_inserts_a_new_line_and_enter_sends():
    assert _type([
        KeyAction("insert", "hello"),
        KeyAction("newline"),
        KeyAction("insert", "world"),
        KeyAction("submit"),
    ]) == "hello\nworld"


def test_shift_return_inserts_a_paragraph():
    assert _type([
        KeyAction("insert", "hello"),
        KeyAction("paragraph"),
        KeyAction("insert", "world"),
        KeyAction("submit"),
    ]) == "hello\n\nworld"


def test_backspace_removes_a_line_break():
    editor = Composer()
    editor.apply(KeyAction("insert", "ab"))
    editor.apply(KeyAction("newline"))
    editor.apply(KeyAction("backspace"))
    assert editor.text == "ab"
    assert editor.cursor == 2


def test_windows_shift_enter_is_a_new_line_and_shift_return_is_a_paragraph():
    assert action_from_windows_key(VK_RETURN, SHIFT_PRESSED, "\r").kind == "newline"
    assert action_from_windows_key(VK_RETURN, SHIFT_PRESSED | ENHANCED_KEY, "\r").kind == "paragraph"
    assert action_from_windows_key(VK_RETURN, 0, "\r").kind == "submit"
    assert action_from_windows_key(VK_RETURN, ENHANCED_KEY, "\r").kind == "submit"
    assert action_from_windows_key(ord("A"), SHIFT_PRESSED, "A").kind == "insert"


def test_terminal_shift_enter_and_shift_return_sequences():
    assert _decode("hi\r") == ["h", "i", "submit"]
    assert _decode("\x1b[13;2u") == ["newline"]
    assert _decode("\x1b[57414;2u") == ["paragraph"]
    assert _decode("\x1b[27;2;13~") == ["newline"]
    assert _decode("\x1bOM") == ["submit"]
    assert _decode("\x1b\r") == ["newline"]


def test_cursor_stays_on_the_prompt_row_until_the_line_wraps():
    assert cursor_cell(10, "hi", 80) == (0, 12)
    assert cursor_cell(10, "hello\nnext", 80) == (1, 4)


def test_scripted_console_stays_on_ordinary_line_input():
    class Scripted:
        def input(self, prompt: str = "") -> str:
            assert "SOL" in prompt
            return "line one\n\nline two"

    assert read_message(Scripted(), "SOL ❯ ") == "line one\n\nline two"
