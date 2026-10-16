"""Chat composer. Enter sends. Shift+Enter inserts a line. Shift+Return inserts a paragraph."""
from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from io import StringIO
from typing import Any, TextIO

from rich.console import Console
from rich.text import Text

from .theme import SOL_LITE_THEME

SHIFT_PRESSED = 0x0010
ENHANCED_KEY = 0x0100
CTRL_PRESSED = 0x0004 | 0x0008
VK_RETURN = 0x0D
VK_BACK = 0x08
VK_TAB = 0x09
VK_HOME = 0x24
VK_END = 0x23
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_DELETE = 0x2E


@dataclass(frozen=True)
class KeyAction:
    kind: str
    text: str = ""


class Composer:
    """Editable message buffer. A returned True from apply() means Enter submitted it."""

    def __init__(self) -> None:
        self.text = ""
        self.cursor = 0

    def apply(self, action: KeyAction) -> bool:
        if action.kind == "insert":
            self._insert("    " if action.text == "\t" else action.text)
        elif action.kind == "newline":
            self._insert("\n")
        elif action.kind == "paragraph":
            self._insert("\n\n")
        elif action.kind == "backspace":
            self._delete_before()
        elif action.kind == "delete":
            self._delete_after()
        elif action.kind == "left":
            self.cursor = max(0, self.cursor - 1)
        elif action.kind == "right":
            self.cursor = min(len(self.text), self.cursor + 1)
        elif action.kind == "home":
            self.cursor = self.text.rfind("\n", 0, self.cursor) + 1
        elif action.kind == "end":
            nxt = self.text.find("\n", self.cursor)
            self.cursor = len(self.text) if nxt < 0 else nxt
        elif action.kind == "up":
            self._vertical(-1)
        elif action.kind == "down":
            self._vertical(1)
        elif action.kind == "submit":
            return True
        return False

    def _insert(self, value: str) -> None:
        self.text = self.text[: self.cursor] + value + self.text[self.cursor :]
        self.cursor += len(value)

    def _delete_before(self) -> None:
        if self.cursor <= 0:
            return
        self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
        self.cursor -= 1

    def _delete_after(self) -> None:
        if self.cursor >= len(self.text):
            return
        self.text = self.text[: self.cursor] + self.text[self.cursor + 1 :]

    def _vertical(self, direction: int) -> None:
        line_start = self.text.rfind("\n", 0, self.cursor) + 1
        column = self.cursor - line_start
        if direction < 0:
            if line_start == 0:
                self.cursor = 0
                return
            previous_end = line_start - 1
            previous_start = self.text.rfind("\n", 0, previous_end) + 1
            self.cursor = previous_start + min(column, previous_end - previous_start)
            return
        line_end = self.text.find("\n", self.cursor)
        if line_end < 0:
            self.cursor = len(self.text)
            return
        nxt = line_end + 1
        nxt_end = self.text.find("\n", nxt)
        limit = len(self.text) if nxt_end < 0 else nxt_end
        self.cursor = nxt + min(column, limit - nxt)


class EscapeDecoder:
    """Turn terminal bytes into composer actions, including Shift+Enter sequences."""

    def __init__(self) -> None:
        self.buf = ""

    def feed(self, char: str) -> list[KeyAction]:
        self.buf += char
        return self._drain(final=False)

    def flush(self) -> list[KeyAction]:
        self.buf = ""
        return []

    def _drain(self, *, final: bool) -> list[KeyAction]:
        actions: list[KeyAction] = []
        while self.buf:
            if self.buf[0] != "\x1b":
                actions.append(_plain_key(self.buf[0]))
                self.buf = self.buf[1:]
                continue
            if self.buf.startswith("\x1b\r") or self.buf.startswith("\x1b\n"):
                actions.append(KeyAction("newline"))
                self.buf = self.buf[2:]
                continue
            if len(self.buf) == 1:
                break
            if self.buf[1] == "O":
                if len(self.buf) < 3:
                    break
                actions.append(_ss3_key(self.buf[2]))
                self.buf = self.buf[3:]
                continue
            if self.buf[1] != "[":
                self.buf = self.buf[1:]
                continue
            end = _csi_end(self.buf)
            if end is None:
                break
            actions.append(_csi_key(self.buf[:end]))
            self.buf = self.buf[end:]
        if final:
            self.buf = ""
        return actions


def action_from_windows_key(virtual_key: int, control_state: int, char: str) -> KeyAction:
    """Map one Windows console key. Keypad Enter is Return; the main key is Enter."""
    key = virtual_key & 0xFFFF
    shift = bool(control_state & SHIFT_PRESSED)
    enhanced = bool(control_state & ENHANCED_KEY)
    ctrl = bool(control_state & CTRL_PRESSED)
    if key == VK_RETURN or char == "\r":
        if shift and enhanced:
            return KeyAction("paragraph")
        if shift:
            return KeyAction("newline")
        return KeyAction("submit")
    if ctrl and key in {0x43, 0x03}:
        return KeyAction("interrupt")
    if ctrl and key in {0x44, 0x5A}:
        return KeyAction("eof")
    if key == VK_BACK or char in {"\b", "\x7f"}:
        return KeyAction("backspace")
    if key == VK_DELETE:
        return KeyAction("delete")
    if key == VK_LEFT:
        return KeyAction("left")
    if key == VK_RIGHT:
        return KeyAction("right")
    if key == VK_UP:
        return KeyAction("up")
    if key == VK_DOWN:
        return KeyAction("down")
    if key == VK_HOME:
        return KeyAction("home")
    if key == VK_END:
        return KeyAction("end")
    if key == VK_TAB or char == "\t":
        return KeyAction("insert", "\t")
    if char and (char >= " " or char == "\t"):
        return KeyAction("insert", char)
    if char == "\x03":
        return KeyAction("interrupt")
    if char in {"\x04", "\x1a"}:
        return KeyAction("eof")
    return KeyAction("ignore")


def cursor_cell(origin_col: int, text: str, width: int) -> tuple[int, int]:
    """Return the row and column of the cursor after origin_col and text."""
    row, col = divmod(max(origin_col, 0), width)
    for char in text:
        if char == "\n":
            row += 1
            col = 0
            continue
        col += 1
        if col >= width:
            row += 1
            col = 0
    return row, col


def read_message(console: Any, prompt: str) -> str:
    """Read one chat message. Scripted and piped consoles keep ordinary line input."""
    if not _interactive(console):
        return str(console.input(prompt))
    try:
        if sys.platform == "win32":
            return _read_windows(console, prompt)
        return _read_posix(console, prompt)
    except OSError:
        return str(console.input(prompt))


def _interactive(console: object) -> bool:
    file = getattr(console, "file", None)
    isatty = getattr(file, "isatty", None)
    if not callable(isatty):
        return False
    try:
        return bool(isatty()) and bool(sys.stdin.isatty())
    except (OSError, ValueError):
        return False


def _prompt_ansi(console: object, prompt: str) -> tuple[str, int]:
    plain = Text.from_markup(prompt).plain
    width = int(getattr(console, "width", 80) or 80)
    if not getattr(console, "color_system", None):
        return plain, len(plain)
    buffer = StringIO()
    capture = Console(
        file=buffer,
        force_terminal=True,
        width=width,
        theme=SOL_LITE_THEME,
        highlight=False,
        color_system=getattr(console, "color_system", "auto"),
    )
    capture.print(prompt, end="")
    return buffer.getvalue(), len(plain)


class _View:
    def __init__(self, stream: TextIO, prompt_ansi: str, prompt_width: int, width: int) -> None:
        self.stream = stream
        self.prompt_ansi = prompt_ansi
        self.prompt_width = prompt_width
        self.width = max(width, 2)
        self.rows = 0

    def render(self, text: str, cursor: int) -> None:
        if self.rows > 1:
            self.stream.write(f"\x1b[{self.rows - 1}A")
        self.stream.write("\r\x1b[J")
        self.stream.write(self.prompt_ansi)
        self.stream.write(text)
        end_row, _end_col = cursor_cell(self.prompt_width, text, self.width)
        cur_row, cur_col = cursor_cell(self.prompt_width, text[:cursor], self.width)
        up = end_row - cur_row
        if up > 0:
            self.stream.write(f"\x1b[{up}A")
        self.stream.write("\r")
        if cur_col:
            self.stream.write(f"\x1b[{cur_col}C")
        self.rows = end_row + 1
        self.stream.flush()

    def finish(self, text: str) -> None:
        self.render(text, len(text))
        self.stream.write("\n")
        self.stream.flush()
        self.rows = 0


def _edit(console: object, prompt: str, read_batch: Callable[[], list[KeyAction]]) -> str:
    stream = getattr(console, "file", None) or sys.stdout
    prompt_ansi, prompt_width = _prompt_ansi(console, prompt)
    width = int(getattr(console, "width", 80) or 80)
    editor = Composer()
    view = _View(stream, prompt_ansi, prompt_width, width)
    try:
        view.render(editor.text, editor.cursor)
        while True:
            submitted = False
            for action in read_batch():
                if action.kind == "interrupt":
                    raise KeyboardInterrupt
                if action.kind == "eof":
                    if editor.text:
                        submitted = True
                        break
                    raise EOFError
                if editor.apply(action):
                    submitted = True
                    break
            view.render(editor.text, editor.cursor)
            if submitted:
                return editor.text
    finally:
        view.finish(editor.text)


def _plain_key(char: str) -> KeyAction:
    if char in {"\r", "\n"}:
        return KeyAction("submit")
    if char in {"\b", "\x7f"}:
        return KeyAction("backspace")
    if char == "\x03":
        return KeyAction("interrupt")
    if char in {"\x04", "\x1a"}:
        return KeyAction("eof")
    if char == "\t":
        return KeyAction("insert", "\t")
    if char < " ":
        return KeyAction("ignore")
    return KeyAction("insert", char)


def _ss3_key(char: str) -> KeyAction:
    if char == "M":
        return KeyAction("submit")
    return KeyAction("ignore")


def _csi_end(sequence: str) -> int | None:
    for index, char in enumerate(sequence):
        if index < 2:
            continue
        if "@" <= char <= "~":
            return index + 1
    return None


def _shifted(modifier: int) -> bool:
    return bool((modifier - 1) & 0x1) if modifier else False


def _csi_key(sequence: str) -> KeyAction:
    body = sequence[2:]
    final = body[-1:]
    parts = body[:-1].split(";") if body[:-1] else []
    if final == "u" and parts and parts[0].isdigit():
        code = int(parts[0])
        modifier = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        return _modified_enter(code, _shifted(modifier))
    if final == "~" and len(parts) >= 3 and parts[0] == "27" and parts[2].isdigit():
        modifier = int(parts[1]) if parts[1].isdigit() else 1
        return _modified_enter(int(parts[2]), _shifted(modifier))
    if final == "~" and parts[:1] == ["3"]:
        return KeyAction("delete")
    if final == "~" and parts[:1] in (["1"], ["7"]):
        return KeyAction("home")
    if final == "~" and parts[:1] in (["4"], ["8"]):
        return KeyAction("end")
    return {
        "A": KeyAction("up"),
        "B": KeyAction("down"),
        "C": KeyAction("right"),
        "D": KeyAction("left"),
        "H": KeyAction("home"),
        "F": KeyAction("end"),
    }.get(final, KeyAction("ignore"))


def _modified_enter(code: int, shift: bool) -> KeyAction:
    if code == 13 and shift:
        return KeyAction("newline")
    if code == 57414 and shift:
        return KeyAction("paragraph")
    if code in {13, 57414}:
        return KeyAction("submit")
    return KeyAction("ignore")


def _read_posix(console: object, prompt: str) -> str:
    import codecs
    import os
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    decoder = EscapeDecoder()
    utf8 = codecs.getincrementaldecoder("utf-8")("replace")

    def read_char() -> str:
        while True:
            raw = os.read(fd, 1)
            if not raw:
                raise EOFError
            chars = utf8.decode(raw)
            if chars:
                return chars

    def read_batch() -> list[KeyAction]:
        actions = decoder.feed(read_char())
        if decoder.buf:
            ready, _, _ = select.select([fd], [], [], 0.05)
            if not ready:
                actions.extend(decoder.flush())
        return actions or [KeyAction("ignore")]

    try:
        return _edit(console, prompt, read_batch)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original)


def _read_windows(console: object, prompt: str) -> str:
    import ctypes
    from ctypes import byref, c_char, c_long, c_short, c_ulong, windll
    from ctypes.wintypes import BOOL, DWORD, HANDLE, WCHAR

    class UnicodeOrAscii(ctypes.Union):
        _fields_ = [("AsciiChar", c_char), ("UnicodeChar", WCHAR)]

    class KeyEventRecord(ctypes.Structure):
        _fields_ = [
            ("KeyDown", c_long),
            ("RepeatCount", c_short),
            ("VirtualKeyCode", c_short),
            ("VirtualScanCode", c_short),
            ("uChar", UnicodeOrAscii),
            ("ControlKeyState", c_long),
        ]

    class MouseEventRecord(ctypes.Structure):
        _fields_ = [
            ("MousePositionX", c_short),
            ("MousePositionY", c_short),
            ("ButtonState", c_long),
            ("ControlKeyState", c_long),
            ("EventFlags", c_long),
        ]

    class WindowBufferSizeRecord(ctypes.Structure):
        _fields_ = [("X", c_short), ("Y", c_short)]

    class MenuEventRecord(ctypes.Structure):
        _fields_ = [("CommandId", c_long)]

    class FocusEventRecord(ctypes.Structure):
        _fields_ = [("SetFocus", c_long)]

    class EventRecord(ctypes.Union):
        _fields_ = [
            ("KeyEvent", KeyEventRecord),
            ("MouseEvent", MouseEventRecord),
            ("WindowBufferSizeEvent", WindowBufferSizeRecord),
            ("MenuEvent", MenuEventRecord),
            ("FocusEvent", FocusEventRecord),
        ]

    class InputRecord(ctypes.Structure):
        _fields_ = [("EventType", c_short), ("Event", EventRecord)]

    kernel = windll.kernel32
    kernel.GetStdHandle.restype = HANDLE
    kernel.GetStdHandle.argtypes = [DWORD]
    kernel.GetConsoleMode.argtypes = [HANDLE, ctypes.POINTER(DWORD)]
    kernel.GetConsoleMode.restype = BOOL
    kernel.SetConsoleMode.argtypes = [HANDLE, DWORD]
    kernel.SetConsoleMode.restype = BOOL
    kernel.ReadConsoleInputW.argtypes = [
        HANDLE,
        ctypes.POINTER(InputRecord),
        DWORD,
        ctypes.POINTER(DWORD),
    ]
    kernel.ReadConsoleInputW.restype = BOOL
    kernel.GetNumberOfConsoleInputEvents.argtypes = [HANDLE, ctypes.POINTER(DWORD)]
    kernel.GetNumberOfConsoleInputEvents.restype = BOOL

    handle = kernel.GetStdHandle(DWORD(c_ulong(-10).value))
    original = DWORD()
    if not kernel.GetConsoleMode(handle, byref(original)):
        raise OSError("SOL-Lite could not read the console input mode")
    echo_input = 0x0004
    line_input = 0x0002
    processed_input = 0x0001
    virtual_terminal_input = 0x0200
    mode = original.value & ~(echo_input | line_input | virtual_terminal_input)
    if not kernel.SetConsoleMode(handle, DWORD(mode | processed_input)):
        raise OSError("SOL-Lite could not set the console input mode")

    def read_batch() -> list[KeyAction]:
        collected: list[KeyAction] = []
        while True:
            record = InputRecord()
            read = DWORD()
            if not kernel.ReadConsoleInputW(handle, byref(record), 1, byref(read)):
                raise OSError("SOL-Lite could not read a console key")
            if record.EventType == 1 and record.Event.KeyEvent.KeyDown:
                key = record.Event.KeyEvent
                char = key.uChar.UnicodeChar or ""
                action = action_from_windows_key(int(key.VirtualKeyCode), int(key.ControlKeyState), char)
                if action.kind != "ignore":
                    collected.extend([action] * max(1, int(key.RepeatCount)))
            pending = DWORD()
            kernel.GetNumberOfConsoleInputEvents(handle, byref(pending))
            if not pending.value and collected:
                return collected

    try:
        return _edit(console, prompt, read_batch)
    finally:
        kernel.SetConsoleMode(handle, original)
