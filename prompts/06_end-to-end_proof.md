VALIDATION PASS

This prompt is intended for use after an approved implementation.

Do not make additional modifications unless the user explicitly requests them.

VALIDATION ORDER

1. Inspect changed files and confirm only planned files changed.
2. Run formatting/lint/type checks where applicable.
3. Run unit tests.
4. Run integration/API tests.
5. Run frontend tests/build.
6. Validate persona registration/loading.
7. Validate Anvil persona discovery specifically.
8. Validate at least TWO working sectors for regression.
9. Validate LIVE behavior if configured.
10. Compare LIVE/GITEA/WORKSPACE revision evidence.
11. Confirm original functional defect is fixed.
12. Confirm no unrelated behavior changed.
13. Update documentation only if it is part of the approved plan.

For every validation item report:
- command/action
- result
- pass/fail
- evidence
- affected files
- limitations

Do not declare success merely because a build passes.

FINAL REPORT
- implementation summary
- exact files changed
- tests executed
- functional result
- Anvil result
- working-sector regression result
- LIVE result
- remaining UNKNOWN items
- risks
- documentation status
