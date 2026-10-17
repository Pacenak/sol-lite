# Infrastructure automation: local test round

Date: 17 October 2026 (Pacific/Auckland).

## Final result

**96 tests passed** in the focused combined round, including **77 new contract tests**, which also passed independently. No SSH connection, credential-provider access, package installation or remote mutation was performed. These results validate design assets and existing local regression behavior; they do not certify a production broker.

## Scope and evidence

Combined pytest targets:

```text
tests/unit/test_infrastructure_automation_contract.py
tests/unit/test_remote_tools.py
tests/unit/test_remote_infrastructure.py
tests/unit/test_agent_tool_allowlist.py
tests/unit/test_agent_prompt_tool_safety.py
tests/unit/test_skill_manager.py
tests/unit/test_skill_network_gate.py
```

Executed through `pytest.main` with `-q --tb=short`, a fresh writable pytest base directory and an explicit writable `tempfile.tempdir` under the task's approved visualization output root. Final output: `96 passed in 1.02s`. See the [test guide](infrastructure-automation.md) for repeatable commands and the sandbox workaround.

The independent contract run (`python -m pytest tests/unit/test_infrastructure_automation_contract.py -q`) returned `77 passed in 0.16s`. It checks Draft 2020-12 schema validity, valid read/plan/apply payload shapes, command and credential-field rejection, identifier injection, timeout bounds, operation enumeration, batch bounds, nested-object closure, IPv4 format checking and sanitized response shape.

Additional checks:

- Skill-creator `quick_validate.py skills/infrastructure-automation`: `Skill is valid!`
- `python -m ruff check tests/unit/test_infrastructure_automation_contract.py`: `All checks passed!`
- `python -m ruff format --check tests/unit/test_infrastructure_automation_contract.py`: `1 file already formatted`
- Targeted `git diff --check`: passed; Git emitted a line-ending normalization notice for `pyproject.toml`.

`jsonschema>=4.18,<5` is declared in the development extra for reproducible contract-test dependencies. Runtime application dependencies are unchanged.

## Initial failures and resolution

The first combined run returned 88 passed and eight setup errors because pytest could not create its default sandbox temporary directories. A second run with only `--basetemp` returned 95 passed and one failure: an application `TemporaryDirectory()` cleanup still used the sandbox default and failed with Windows access denied. The expected ZIP traversal guard had already rejected the unsafe member; temporary-directory cleanup masked its exception.

The final run redirected both Python temporary storage and pytest fixture storage to fresh writable directories. All 96 tests passed without changes to existing runtime or tests. One new-test import-order lint issue was corrected and the file formatted before final verification.

## Limits and remaining release gates

No live Linux or macOS host was tested. Approval authenticity, credential isolation, output sanitization, remote watchdogs, host-key pinning, configuration idempotence, crash consistency, concurrent writes and rollback require the implemented broker and disposable-host acceptance scenarios in the test guide. Schema tests cannot prove that summaries contain no secrets or that every DNS string has valid IP semantics; these require broker parsers and runtime tests.

The complete repository test suite and packaging preflight were not run in this focused round. Static inspection found `scripts/preflight.py` expects 39 built-in skills, while the skill catalogue exceeds that count. Release manifest reconciliation remains a separate maintainer task. The working tree already contained unrelated changes; this report does not certify them.
