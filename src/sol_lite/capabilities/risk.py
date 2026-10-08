"""Risk classification for executable SOL-Lite capabilities."""
from enum import StrEnum


class RiskClass(StrEnum):
    READ_ONLY = "READ_ONLY"
    LOW_RISK = "LOW_RISK"
    MUTATING = "MUTATING"
    PRIVILEGED = "PRIVILEGED"
    REMOTE = "REMOTE"
    NETWORK = "NETWORK"
    DESTRUCTIVE = "DESTRUCTIVE"
    CREDENTIAL_SENSITIVE = "CREDENTIAL_SENSITIVE"
