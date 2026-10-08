"""Capability contracts for native, MCP, skill, and remote execution."""
from .definition import CapabilityDefinition, CapabilityLocality, CapabilityProvider
from .dispatcher import CapabilityDispatcher, ExecutionResult
from .evidence import EvidenceRecord
from .registry import CapabilityRegistry
from .risk import RiskClass

__all__ = ["CapabilityDefinition", "CapabilityDispatcher", "CapabilityLocality", "CapabilityProvider", "CapabilityRegistry", "EvidenceRecord", "ExecutionResult", "RiskClass"]
