from sol_lite.tools import build_tool_registry


def test_implemented_tool_manifest():
    names = set(build_tool_registry().names())
    assert names == {
        "skill_read",
        "artifact_dependencies", "artifact_create", "artifact_render", "artifact_validate",
        "inventory_workspace", "list_workspace_directories", "list_project_structure", "find_workspace_files",
        "read_workspace_file", "read_workspace_files", "get_workspace_file_metadata",
        "write_workspace_file", "edit_workspace_file", "workspace_notes_read", "workspace_notes_write",
        "search_codebase", "analyze_architecture_drift",
        "execute_terminal_command", "repository_status", "repository_diff", "repository_log",
        "repository_branches", "repository_remotes", "repository_create_branch",
        "repository_checkout", "repository_stage", "repository_commit",
        "repository_create_bundle", "repository_import_bundle", "repository_create_patch",
        "repository_apply_patch", "repository_merge_import", "repository_pull",
        "repository_merge", "repository_conflict_status", "repository_resolve_and_continue",
        "repository_set_remote",
        "repository_fetch",
        "repository_push", "repository_clone_remote", "repository_clone_local",
        "hosting_pr_create", "hosting_pr_status", "hosting_pr_merge",
        "runtime_get_context", "skill_discover", "skill_install", "searxng_search",
        "sol_command_status", "sol_shared_memories", "sol_shared_rag_search", "sol_jarvis_propose",
        "google_email_search", "google_email_read", "google_email_send",
        "google_calendar_list", "google_calendar_create", "google_calendar_reminder",
        "jira_status", "jira_workspace_status", "jira_save_workspace", "jira_projects", "jira_boards", "jira_board_issues", "jira_search",
        "jira_get", "jira_plan", "jira_create", "jira_update", "jira_comment", "jira_transition",
        "studio_odoo_status", "studio_odoo_bind", "studio_odoo_schema", "studio_odoo_inventory",
        "studio_odoo_copy_catalogs", "studio_odoo_adopt_source", "studio_odoo_write_import",
        "remote_list_nodes", "remote_execute",
        "procedure_load", "procedure_status", "procedure_advance", "procedure_acknowledge",
        "studio_inspect", "studio_create", "studio_edit", "studio_quarantine",
        "studio_owner_status", "studio_seccheck", "studio_lite_pen",
    }


def test_google_and_command_mutability_is_preserved():
    registry = build_tool_registry()
    assert registry.get("sol_command_status").mutability is False
    assert registry.get("sol_jarvis_propose").mutability is True
    assert registry.get("google_email_search").mutability is False
    assert registry.get("google_email_send").mutability is True
    assert registry.get("google_calendar_create").mutability is True
    assert registry.get("jira_search").mutability is False
    assert registry.get("jira_create").mutability is True
    assert registry.get("jira_transition").mutability is True
    assert registry.get("studio_odoo_schema").mutability is False
    assert registry.get("studio_odoo_write_import").mutability is True
    assert registry.get("studio_odoo_copy_catalogs").mutability is True
    assert registry.get("remote_list_nodes").mutability is False
    assert registry.get("remote_execute").mutability is True
    assert registry.get("procedure_load").mutability is False
    assert registry.get("procedure_advance").mutability is False
