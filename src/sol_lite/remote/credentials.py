"""Credential references. Secrets never enter model-facing objects."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CredentialReference:
    provider: str
    key: str


class CredentialStore(Protocol):
    def resolve(self, reference: CredentialReference) -> object: ...


class EnvironmentCredentialStore:
    """Minimal adapter for non-secret credential references.

    It returns a credential object supplied by the caller's process environment
    through an injected resolver; the model layer only sees the reference.
    """

    def __init__(self, resolver):
        self._resolver = resolver

    def resolve(self, reference: CredentialReference) -> object:
        return self._resolver(reference)
