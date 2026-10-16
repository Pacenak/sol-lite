"""Fill {{NAME}} inside the runtime. The model and the audit see the name."""
from __future__ import annotations

import os
import re

from ..credentials.manager import CredentialReference

_TOKEN = re.compile(r"\{\{([A-Z][A-Z0-9_]{2,})\}\}")
_PROVIDER = "plg-studio"


class MissingSecret(ValueError):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"missing_secret: {name}")


def resolve_command(template: str, ctx) -> tuple[str, str, list[tuple[str, str]]]:
    """Return the original template, the rendered command, and the values used."""
    names = []
    for name in _TOKEN.findall(template or ""):
        if name not in names:
            names.append(name)
    if not names:
        return template, template, []
    found: list[tuple[str, str]] = []
    rendered = template
    for name in names:
        value = _lookup(ctx, name)
        rendered = rendered.replace("{{" + name + "}}", value)
        found.append((name, value))
    return template, rendered, found


def redact(text: str, secrets: list[tuple[str, str]]) -> str:
    redacted = text or ""
    for name, value in secrets:
        if value:
            redacted = redacted.replace(value, "{{" + name + "}}")
    return redacted


def _lookup(ctx, name: str) -> str:
    manager = getattr(ctx, "credential_manager", None)
    if manager is not None:
        try:
            value = manager.resolve(CredentialReference(_PROVIDER, name))
        except (KeyError, RuntimeError, TypeError):
            value = None
        if value not in (None, ""):
            return _clean(name, str(value))
    env = os.environ.get(name)
    if env:
        return _clean(name, env)
    raise MissingSecret(name)


def _clean(name: str, value: str) -> str:
    if "\n" in value or "\r" in value or "\x00" in value:
        raise MissingSecret(name)
    return value
