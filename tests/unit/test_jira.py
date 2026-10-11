"""Scope checks for the native Jira client and agent tool grants."""
import json
from pathlib import Path

from sol_lite.agents.task_fit import permitted_tools
from sol_lite.agents.tool_allowlist import resolve_session_tools
from sol_lite.credentials.manager import CredentialManager
from sol_lite.integrations.jira import JiraCatalog, JiraError, constrain_jql
from sol_lite.tools import build_tool_registry

ROOT = Path(__file__).resolve().parents[2]
TOKEN = "secret-token-value"


class MemoryBackend:
    def __init__(self):
        self.data = {}

    def get(self, provider, key):
        if (provider, key) not in self.data:
            raise KeyError(key)
        return self.data[(provider, key)]

    def set(self, provider, key, value):
        self.data[(provider, key)] = value

    def delete(self, provider, key):
        self.data.pop((provider, key), None)


class Transport:
    def __init__(self, responder):
        self.calls = []
        self.responder = responder

    def request(self, method, url, headers, json_body=None, params=None):
        self.calls.append({
            "method": method, "url": url, "headers": dict(headers),
            "json": json_body, "params": params,
        })
        return self.responder(method, url, json_body, params)


def catalog(tmp_path, responder):
    transport = Transport(responder)
    client = JiraCatalog(
        tmp_path / "jira.json",
        CredentialManager(MemoryBackend()),
        transport,
    )
    return client, transport


def connect(client, name="Work", projects=None, token=TOKEN):
    return client.connect(
        name, "https://example.atlassian.net", "ada@example.com", token, projects or ["SOL"],
    )


def test_jql_is_forced_inside_granted_projects():
    bounded = constrain_jql("project = OTHER ORDER BY updated DESC", ["SOL"])
    assert "project in (SOL)" in bounded
    assert bounded.index("project = OTHER") < bounded.index("AND project in (SOL)")


def test_foreign_issue_and_unscoped_search_are_rejected(tmp_path):
    def responder(method, url, body, params):
        return 200, {"issues": []}

    client, transport = catalog(tmp_path, responder)
    connect(client, "One", ["SOL"])
    connect(client, "Two", ["PLG"])
    try:
        client.get("OTHER-1")
    except JiraError as exc:
        assert "not granted" in str(exc)
    else:
        raise AssertionError("foreign issue key was accepted")
    try:
        client.search("project = OTHER")
    except JiraError as exc:
        assert "Choose a Jira project" in str(exc)
    else:
        raise AssertionError("search without a project was accepted")
    assert transport.calls == []


def test_search_keeps_scope_and_hides_the_token(tmp_path):
    def responder(method, url, body, params):
        return 200, {"issues": [{
            "key": "SOL-1",
            "fields": {
                "summary": f"see {TOKEN}",
                "status": {"name": "To Do"},
                "project": {"key": "SOL"},
                "description": "plain",
            },
        }, {
            "key": "OTHER-9",
            "fields": {"summary": "nope", "project": {"key": "OTHER"}},
        }]}

    client, transport = catalog(tmp_path, responder)
    connect(client)
    result = client.search("project = OTHER ORDER BY rank")
    sent = transport.calls[0]["json"]["jql"]
    assert "project in (SOL)" in sent
    assert "Authorization" in transport.calls[0]["headers"]
    encoded = json.dumps(result)
    assert TOKEN not in encoded
    assert "Authorization" not in encoded
    assert [issue["key"] for issue in result["issues"]] == ["SOL-1"]
    saved = (tmp_path / "jira.json").read_text(encoding="utf-8")
    assert TOKEN not in saved


def test_boards_are_filtered_to_granted_projects(tmp_path):
    def responder(method, url, body, params):
        return 200, {"isLast": True, "values": [
            {"id": 1, "name": "SOL board", "type": "scrum", "location": {"projectKey": "SOL"}},
            {"id": 2, "name": "Other board", "type": "kanban", "location": {"projectKey": "OTHER"}},
            {"id": 3, "name": "No project", "type": "scrum"},
        ]}

    client, _transport = catalog(tmp_path, responder)
    connect(client, projects=["SOL"])
    result = client.boards()
    assert result["boards"] == [{
        "id": 1, "name": "SOL board", "project": "SOL", "type": "scrum",
    }]


def test_plan_walks_every_connection(tmp_path):
    def responder(method, url, body, params):
        if url.endswith("/board"):
            project = "SOL" if "example" in url else "PLG"
            return 200, {"isLast": True, "values": [
                {"id": 7, "name": f"{project} board", "type": "scrum", "location": {"projectKey": project}},
            ]}
        if url.endswith("/sprint"):
            return 200, {"isLast": True, "values": [{"id": 3, "name": "Sprint", "state": "active"}]}
        if url.endswith("/issue"):
            return 200, {"isLast": True, "issues": [{
                "key": "SOL-2" if "/example." in url else "PLG-2",
                "fields": {"summary": "Open", "project": {"key": "SOL" if "/example." in url else "PLG"}},
            }]}
        return 200, {}

    client, _transport = catalog(tmp_path, responder)
    connect(client, "Work", ["SOL"])
    client.connect("Studio", "https://studio.atlassian.net", "ada@example.com", TOKEN, ["PLG"])
    result = client.plan()
    assert {board["project"] for board in result["boards"]} == {"SOL", "PLG"}
    assert all("error" not in board for board in result["boards"])


def test_pa_plans_and_engineer_updates_without_business_access():
    available = build_tool_registry().names()
    pa = set(resolve_session_tools(ROOT, "sol_pa", available))
    engineer = set(resolve_session_tools(ROOT, "sol_engineer", available))
    business = set(resolve_session_tools(ROOT, "sol_business", available))
    assert {"jira_plan", "jira_create", "jira_boards"} <= pa
    assert "jira_plan" not in engineer and "jira_create" not in engineer
    assert "jira_comment" in engineer and "jira_get" in engineer
    assert not business.intersection(pa.intersection({
        "jira_plan", "jira_create", "jira_get", "jira_comment",
    }))
    allowed = permitted_tools("plan the jira sprint", frozenset(available))
    assert "jira_plan" in allowed
    assert "jira_plan" not in permitted_tools("list the folders", frozenset(available))


WEEKLY = "both work and personal. set up agile and use jira for work"


def test_jira_reads_wait_until_this_workspace_has_projects():
    from sol_lite.agents.task_fit import apply_jira_workspace_gate

    available = frozenset(build_tool_registry().names())
    weekly = permitted_tools(WEEKLY, available)
    closed = apply_jira_workspace_gate(WEEKLY, weekly, [])
    assert "jira_plan" not in closed
    assert "jira_status" not in closed
    assert "jira_save_workspace" in closed
    assert "jira_workspace_status" in closed
    still_planning = apply_jira_workspace_gate(WEEKLY, weekly, ["SOL"])
    assert "jira_plan" not in still_planning
    reading = apply_jira_workspace_gate(
        "plan the jira sprint",
        permitted_tools("plan the jira sprint", available),
        ["SOL"],
    )
    assert "jira_plan" in reading
    assert "jira_plan" not in apply_jira_workspace_gate(
        "plan the jira sprint",
        permitted_tools("plan the jira sprint", available),
        [],
    )


def test_save_workspace_stores_projects_without_returning_the_token(tmp_path):
    from types import SimpleNamespace

    from sol_lite.core.exceptions import ApprovalRequired
    from sol_lite.core.session import WorkspaceManager
    from sol_lite.tools.jira import _save_workspace, _workspace_status

    class Permit:
        def check(self, scope, **kwargs):
            if not kwargs.get("approval_id"):
                raise ApprovalRequired("need approval", request=None)

    client, _transport = catalog(tmp_path, lambda *args: (200, {}))
    root = tmp_path / "ws"
    root.mkdir()
    manager = WorkspaceManager(tmp_path / "workspaces.json")
    workspace = manager.register(root)
    ctx = SimpleNamespace(
        jira=client,
        permission_engine=Permit(),
        workspace_manager=manager,
        workspace_id=workspace.workspace_id,
        jira_projects=(),
        audit=None,
    )
    details = {
        "projects": "SOL",
        "name": "Work",
        "base_url": "https://example.atlassian.net",
        "email": "ada@example.com",
        "token": TOKEN,
    }
    try:
        _save_workspace(ctx, details)
    except ApprovalRequired:
        pass
    else:
        raise AssertionError("save ran before approval")
    result = _save_workspace(ctx, {**details, "approval_id": "a1"})
    encoded = json.dumps(result)
    assert result["projects"] == ["SOL"]
    assert TOKEN not in encoded
    assert manager.get(workspace.workspace_id).jira_projects == ["SOL"]
    assert ctx.jira_projects == ("SOL",)
    status = _workspace_status(ctx, {})
    assert status["projects_set"] is True
    assert status["site_saved"] is True
    assert TOKEN not in json.dumps(status)
    saved = (tmp_path / "jira.json").read_text(encoding="utf-8")
    assert TOKEN not in saved


def test_remembered_text_redacts_the_jira_token():
    from sol_lite.agents.shell import redact_secrets

    text = f"token is {TOKEN} please"
    assert redact_secrets(text, [TOKEN]) == "token is [redacted] please"
    assert redact_secrets(text, ["short"]) == text
