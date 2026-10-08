from sol_lite.capabilities import CapabilityDefinition, CapabilityDispatcher, CapabilityProvider, CapabilityRegistry, RiskClass
from sol_lite.orchestration import ContextManager, EvidenceLedger, TaskContext

class Context:
    session_id = "session-1"

def test_capability_definition_preserves_ollama_schema():
    capability = CapabilityDefinition(identity="example", description="Example capability.", input_schema={"type": "object", "properties": {"value": {"type": "string"}}, "required": ["value"]}, risk=frozenset({RiskClass.READ_ONLY}))
    assert capability.name == "example"
    assert capability.parameters["required"] == ["value"]
    assert capability.as_ollama_schema()["function"]["name"] == "example"

def test_registry_rejects_duplicates():
    registry = CapabilityRegistry()
    capability = CapabilityDefinition(identity="z")
    registry.register(capability)
    assert registry.names() == ["z"]
    try:
        registry.register(capability)
    except ValueError as exc:
        assert "Duplicate capability" in str(exc)
    else:
        raise AssertionError("duplicate registration was accepted")

def test_dispatcher_returns_evidence():
    registry = CapabilityRegistry()
    registry.register(CapabilityDefinition(identity="example", provider=CapabilityProvider.NATIVE, handler=lambda ctx, args: {"ok": args["value"]}))
    result = CapabilityDispatcher(registry).execute("example", {"value": "x"}, Context())
    assert result.success is True
    assert result.value == {"ok": "x"}
    assert result.evidence is not None
    assert result.evidence.capability == "example"

def test_context_and_evidence_are_structured():
    context = TaskContext("test objective", session_id="s1")
    manager = ContextManager(context)
    manager.add_constraint("offline-first")
    manager.add_constraint("offline-first")
    manager.add_changed_file("a.py")
    context.add_event({"phase": "DISCOVERY"})
    ledger = EvidenceLedger()
    ledger.record(kind="observation", source="native", operation="read", target="a.py", result={"bytes": 1}, success=True)
    snapshot = manager.snapshot()
    assert snapshot["constraints"] == ["offline-first"]
    assert snapshot["changed_files"] == ["a.py"]
    assert ledger.has_successful_operation("read")
