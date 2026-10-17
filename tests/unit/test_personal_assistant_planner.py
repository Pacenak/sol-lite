"""Execute the documented primitives; do not substitute a test-only implementation."""
import json
import re
from copy import deepcopy
from pathlib import Path

import pytest
from icalendar import Calendar
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from sol_lite.skills.manager import SkillManager

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/personal-assistant-planner/SKILL.md"


@pytest.fixture(scope="module")
def primitives():
    namespace = {}
    for code in re.findall(r"```python\n(.*?)```", SKILL.read_text(encoding="utf-8"), re.DOTALL):
        exec(compile(code, str(SKILL), "exec"), namespace)  # noqa: S102 - trusted skill examples
    return namespace


@pytest.fixture
def event():
    return {"uid": "focus-1@example.invalid", "title": "Review", "start": "2026-10-18T20:00:00Z",
            "end": "2026-10-18T20:30:00Z", "immutable": False, "sequence": 0}


@pytest.fixture(scope="module")
def validator():
    text = SKILL.read_text(encoding="utf-8")
    schema = json.loads(re.findall(r"```json\n(.*?)```", text, re.DOTALL)[0])
    Draft202012Validator.check_schema(schema)
    checker = FormatChecker()
    assert "date-time" in checker.checkers, "Install the RFC 3339 test dependency"
    return Draft202012Validator(schema, format_checker=checker)


@pytest.fixture
def envelope(event):
    return {"schema_version": "1.0", "tenant_id": "tenant-a", "principal_id": "principal-a",
            "schedule_id": "week-1", "revision": 1, "events": [event]}


@pytest.mark.parametrize("agent", ["sol_pa", "sol_docs", "sol_business", "sol_engineer"])
def test_builtin_discovery_and_routing(tmp_path, agent):
    manager = SkillManager(ROOT, tmp_path)
    record = next(r for r in manager.for_agent(agent)
                  if r.skill_id == "personal-assistant-planner")
    assert record.source_type == "builtin" and record.status == "BUILTIN"
    assert record.warnings == []
    for task in ("Please PLAN  MY WEEK", "Update my schedule", "Export my calendar",
                 "Use $personal-assistant-planner"):
        assert "DETAILED SKILL: personal-assistant-planner\n" in manager.prompt_context(
            agent, task=task)
    assert "DETAILED SKILL: personal-assistant-planner\n" not in manager.prompt_context(
        agent, task="Inspect scheduler_cache variables")


@pytest.mark.parametrize(("action", "exists", "bound", "expected"), [
    ("read", True, False, "read"), ("export", True, True, "export"),
    ("create", False, False, "create"), ("save-as", False, False, "create"),
    ("save", False, False, "create"), ("save", True, True, "patch"),
    ("edit", True, True, "edit"), ("update", True, True, "update"),
    ("delete", True, True, "delete"),
])
def test_intent_transitions(primitives, action, exists, bound, expected):
    assert primitives["file_intent"](action, exists, bound) == expected


@pytest.mark.parametrize(("action", "exists", "bound"), [
    ("create", True, True), ("save-as", True, False), ("save", True, False),
    ("edit", False, True), ("update", True, False), ("delete", False, False),
    ("ambiguous", True, True),
])
def test_intent_rejects_unsafe_or_ambiguous_transitions(primitives, action, exists, bound):
    with pytest.raises((ValueError, FileExistsError)):
        primitives["file_intent"](action, exists, bound)


def test_adjacent_intervals_and_offsets(primitives, event):
    following = dict(event, uid="second", start="2026-10-19T09:30:00+13:00",
                     end="2026-10-19T10:00:00+13:00")
    primitives["assert_no_overlap"]([following, event])
    primitives["assert_no_overlap"]([])


@pytest.mark.parametrize(("start", "end"), [
    ("2026-10-18T20:15:00Z", "2026-10-18T21:00:00Z"),
    ("2026-10-18T19:00:00Z", "2026-10-18T21:00:00Z"),
    ("2026-10-18T20:00:00Z", "2026-10-18T20:00:00Z"),
    ("2026-10-18T21:00:00Z", "2026-10-18T20:00:00Z"),
    ("2026-10-18T20:00:00", "2026-10-18T21:00:00"),
])
def test_reject_overlap_nonpositive_and_naive_times(primitives, event, start, end):
    with pytest.raises(ValueError):
        primitives["assert_no_overlap"]([event, dict(event, uid="other", start=start, end=end)])


def test_json_valid_envelope(validator, envelope):
    validator.validate(envelope)


@pytest.mark.parametrize(("field", "value"), [
    ("start", "2026-02-30T20:00:00Z"), ("end", "2026-10-18T21:00:00"),
    ("start", "2026-10-18T20:00:00+00:00"), ("sequence", -1),
    ("sequence", 2147483648), ("immutable", "false"), ("uid", "bad\r\nUID:injected"),
])
def test_json_invalid_event(validator, envelope, field, value):
    envelope["events"][0][field] = value
    with pytest.raises(ValidationError):
        validator.validate(envelope)


def test_json_closed_schema_and_required_fields(validator, envelope):
    envelope["unapproved"] = True
    with pytest.raises(ValidationError):
        validator.validate(envelope)
    del envelope["unapproved"]
    del envelope["tenant_id"]
    with pytest.raises(ValidationError):
        validator.validate(envelope)


def test_ics_unicode_escaping_roundtrip_and_bytes(primitives, event):
    event["title"] = 'Review, notes; C:\\work\r\n' + 'ā😀' * 90
    original = deepcopy(event)
    raw = primitives["export_ics"]([event], "2026-10-17T08:00:00Z")
    assert event == original
    assert raw.endswith(b"\r\n")
    assert b"\n" not in raw.replace(b"\r\n", b"")
    assert all(len(line) <= 75 for line in raw.split(b"\r\n"))
    for line in raw.split(b"\r\n"):
        line.decode("utf-8")
    parsed = Calendar.from_ical(raw).walk("VEVENT")
    assert len(parsed) == 1
    assert str(parsed[0]["SUMMARY"]) == event["title"].replace("\r\n", "\n")
    assert parsed[0].decoded("DTSTART") == primitives["instant"](event["start"])
    assert parsed[0].decoded("DTEND") == primitives["instant"](event["end"])
    assert str(parsed[0]["UID"]) == event["uid"]


def test_raw_ics_template_is_parseable():
    raw = re.findall(r"```ics\n(.*?)```", SKILL.read_text(encoding="utf-8"), re.DOTALL)[0]
    parsed = Calendar.from_ical(raw.replace("\n", "\r\n").encode()).walk("VEVENT")
    assert len(parsed) == 1
    assert (parsed[0].decoded("DTEND") - parsed[0].decoded("DTSTART")).total_seconds() == 1800


@pytest.mark.parametrize(("field", "value"), [
    ("uid", "bad\r\nSUMMARY:injected"), ("sequence", True),
    ("sequence", -1), ("sequence", 2147483648), ("title", "bad\x00text"),
    ("title", "bad\x7ftext"), ("start", "2026-10-18T20:00:00.1Z"),
])
def test_ics_rejects_invalid_values(primitives, event, field, value):
    event[field] = value
    with pytest.raises(ValueError):
        primitives["export_ics"]([event], "2026-10-17T08:00:00Z")


def test_ics_rejects_duplicate_uids_even_without_overlap(primitives, event):
    duplicate = dict(event, start="2026-10-18T21:00:00Z", end="2026-10-18T21:30:00Z")
    with pytest.raises(ValueError, match="Duplicate"):
        primitives["export_ics"]([event, duplicate], "2026-10-17T08:00:00Z")
