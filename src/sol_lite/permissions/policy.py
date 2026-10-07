"""Permission policy."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PermissionRule:
    enabled: bool
    approval_required: bool

class PermissionPolicy:
    def __init__(self, raw):
        self.raw = raw.get("permissions", raw)

    def rule(self, *parts):
        current = self.raw
        for part in parts:
            if not isinstance(current, dict):
                return PermissionRule(False, True)
            current = current.get(part)
        if not isinstance(current, dict):
            return PermissionRule(False, True)
        return PermissionRule(
            bool(current.get("enabled", False)),
            bool(current.get("approval_required", True)),
        )

    def terminal_lists(self):
        t = self.raw.get("terminal", {})
        return list(t.get("allowed_commands", [])), list(t.get("blocked_commands", []))
