from pathlib import Path

from sol_lite.agents.tool_allowlist import resolve_session_tools
from sol_lite.tools import build_tool_registry

ROOT = Path(__file__).resolve().parents[2]


def test_engineer_session_tools_are_a_subset_and_include_workspace_and_remote():
    available = build_tool_registry().names()
    names = resolve_session_tools(ROOT, "sol_engineer", available)
    assert names is not None
    assert "inventory_workspace" in names
    assert "list_project_structure" in names
    assert "execute_terminal_command" in names
    assert "remote_execute" in names
    assert "procedure_load" in names
    assert "procedure_status" in names
    assert "procedure_advance" in names
    assert "procedure_acknowledge" in names
    assert "studio_inspect" in names
    assert "studio_edit" in names
    assert "studio_quarantine" in names
    assert "google_email_send" not in names
    assert "jira_search" in names
    assert "jira_comment" in names
    assert "jira_plan" not in names
    assert "jira_create" not in names
    assert set(names) <= set(available)


def test_pa_session_keeps_google_and_remote():
    available = build_tool_registry().names()
    names = resolve_session_tools(ROOT, "sol_pa", available)
    assert "google_email_search" in names
    assert "jira_plan" in names
    assert "jira_create" in names
    assert "remote_list_nodes" in names
    assert "repository_push" not in names


def test_missing_agent_yaml_falls_back_to_core_tools():
    available = ["inventory_workspace", "execute_terminal_command", "google_email_send"]
    names = resolve_session_tools(Path("/nonexistent"), "sol_unknown", available)
    assert names == ("inventory_workspace", "execute_terminal_command")


def test_studio_admin_session_has_sec_git_read_not_push():
    available = build_tool_registry().names()
    names = resolve_session_tools(ROOT, "sol_studio_admin", available)
    assert "studio_owner_status" in names
    assert "studio_seccheck" in names
    assert "studio_lite_pen" in names
    assert "inventory_workspace" in names
    assert "write_workspace_file" in names
    assert "repository_status" in names
    assert "remote_list_nodes" in names
    assert "skill_discover" in names
    assert "repository_push" not in names
    assert "hosting_pr_merge" not in names
    assert "google_email_send" not in names
    assert set(names) <= set(available)
