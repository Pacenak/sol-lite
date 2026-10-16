"""Optional integrations with independently deployed SOL services."""

from .sol_command import SolCommandClient, SolCommandConfig, stage_synced_skills
from .studio_odoo import REQUIRED_KEY, StudioCatalog, StudioError, verify_studio_root

__all__ = [
    "REQUIRED_KEY",
    "SolCommandClient",
    "SolCommandConfig",
    "StudioCatalog",
    "StudioError",
    "stage_synced_skills",
    "verify_studio_root",
]
