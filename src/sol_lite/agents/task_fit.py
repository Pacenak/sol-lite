
"""Decide which tools are allowed to answer the user's latest request."""

from __future__ import annotations

import re

WORKSPACE_EVIDENCE_TOOL_NAMES = frozenset({
    "inventory_workspace",
    "list_project_structure",
    "list_workspace_directories",
    "find_workspace_files",
    "read_workspace_file",
    "read_workspace_files",
    "get_workspace_file_metadata",
    "search_codebase",
    "analyze_architecture_drift",
    "runtime_get_context",
})

DIRECTORY_LISTING_TOOL_NAMES = frozenset({
    "list_workspace_directories",
    "list_project_structure",
})

COMMAND_TOOL_NAMES = frozenset({
    "sol_command_status",
    "sol_shared_memories",
    "sol_shared_rag_search",
    "sol_jarvis_propose",
})

GOOGLE_TOOL_NAMES = frozenset({
    "google_email_search",
    "google_email_read",
    "google_email_send",
    "google_calendar_list",
    "google_calendar_create",
    "google_calendar_reminder",
})

JIRA_NETWORK_TOOL_NAMES = frozenset({
    "jira_status",
    "jira_projects",
    "jira_boards",
    "jira_board_issues",
    "jira_search",
    "jira_get",
    "jira_plan",
    "jira_create",
    "jira_update",
    "jira_comment",
    "jira_transition",
})

JIRA_LOCAL_TOOL_NAMES = frozenset({
    "jira_workspace_status",
    "jira_save_workspace",
})

JIRA_TOOL_NAMES = JIRA_NETWORK_TOOL_NAMES | JIRA_LOCAL_TOOL_NAMES

STUDIO_BOUND_TOOL_NAMES = frozenset({
    "studio_odoo_schema",
    "studio_odoo_inventory",
    "studio_odoo_copy_catalogs",
    "studio_odoo_adopt_source",
    "studio_odoo_write_import",
})

STUDIO_LOCAL_TOOL_NAMES = frozenset({
    "studio_odoo_status",
    "studio_odoo_bind",
})

STUDIO_TOOL_NAMES = STUDIO_BOUND_TOOL_NAMES | STUDIO_LOCAL_TOOL_NAMES

WEB_TOOL_NAMES = frozenset({"searxng_search"})

TERMINAL_TOOL_NAMES = frozenset({"execute_terminal_command"})

REMOTE_TOOL_NAMES = frozenset({
    "remote_list_nodes",
    "remote_execute",
})

PROCEDURE_TOOL_NAMES = frozenset({
    "procedure_load",
    "procedure_status",
    "procedure_advance",
    "procedure_acknowledge",
    "studio_inspect",
    "studio_create",
    "studio_edit",
    "studio_quarantine",
})

GIT_READ_TOOL_NAMES = frozenset({
    "repository_status",
    "repository_diff",
    "repository_log",
    "repository_branches",
    "repository_remotes",
    "repository_conflict_status",
    "hosting_pr_status",
})

GIT_WRITE_TOOL_NAMES = frozenset({
    "repository_create_branch",
    "repository_checkout",
    "repository_stage",
    "repository_commit",
    "repository_create_bundle",
    "repository_import_bundle",
    "repository_create_patch",
    "repository_apply_patch",
    "repository_merge_import",
    "repository_pull",
    "repository_merge",
    "repository_resolve_and_continue",
    "repository_set_remote",
    "repository_fetch",
    "repository_push",
    "repository_clone_remote",
    "repository_clone_local",
    "hosting_pr_create",
    "hosting_pr_merge",
})

NOTES_TOOL_NAMES = frozenset({
    "workspace_notes_read",
    "workspace_notes_write",
})

CHANGE_TOOL_NAMES = (
    WORKSPACE_EVIDENCE_TOOL_NAMES
    | TERMINAL_TOOL_NAMES
    | frozenset({
        "write_workspace_file",
        "edit_workspace_file",
        "studio_inspect",
        "studio_create",
        "studio_edit",
        "studio_quarantine",
    })
)

OPT_IN_TOOL_NAMES = (
    COMMAND_TOOL_NAMES
    | GOOGLE_TOOL_NAMES
    | JIRA_TOOL_NAMES
    | STUDIO_TOOL_NAMES
    | WEB_TOOL_NAMES
    | TERMINAL_TOOL_NAMES
    | GIT_WRITE_TOOL_NAMES
    | REMOTE_TOOL_NAMES
    | NOTES_TOOL_NAMES
)

_TASK_TOOLS = {
    "procedure": PROCEDURE_TOOL_NAMES,
    "directory_listing": DIRECTORY_LISTING_TOOL_NAMES,
    "sol_command": COMMAND_TOOL_NAMES,
    "google": GOOGLE_TOOL_NAMES,
    "jira": JIRA_TOOL_NAMES,
    "studio_odoo": STUDIO_TOOL_NAMES,
    "web": WEB_TOOL_NAMES,
    "terminal": TERMINAL_TOOL_NAMES,
    "git_write": GIT_WRITE_TOOL_NAMES,
    "git_read": GIT_READ_TOOL_NAMES,
    "remote": REMOTE_TOOL_NAMES,
    "workspace_inspection": WORKSPACE_EVIDENCE_TOOL_NAMES,
    "identity": WORKSPACE_EVIDENCE_TOOL_NAMES,
    "notes": WORKSPACE_EVIDENCE_TOOL_NAMES | NOTES_TOOL_NAMES,
    "change": CHANGE_TOOL_NAMES,
}

_DIRECTORY_LISTING_PATTERNS = (
    r"\bfolders?\b",
    r"\bdirector(?:y|ies)\b",
    r"\bdirs?\b",
    r"\bsub[- ]?folders?\b",
    r"\btree\b",
    r"\bpaths?\b",
)

_COMMAND_PATTERNS = (
    r"\bsol-command\b",
    r"\bsol command\b",
    r"\bshared memor(?:y|ies)\b",
    r"\bsectors?\b",
    r"\bjarvis\b",
)

_GOOGLE_PATTERNS = (
    r"\bemail\b",
    r"\bgmail\b",
    r"\bcalendar\b",
    r"\binbox\b",
)

_JIRA_PATTERNS = (
    r"\bjira\b",
    r"\batlassian\b",
    r"\bjql\b",
    r"\bsprints?\b",
    r"\bkanban\b",
    r"\bbacklogs?\b",
)

_STUDIO_PATTERNS = (
    r"\bodoo\b",
    r"\bgather[- ]pack\b",
    r"\bgst101a\b",
    r"\bstudio[- ]odoo\b",
    r"\bplg-odooacc\b",
    r"\bmyir\b",
)

_WEB_PATTERNS = (
    r"\bsearxng\b",
    r"\bsearch the web\b",
    r"\bsearch online\b",
    r"\bweb search\b",
    r"\binternet\b",
    r"\b(?:look up|lookup|research|find|check|consult|search)"
    r"\b[\s\S]{0,90}\b(?:online|documentation|docs|api reference|"
    r"official docs|library docs|package docs|website|github|pypi)\b",
    r"\b(?:latest|current|up[- ]to[- ]date)"
    r"\b[\s\S]{0,70}\b(?:documentation|docs|api|library|package)\b",
)

_TERMINAL_PATTERNS = (
    r"\bterminal\b",
    r"\bshell command\b",
    r"\bexecute\b",
    r"\brun (?:the |a )?(?:command|tests?|pytest|script)\b",
    r"\b(?:run|execute|perform)\b[\s\S]{0,60}"
    r"\b(?:ruff|mypy|lint|typecheck|build|compile|test suite)\b",
)

_REMOTE_PATTERNS = (
    r"\bssh\b",
    r"\bremote host\b",
    r"\bremote shell\b",
    r"\bpowershell remoting\b",
)

_PROCEDURE_PATTERNS = (
    r"\bfollow (?:the |this )?(?:studio |infrastructure )?"
    r"(?:procedure|checklist|runbook|docs?|manual|volume)\b",
    r"\bprocedure\b",
    r"\bchecklist\b",
    r"\brunbook\b",
    r"\binfrastructure\b",
    r"\bonboarding\b",
    r"\bstudio (?:setup|creation|hosts?)\b",
)

_GIT_WRITE_PATTERNS = (
    r"\bcommit\b",
    r"\bpush\b",
    r"\bpull\b",
    r"\bmerge\b",
    r"\bcheckout\b",
    r"\bstage\b",
    r"\bclone\b",
    r"\bfetch\b",
    r"\bcreate (?:a )?branch\b",
    r"\bpull request\b",
    r"\bpr\b",
)

_GIT_READ_PATTERNS = (
    r"\bgit\b",
    r"\bcommits?\b",
    r"\bbranch(?:es)?\b",
    r"\bdiffs?\b",
    r"\bhistory\b",
    r"\bconflict\b",
)

WORKSPACE_EVIDENCE_PATTERNS = (
    r"\bworkspace\b",
    r"\brepository\b",
    r"\brepo\b",
    r"\bcodebase\b",
    r"\bsource\b",
    r"\bfolder\b",
    r"\bdirectory\b",
    r"\bfiles?\b",
    r"\bcontents?\b",
    r"\banaly[sz]e\b",
    r"\binspect\b",
    r"\breview\b",
    r"\baudit\b",
    r"\bdebug\b",
    r"\bunderstand\b",
    r"\btrace\b",
    r"\binvestigate\b",
    r"\bfix\b",
    r"\bfunctions?\b",
    r"\bclasses\b",
    r"\bmodules?\b",
    r"\bdependencies\b",
    r"\bstack trace\b",
    r"\btraceback\b",
)

_IDENTITY_PATTERNS = (
    r"\bproject name\b",
    r"\bwhat is this\b",
    r"\bwhat(?:'s| is) the (?:project|program|app)\b",
    r"\bwhat (?:does|do)\b[\s\S]{0,80}\b(?:create|build|do)\b",
    r"\banaly[sz]e\b",
    r"\bworkspace\b",
    r"\bsource\b",
    r"\bhow to edit\b",
)

_NOTES_PATTERNS = (
    r"\bwrite (?:up )?notes\b",
    r"\bremember\b",
    r"\bso you know\b",
    r"\btake notes?\b",
    r"\bnote this\b",
    r"\bnote that\b",
)

_JIRA_READ_NOW_PATTERNS = (
    r"\bsprints?\b",
    r"\bboards?\b",
    r"\bissues?\b",
    r"\bbacklogs?\b",
    r"\bjql\b",
    r"\bkanban\b",
    r"\bjira status\b",
    r"\bstatus of (?:the |my )?jira\b",
    r"\bjira plan\b",
    r"\bplan (?:the |my )?jira\b",
)

_BROAD_PLAN = re.compile(
    r"\bplan my\b|\bweekly\b|\bmy weeks?\b|\bwork and personal\b",
    re.IGNORECASE,
)

_JIRA_SETUP = re.compile(
    r"\bset up\b|\bsetup\b|\bconnect jira\b|\buse jira\b",
    re.IGNORECASE,
)

_CHANGE_PATTERNS = (
    r"\bfix\b",
    r"\bimplement\b",
    r"\bchange\b",
    r"\badd\b",
    r"\brun (?:the |a )?(?:tests?|pytest)\b",
    r"(?<!how to )\bedit\b",
    r"\bpatch\b",
    r"\brefactor\b",
    r"\bmodify\b",
    r"\brepair\b",
    r"\bupgrade\b",
    r"\bupdate (?:the |a )?(?:code|source|function|module|file)\b",
    r"\bupdate (?:the |a )?(?:configuration|config|settings|tests?)\b",
    r"\bwrite (?:the |a )?(?:code|function|test)\b",
    r"\bcreate (?:the |a )?(?:function|module|file|test)\b",
)

_CLASS_PATTERNS = (
    ("procedure", _PROCEDURE_PATTERNS),
    ("directory_listing", _DIRECTORY_LISTING_PATTERNS),
    ("sol_command", _COMMAND_PATTERNS),
    ("google", _GOOGLE_PATTERNS),
    ("jira", _JIRA_PATTERNS),
    ("studio_odoo", _STUDIO_PATTERNS),
    ("web", _WEB_PATTERNS),
    ("terminal", _TERMINAL_PATTERNS),
    ("git_write", _GIT_WRITE_PATTERNS),
    ("git_read", _GIT_READ_PATTERNS),
    ("remote", _REMOTE_PATTERNS),
    ("workspace_inspection", WORKSPACE_EVIDENCE_PATTERNS),
    ("identity", _IDENTITY_PATTERNS),
    ("notes", _NOTES_PATTERNS),
    ("change", _CHANGE_PATTERNS),
)

_NARROW_WHEN_DIRECTORY = frozenset({
    "identity",
    "notes",
    "change",
})

_PATH_TOKEN = re.compile(
    r"(?:[A-Za-z]:[\\/][^\s`\"'|<>]+)|"
    r"(?:[\w.@+-]+(?:[\\/][\w.@+-]+)+)"
)

_LINE_PATH = re.compile(
    r"^[A-Za-z0-9._+-]+(?:/[A-Za-z0-9._+-]+)*$"
)


def _matches(text, patterns):
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in patterns
    )


def matching_tasks(user_text: str) -> list[str]:
    """Return every task class the sentence hits, in class order."""
    text = user_text or ""
    return [
        name
        for name, patterns in _CLASS_PATTERNS
        if _matches(text, patterns)
    ]


def classify_task(user_text: str) -> str | None:
    """Return the first task class, for callers needing one label."""
    tasks = matching_tasks(user_text)
    return tasks[0] if tasks else None


def jira_read_now(user_text: str) -> bool:
    """True when the user requests Jira data rather than setup."""
    text = user_text or ""
    if _BROAD_PLAN.search(text) and _JIRA_SETUP.search(text):
        return False
    return _matches(text, _JIRA_READ_NOW_PATTERNS)


def apply_jira_workspace_gate(
    user_text,
    permitted,
    workspace_projects,
):
    """Hide network Jira tools until workspace prerequisites hold."""
    if permitted is None or "jira" not in matching_tasks(user_text):
        return permitted

    projects = [
        str(item).strip()
        for item in (workspace_projects or ())
        if str(item).strip()
    ]

    if projects and jira_read_now(user_text):
        return permitted

    return frozenset(permitted) - JIRA_NETWORK_TOOL_NAMES


def apply_studio_workspace_gate(
    user_text,
    permitted,
    studio_root,
):
    """Hide Studio import tools until a studio root is verified."""
    if permitted is None or "studio_odoo" not in matching_tasks(user_text):
        return permitted

    if str(studio_root or "").strip():
        return permitted

    return frozenset(permitted) - STUDIO_BOUND_TOOL_NAMES


def permitted_tools(
    user_text: str,
    allowlist: frozenset[str] | None,
) -> frozenset[str] | None:
    """Select tools available for the request.

    Matching classes are unioned. Opt-in tools remain excluded
    unless their task class matches. The agent allowlist is always
    applied when supplied.

    None preserves the legacy behavior for callers that provide
    neither a recognized task nor an allowlist.
    """
    tasks = matching_tasks(user_text)

    if (
        "directory_listing" in tasks
        and not _NARROW_WHEN_DIRECTORY.intersection(tasks)
    ):
        tasks = [
            name
            for name in tasks
            if name != "workspace_inspection"
        ]

    if not tasks:
        if allowlist is None:
            return None
        permitted = frozenset(allowlist) - OPT_IN_TOOL_NAMES
    else:
        permitted = frozenset()
        for name in tasks:
            permitted |= _TASK_TOOLS[name]

    # Reading an active procedure is supporting context, not a new task domain.
    # Agent allowlists and the skill-inspection permission still apply.
    if allowlist is not None and "skill_read" in allowlist:
        permitted = permitted | frozenset({"skill_read"})
    if allowlist is not None:
        permitted = permitted & frozenset(allowlist)

    return permitted


def normalize_directory_path(
    token: str,
    root: str | None = None,
) -> str:
    text = token.strip().strip("`\"'").replace("\\", "/")

    while text.startswith("./"):
        text = text[2:]

    text = text.rstrip("/")
    folded = text.casefold()

    if root:
        root_norm = root.replace("\\", "/").rstrip("/").casefold()

        if folded == root_norm:
            return ""

        prefix = root_norm + "/"
        folded = folded.removeprefix(prefix)

    return folded


def directory_evidence(
    name: str,
    result,
) -> tuple[set[str], str | None]:
    """Collect normalized paths from a successful directory listing."""
    if not isinstance(result, dict) or result.get("ok") is False:
        return set(), None

    if name == "list_workspace_directories":
        paths = {
            normalize_directory_path(path)
            for path in result.get("directories") or []
            if isinstance(path, str)
            and normalize_directory_path(path)
        }

        root = result.get("root")
        return paths, root if isinstance(root, str) else None

    if name == "list_project_structure":
        paths = set()

        for line in result.get("tree") or []:
            text = str(line).strip()

            if text.endswith("/"):
                normalized = normalize_directory_path(text)
                if normalized:
                    paths.add(normalized)

        return paths, None

    return set(), None


def invented_directory_paths(
    content: str,
    evidence: set[str],
    root: str | None = None,
) -> list[str]:
    """Return directory paths in an answer absent from tool evidence."""
    allowed = set(evidence)
    invented = []
    seen = set()

    def consider(token):
        if not token or token in seen:
            return

        seen.add(token)
        normalized = normalize_directory_path(token, root)

        if not normalized or normalized in allowed:
            return

        invented.append(token)

    for match in _PATH_TOKEN.finditer(content or ""):
        consider(match.group(0).strip(".,);]"))

    for line in (content or "").splitlines():
        stripped = line.strip().lstrip("-*").strip().strip("`")

        if _LINE_PATH.fullmatch(stripped):
            consider(stripped)

    return invented
