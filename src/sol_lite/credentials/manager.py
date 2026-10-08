"""Credential manager. Secrets never cross into model-facing context."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
@dataclass(frozen=True, slots=True)
class CredentialReference:
    provider: str
    key: str
class CredentialBackend(Protocol):
    def get(self, provider: str, key: str) -> object: ...
    def set(self, provider: str, key: str, value: object) -> None: ...
    def delete(self, provider: str, key: str) -> None: ...
class CredentialManager:
    def __init__(self, backend: CredentialBackend): self._backend = backend
    def reference(self, provider: str, key: str) -> CredentialReference: return CredentialReference(provider, key)
    def resolve(self, reference: CredentialReference) -> object: return self._backend.get(reference.provider, reference.key)
    def store(self, reference: CredentialReference, value: object) -> None: self._backend.set(reference.provider, reference.key, value)
    def delete(self, reference: CredentialReference) -> None: self._backend.delete(reference.provider, reference.key)
class KeyringBackend:
    """OS-backed credential storage through the established keyring package."""
    def _keyring(self):
        try:
            import keyring
        except ImportError as exc:
            raise RuntimeError("Credential storage requires the 'keyring' package.") from exc
        return keyring
    def get(self, provider: str, key: str) -> object:
        value = self._keyring().get_password(provider, key)
        if value is None: raise KeyError(f"Credential not found: {provider}/{key}")
        return value
    def set(self, provider: str, key: str, value: object) -> None: self._keyring().set_password(provider, key, str(value))
    def delete(self, provider: str, key: str) -> None: self._keyring().delete_password(provider, key)
