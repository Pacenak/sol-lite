"""Parse studio Markdown checklists into classified steps."""
from __future__ import annotations

import re

from .models import ProcedureDocument, ProcedureStep

_PLACEHOLDER = re.compile(r"\{\{[^{}]+\}\}")
_EXAMPLE_IP = re.compile(r"\b10\.10(?:\.\d{1,3}){2}\b")
_EXAMPLE_HOST = re.compile(r"\b[\w.-]*pacenlife\.com\b", re.IGNORECASE)
_CLAIM = re.compile(r"\[(?:PLANNED|UNKNOWN)\]", re.IGNORECASE)
_HUMAN = re.compile(r"\b(?:bitwarden|password|gui)\b", re.IGNORECASE)
_APPROVAL = re.compile(
    r"(?i)(\bsudo\b|scripts/install/|\bdocker\s+compose\s+up\b|\bremote_execute\b)"
)
_STATUS = re.compile(r"(?:→|->)\s*(\d{3})\b")
_HEADING = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
_BACKTICK = re.compile(r"`([^`]+)`")


def parse_procedure(text: str, *, source: str) -> ProcedureDocument:
    """Return classified rows. Unrecognised prose is listed, not executed."""
    lines = text.splitlines()
    tables = _tables(lines)
    consumed = {index for table in tables for index in table["indexes"]}
    steps: list[ProcedureStep] = []
    for table in tables:
        steps.extend(_classify_table(table, _section_for(lines, table["indexes"][0])))
    unparsed = _unparsed_sections(lines, consumed)
    steps.extend(_fences(lines))
    return ProcedureDocument(source, tuple(steps), tuple(unparsed))


def _tables(lines: list[str]) -> list[dict]:
    tables = []
    index = 0
    while index < len(lines):
        if not _is_table_line(lines[index]):
            index += 1
            continue
        start = index
        while index < len(lines) and _is_table_line(lines[index]):
            index += 1
        rows = [_split_row(lines[row]) for row in range(start, index)]
        rows = [row for row in rows if not _is_separator(row)]
        if len(rows) >= 2:
            tables.append({
                "headers": [_plain(cell) for cell in rows[0]],
                "body": rows[1:],
                "indexes": list(range(start, index)),
            })
    return tables


def _classify_table(table: dict, section: str) -> list[ProcedureStep]:
    headers = [cell.casefold() for cell in table["headers"]]
    header_text = " ".join(headers)
    kind = _table_kind(headers, header_text, table["body"])
    if kind is None:
        return []
    steps = []
    for offset, row in enumerate(table["body"], start=1):
        padded = row + [""] * max(0, len(table["headers"]) - len(row))
        steps.append(_classify_row(kind, table["headers"], padded, section, offset))
    return steps


def _table_kind(headers: list[str], header_text: str, body: list[list[str]]) -> str | None:
    names = set(headers)
    if {"step", "action", "validate"} <= names:
        return "procedure"
    if {"step", "host", "action"} <= names and "validate" not in names:
        return "host"
    blob = header_text + " " + " ".join(cell for row in body for cell in row)
    if "bitwarden" in header_text or "done?" in names or "☐" in blob or _HUMAN.search(header_text):
        return "human"
    return None


def _classify_row(kind, headers, row, section, offset) -> ProcedureStep:
    raw = {_plain(header).casefold(): cell.strip() for header, cell in zip(headers, row, strict=False)}
    cells = {key: _plain(value) for key, value in raw.items()}
    step_id = cells.get("step") or cells.get("#") or f"check-{offset}"
    step_id = step_id or f"check-{offset}"
    if kind == "procedure":
        action = cells.get("action", "")
        validate = cells.get("validate", "")
        action_command = _command(raw.get("action", ""))
        validate_command = _command(raw.get("validate", ""))
    elif kind == "host":
        action = " ".join(
            part for part in (cells.get("host", ""), cells.get("action", "")) if part
        )
        validate = ""
        action_command = _command(raw.get("action", ""))
        validate_command = ""
    else:
        action = " | ".join(part for part in (_plain(part) for part in row) if part)
        validate = ""
        action_command = ""
        validate_command = ""
    status = _STATUS.search(raw.get("validate", validate) if kind == "procedure" else validate)
    classification = _classification(
        kind,
        f"{action} {validate}",
        action_command,
        validate_command,
    )
    return ProcedureStep(
        step_id=step_id,
        action=action,
        validate=validate,
        classification=classification,
        section=section,
        action_command=action_command,
        validate_command=validate_command,
        required_status=status.group(1) if status else "",
    )


def _classification(kind, text, action_command, validate_command) -> str:
    if kind == "host":
        return "unverifiable"
    if kind == "human":
        return "human_gate"
    if _CLAIM.search(text) or _PLACEHOLDER.search(text):
        return "blocked"
    if _EXAMPLE_IP.search(text) or _EXAMPLE_HOST.search(text):
        return "blocked"
    if _HUMAN.search(text) or "☐" in text:
        return "human_gate"
    if not validate_command:
        return "unverifiable"
    if _needs_approval(action_command):
        return "needs_approval"
    return "read_only"


def _needs_approval(command: str) -> bool:
    if not command:
        return False
    if _APPROVAL.search(command):
        return True
    return any(token in command for token in (";", "&&", "||", "|", ">", "<"))


def _fences(lines: list[str]) -> list[ProcedureStep]:
    steps = []
    index = 0
    number = 0
    while index < len(lines):
        if not re.match(r"^```[A-Za-z0-9_-]*\s*$", lines[index].strip()):
            index += 1
            continue
        index += 1
        body = []
        while index < len(lines) and not lines[index].strip().startswith("```"):
            body.append(lines[index])
            index += 1
        if index < len(lines):
            index += 1
        number += 1
        command = "\n".join(body).strip()
        steps.append(ProcedureStep(
            step_id=f"block-{number}",
            action=command,
            validate="",
            classification="candidate",
            action_command=command,
        ))
    return steps


def _command(cell: str) -> str:
    found = _BACKTICK.findall(cell)
    return found[0].strip() if found else ""


def _unparsed_sections(lines: list[str], consumed: set[int]) -> list[str]:
    sections = []
    current = None
    has_table = False
    has_prose = False

    def close():
        if current and has_prose and not has_table:
            sections.append(current)

    for index, line in enumerate(lines):
        heading = _HEADING.match(line.strip())
        if heading:
            close()
            current = heading.group(2).strip()
            has_table = False
            has_prose = False
            continue
        if current is None:
            continue
        if index in consumed:
            has_table = True
            continue
        if line.strip():
            has_prose = True
    close()
    return sections


def _section_for(lines: list[str], index: int) -> str:
    section = ""
    for line_index, line in enumerate(lines):
        if line_index > index:
            break
        heading = _HEADING.match(line.strip())
        if heading:
            section = heading.group(2).strip()
    return section


def _is_table_line(line: str) -> bool:
    return line.strip().startswith("|")


def _split_row(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def _is_separator(row: list[str]) -> bool:
    return bool(row) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in row)


def _plain(text: str) -> str:
    return text.replace("**", "").replace("`", "").strip()
