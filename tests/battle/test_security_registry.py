from sol_lite.capabilities.risk import RiskClass
from sol_lite.tools.base import ToolDefinition
from sol_lite.tools.registry import (
    ToolRegistry,
)


def handler(context, arguments):
    return arguments


def test_remote_repository_tools_get_remote_permission():
    registry = ToolRegistry()

    tool = ToolDefinition(
        name="repository_push",
        description="Push",
        parameters={
            "type": "object",
        },
        handler=handler,
    )

    registry.register(tool)

    registered = registry.get(
        "repository_push"
    )

    assert registered.permissions == (
        "repository.remote",
    )


def test_remote_repository_tools_get_remote_risks():
    registry = ToolRegistry()

    tool = ToolDefinition(
        name="repository_push",
        description="Push",
        parameters={
            "type": "object",
        },
        handler=handler,
    )

    registry.register(tool)

    registered = registry.get(
        "repository_push"
    )

    assert set(registered.risk) == {
        RiskClass.MUTATING,
        RiskClass.REMOTE,
        RiskClass.NETWORK,
    }


def test_local_repository_mutation_remains_repository_write():
    registry = ToolRegistry()

    tool = ToolDefinition(
        name="repository_commit",
        description="Commit",
        parameters={
            "type": "object",
        },
        handler=handler,
    )

    registry.register(tool)

    registered = registry.get(
        "repository_commit"
    )

    assert registered.permissions == (
        "repository.write",
    )

    assert registered.risk == (
        RiskClass.MUTATING,
    )