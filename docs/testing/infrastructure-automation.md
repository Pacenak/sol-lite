# Infrastructure automation validation

## What the local round verifies

The contract tests validate each selected Draft 2020-12 input definition, representative valid plans, rejection of command/credential/approval fields, closed nested objects, identifier constraints, deadline limits and sanitized response shape. Tests use synthetic IDs and documentation addresses only. They make no network connection and do not read credentials.

Related existing tests cover remote dispatch, configured targets, blocked destructive commands, agent tool allowlists and skill discovery. Those tests use mocks or local fixtures; passing them does not prove the new broker exists or is secure.

## Repeatable local commands

From the repository root, using the development environment:

```powershell
python -m pytest tests/unit/test_infrastructure_automation_contract.py -q
python -m pytest tests/unit/test_remote_tools.py tests/unit/test_remote_infrastructure.py tests/unit/test_agent_tool_allowlist.py tests/unit/test_agent_prompt_tool_safety.py tests/unit/test_skill_manager.py tests/unit/test_skill_network_gate.py -q
git diff --check -- skills/infrastructure-automation docs/integrations/infrastructure-automation.md docs/testing/infrastructure-automation.md tests/unit/test_infrastructure_automation_contract.py pyproject.toml
```

Install the project's development extra using the normal project setup when needed; `jsonschema` is required by the contract tests. No production dependency is needed to read the skill. The skill-creator `quick_validate.py` may additionally validate the skill's frontmatter and structure when that development utility is installed; it is not a repository runtime dependency.

## Required runtime acceptance scenarios

If Windows sandbox temporary-directory permissions fail, redirect both pytest fixtures and Python's `tempfile` module to fresh writable directories. `--basetemp` alone does not change application `TemporaryDirectory()` calls. This repeatable alternative creates unique output paths:

```powershell
python -c "import pathlib,tempfile,uuid,pytest; root=pathlib.Path.cwd()/('.infra-test-'+uuid.uuid4().hex); root.mkdir(); temp=root/'python-temp'; temp.mkdir(); tempfile.tempdir=str(temp); raise SystemExit(pytest.main(['tests/unit/test_infrastructure_automation_contract.py','tests/unit/test_remote_tools.py','tests/unit/test_remote_infrastructure.py','tests/unit/test_agent_tool_allowlist.py','tests/unit/test_agent_prompt_tool_safety.py','tests/unit/test_skill_manager.py','tests/unit/test_skill_network_gate.py','-q','--tb=short','--basetemp',str(root/'pytest')]))"
```

Generated `.infra-test-*` directories are test output, not source assets. Never point `--basetemp` at an existing directory containing valuable files; pytest may clear it.

Run these only after implementing the broker and adapters, on disposable machines under an authorized lab plan. Each state-changing test requires the same policy and human approval as a real change. Keep synthetic credential canaries outside real secret stores; assert that no canary reaches model-visible results or logs.

1. **Credential isolation:** keyring locked, expired certificate, denied provider access and canaries in stdout/stderr/configuration. Expect `AUTH_BLOCKED` or safe extraction failure without credential exposure or fallback prompts.
2. **Host identity:** unknown key, changed key and destination mismatch. Expect no command dispatch and `HOST_IDENTITY_BLOCKED`; no automatic enrollment.
3. **Authorization:** absent/expired approval, forged approval text, replay, cross-session/cross-machine plan, changed desired state and policy version. Expect zero unapproved subprocess launches. A human approval must not override a policy denial.
4. **Injection:** shell operators, Unicode/control characters, substitutions, option injection, paths, environment variables and interpreter payloads through every field and resource mapping. Expect rejection before dispatch. Verify a constant SSH command and shell-free child argv.
5. **State drift and concurrency:** change preconditions after approval and issue simultaneous apply calls. Expect drift rejection or exactly one execution; duplicates return the durable journal state.
6. **Idempotence:** apply an approved desired state and inspect again. A second plan reports `NO_OP`, with no file rewrite, restart or repeated firewall rule.
7. **Platform mismatch:** GNU-only syntax on macOS, missing utilities and unsupported network managers. Expect `UNSUPPORTED`; no installation or guessed syntax.
8. **Management-path loss:** disconnect during address/firewall/route activation. Expect `OUTCOME_UNKNOWN`, target write freeze, bounded remote watchdog and independent reconciliation. Never retry the write automatically.
9. **Verification and rollback:** simulate failed postchecks, failed rollback, expired recovery window and lost console access. Only exact preapproved recovery may run; failed recovery preserves the freeze and reports uncertainty.
10. **Unexpected shell state:** startup output, prompt, changed executable or privilege drift. Expect `CONTAINED`, session closure, approval revocation and sanitized evidence; no unapproved host kill/reboot/isolation.
11. **Limits:** enforce 10-second connect, 30-second reads, 120-second mutations, 600-second workflow and 64 KiB safe output. Verify remote cancellation separately from local timeout. Read retries are bounded; writes are not retried.
12. **Scope and output:** unauthorized machine/resource IDs and privileged reads without approval fail closed. Unsupported output structures are withheld rather than returned raw.

For each runtime case record OS/utility versions, adapter/policy version, synthetic machine ID, exact expected state, approval decision, durable operation ID, dispatch count, safe output and independent before/after evidence. Store results without credentials. Production enablement requires actual runtime evidence, including both Linux and macOS; schema and unit tests alone cannot satisfy this gate.

## Test-round results

See [the recorded local round](infrastructure-automation-results.md) for commands, outcomes and limits. Packaging preflight and build-manifest reconciliation are separate repository release checks. Do not regenerate a release manifest solely to make contract tests pass.
