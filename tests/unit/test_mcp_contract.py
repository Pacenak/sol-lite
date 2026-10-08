from sol_lite.mcp.security import MCPExposurePolicy
from sol_lite.capabilities.definition import CapabilityDefinition
from sol_lite.capabilities.risk import RiskClass


def test_mcp_policy_defaults_to_read_only():
    cap = CapabilityDefinition(identity="read", risk=frozenset({RiskClass.READ_ONLY}))
    assert MCPExposurePolicy().allows(cap)


def test_mcp_policy_denies_mutation_by_default():
    cap = CapabilityDefinition(identity="write", risk=frozenset({RiskClass.MUTATING}))
    assert not MCPExposurePolicy().allows(cap)


def test_mcp_policy_requires_explicit_allow_list_when_configured():
    cap = CapabilityDefinition(identity="read", risk=frozenset({RiskClass.READ_ONLY}))
    policy = MCPExposurePolicy(allowed_capabilities=frozenset({"other"}))
    assert not policy.allows(cap)
