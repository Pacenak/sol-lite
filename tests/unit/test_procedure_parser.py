from sol_lite.procedures import parse_procedure

FIXTURE = """
# Fixture checklist

## Pass and fail

| Step | Action | Validate |
|------|--------|----------|
| A1 | `echo alpha` | `echo ok` |
| A2 | `echo beta` | `echo missing` |
| A3 | `echo gamma` | `echo ok` |

## Placeholder

| Step | Action | Validate |
|------|--------|----------|
| P1 | `echo {{PLACEHOLDER}}` | `echo ok` |

## Planned

| Step | Action | Validate |
|------|--------|----------|
| L1 | `echo later` [PLANNED] | `echo ok` |

## Secrets

| Step | Action | Validate |
|------|--------|----------|
| S1 | Create the admin password in Bitwarden `PLG Example` | login works |

## Host only

| Step | Host | Action |
|------|------|--------|
| D1 | plg-horde01 | `echo host` |

## Already done

| Done? | Item |
|-------|------|
| ☐ | Cables are live |

## Notes

This section has no checklist table.
"""


def _doc():
    return parse_procedure(FIXTURE, source="fixture.md")


def test_step_action_validate_rows_keep_ids_and_commands():
    doc = _doc()
    rows = {step.step_id: step for step in doc.steps}

    assert rows["A1"].action_command == "echo alpha"
    assert rows["A1"].validate_command == "echo ok"
    assert rows["A1"].classification == "read_only"
    assert rows["A2"].classification == "read_only"
    assert rows["P1"].classification == "blocked"
    assert rows["L1"].classification == "blocked"
    assert rows["S1"].classification == "human_gate"
    assert rows["D1"].classification == "unverifiable"
    assert any(step.classification == "human_gate" and "Cables" in step.action for step in doc.steps)
    assert any("Notes" in section for section in doc.unparsed_sections)
    assert doc.complete is False


def test_sudo_install_and_example_addresses_do_not_become_read_only():
    text = """
| Step | Action | Validate |
|------|--------|----------|
| A1 | `sudo bash scripts/install/plg-install-docker-official.sh` | `docker compose version` |
| A7 | `curl -sI http://10.10.66.10:8080` | `echo status` → 200 |
| U1 | `echo ship` [UNKNOWN] | `echo ok` |
| W1 | `echo hello > out.txt` | `echo ok` |
"""
    doc = parse_procedure(text, source="risk.md")
    rows = {step.step_id: step for step in doc.steps}

    assert rows["A1"].classification == "needs_approval"
    assert rows["A7"].classification == "blocked"
    assert rows["A7"].required_status == "200"
    assert rows["U1"].classification == "blocked"
    assert rows["W1"].classification == "needs_approval"
