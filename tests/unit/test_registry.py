from sol_lite.tools import build_tool_registry


def test_implemented_tool_manifest():
    names = set(build_tool_registry().names())
    assert names == {
        "inventory_workspace", "list_project_structure", "find_workspace_files",
        "read_workspace_file", "read_workspace_files", "get_workspace_file_metadata",
        "write_workspace_file", "search_codebase", "analyze_architecture_drift",
        "execute_terminal_command", "repository_status", "repository_diff", "repository_log",
        "repository_branches", "repository_remotes", "repository_create_branch",
        "repository_checkout", "repository_stage", "repository_commit",
        "repository_create_bundle", "repository_import_bundle", "repository_create_patch",
        "repository_apply_patch", "repository_merge_import", "repository_set_remote",
        "repository_fetch",
        "repository_push", "repository_clone_remote", "repository_clone_local", "runtime_get_context", "skill_discover", "skill_install", "searxng_search",
    }
