"""Validate public payload boundaries, without SSH or credential access."""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "skills/infrastructure-automation/references/tool-schemas.json").read_text(
        encoding="utf-8"
    )
)
VALID = {
    "check_system_status": {"machine_id": "lab_linux_01", "checks": ["identity", "routes"]},
    "execute_remote_command": {"machine_id": "lab_linux_01", "operation": "interfaces"},
    "prepare_configuration_plan": {
        "machine_id": "lab_linux_01",
        "resource_id": "service_ethernet",
        "change": {"kind": "dns", "servers": ["192.0.2.53"]},
    },
    "apply_configuration_plan": {"machine_id": "lab_linux_01", "plan_id": "plan_dns_001"},
}


def validator(tool):
    # Select the actual input definition: the schema-library root is not a tool.
    return Draft202012Validator(SCHEMA["$defs"][tool], format_checker=FormatChecker())


def test_schema_is_valid_draft_2020_12():
    Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("tool", VALID)
def test_documented_payloads_are_accepted(tool):
    validator(tool).validate(VALID[tool])


@pytest.mark.parametrize("tool", VALID)
@pytest.mark.parametrize(
    "field", ["command", "argv", "password", "private_key", "token", "approval_id", "hostname"]
)
def test_shell_credentials_and_authorization_cannot_enter_payload(tool, field):
    payload = {**VALID[tool], field: "synthetic_canary"}
    assert not validator(tool).is_valid(payload)


@pytest.mark.parametrize(
    "machine_id", ["ab", "-host", "host;id", "host\nwhoami", "$(id)", "../host", "a" * 65]
)
def test_machine_identifier_rejects_noncanonical_input(machine_id):
    payload = {**VALID["check_system_status"], "machine_id": machine_id}
    assert not validator("check_system_status").is_valid(payload)


@pytest.mark.parametrize("tool", ["check_system_status", "execute_remote_command"])
@pytest.mark.parametrize("deadline", [0, -1, 31, 900, 1.5, "30", True])
def test_read_deadline_cannot_be_disabled_or_widened(tool, deadline):
    assert not validator(tool).is_valid({**VALID[tool], "timeout_seconds": deadline})


@pytest.mark.parametrize("operation", ["reboot", "iptables", "sh", "interfaces; id", "unknown"])
def test_only_catalog_read_operations_are_accepted(operation):
    assert not validator("execute_remote_command").is_valid(
        {**VALID["execute_remote_command"], "operation": operation}
    )


@pytest.mark.parametrize("checks", [[], ["identity", "identity"], ["reboot"], ["identity"] * 7])
def test_check_batch_is_bounded_unique_and_read_only(checks):
    assert not validator("check_system_status").is_valid(
        {**VALID["check_system_status"], "checks": checks}
    )


@pytest.mark.parametrize(
    "change",
    [
        {"kind": "dns", "servers": []},
        {"kind": "dns", "servers": ["192.0.2.53"], "command": "id"},
        {"kind": "dhcp_ipv4", "script": "id"},
        {
            "kind": "static_ipv4",
            "address": "999.1.1.1",
            "prefix_length": 24,
            "gateway": "192.0.2.1",
        },
        {
            "kind": "static_ipv4",
            "address": "192.0.2.2",
            "prefix_length": 33,
            "gateway": "192.0.2.1",
        },
        {"kind": "managed_configuration", "desired_state_id": "../../script"},
    ],
)
def test_invalid_and_open_ended_configuration_is_rejected(change):
    assert not validator("prepare_configuration_plan").is_valid(
        {**VALID["prepare_configuration_plan"], "change": change}
    )


@pytest.mark.parametrize(
    "change",
    [
        {"kind": "dhcp_ipv4"},
        {
            "kind": "static_ipv4",
            "address": "192.0.2.2",
            "prefix_length": 24,
            "gateway": "192.0.2.1",
        },
        {"kind": "managed_configuration", "desired_state_id": "desired_network_01"},
    ],
)
def test_supported_plan_variants_are_accepted(change):
    validator("prepare_configuration_plan").validate(
        {**VALID["prepare_configuration_plan"], "change": change}
    )


@pytest.mark.parametrize("tool", VALID)
def test_required_target_cannot_be_omitted(tool):
    payload = copy.deepcopy(VALID[tool])
    del payload["machine_id"]
    assert not validator(tool).is_valid(payload)


def test_response_rejects_raw_output_and_unbounded_summary():
    result = {
        "machine_id": "lab_linux_01",
        "operation_id": "operation_001",
        "status": "OK",
        "summary": "Selected safe state only",
        "truncated": False,
    }
    validator("tool_result").validate(result)
    for field in ("stdout", "stderr", "password", "private_key"):
        assert not validator("tool_result").is_valid({**result, field: "synthetic_canary"})
    assert not validator("tool_result").is_valid({**result, "summary": "x" * 4097})
