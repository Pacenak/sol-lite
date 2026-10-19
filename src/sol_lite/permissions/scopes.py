"""Permission scope names."""
READ = "filesystem.read"
WRITE = "filesystem.write"
MOVE = "filesystem.move"
DELETE = "filesystem.delete"
TERMINAL = "terminal"
TERMINAL_READ = "terminal.read"
TERMINAL_WRITE = "terminal.write"
NETWORK = "network"
REMOTE_LIST = "remote.list"
REMOTE_EXECUTE = "remote.execute"
REPOSITORY_READ = "repository.read"
REPOSITORY_WRITE = "repository.write"
REPOSITORY_REMOTE = "repository.remote"
SKILL_INSPECT = "skills.inspect"
SKILL_INSTALL = "skills.install"


def scope_for_operation(operation: str) -> str:
    """Map a tool operation name to the session-grant scope it spends."""
    op = str(operation or "").strip().lower()
    if op == "consolidate_inbox_apply":
        return WRITE
    if op in {"consolidate_inbox_preview", "search_knowledge_index"}:
        return READ
    if op.startswith("workspace_pack_"):
        return READ if op == "workspace_pack_status" else WRITE
    if "terminal" in op or op == "execute_terminal_command":
        return TERMINAL_WRITE
    if op in {"write_workspace_file", "edit_workspace_file"} or "write" in op or "edit" in op:
        return WRITE
    return op or WRITE
