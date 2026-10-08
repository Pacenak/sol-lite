from sol_lite.capabilities.definition import (
    CapabilityDefinition,
)
from sol_lite.capabilities.risk import RiskClass
from sol_lite.mcp.security import (
    MCPExposurePolicy,
)


def capability(name, *risks):
    return CapabilityDefinition(
        identity=name,
        risk=frozenset(risks),
    )


def test_default_policy_allows_read_only_stdio():
    policy = MCPExposurePolicy()

    cap = capability(
        "repository_status",
        RiskClass.READ_ONLY,
    )

    assert policy.allows(
        cap,
        transport="stdio",
    )


def test_default_policy_rejects_mutating_capability():
    policy = MCPExposurePolicy()

    cap = capability(
        "repository_commit",
        RiskClass.MUTATING,
    )

    assert not policy.allows(
        cap,
        transport="stdio",
    )


def test_denied_capability_overrides_allow_list():
    policy = MCPExposurePolicy(
        allowed_capabilities=frozenset(
            {"repository_status"}
        ),
        denied_capabilities=frozenset(
            {"repository_status"}
        ),
    )

    cap = capability(
        "repository_status",
        RiskClass.READ_ONLY,
    )

    assert not policy.allows(
        cap,
        transport="stdio",
    )


def test_allow_list_fails_closed():
    policy = MCPExposurePolicy(
        allowed_capabilities=frozenset(
            {"repository_status"}
        )
    )

    cap = capability(
        "repository_log",
        RiskClass.READ_ONLY,
    )

    assert not policy.allows(
        cap,
        transport="stdio",
    )


def test_remote_read_only_requires_explicit_authorization():
    policy = MCPExposurePolicy()

    cap = capability(
        "repository_status",
        RiskClass.READ_ONLY,
    )

    assert not policy.allows(
        cap,
        transport="streamable-http",
        authorized=False,
    )

    assert policy.allows(
        cap,
        transport="streamable-http",
        authorized=True,
    )


def test_mixed_risk_capability_is_not_read_only():
    policy = MCPExposurePolicy(
        allowed_risks=frozenset(
            {
                RiskClass.READ_ONLY,
                RiskClass.MUTATING,
            }
        )
    )

    cap = capability(
        "mixed",
        RiskClass.READ_ONLY,
        RiskClass.MUTATING,
    )

    assert not policy.allows(
        cap,
        transport="stdio",
        authorized=False,
    )

    assert policy.allows(
        cap,
        transport="stdio",
        authorized=True,
    )


def test_undeclared_risk_is_rejected():
    policy = MCPExposurePolicy()

    cap = capability("unknown-risk")

    assert not policy.allows(
        cap,
        transport="stdio",
    )