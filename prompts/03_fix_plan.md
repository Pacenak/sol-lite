FIX PLANNING — NO IMPLEMENTATION

Use only verified findings from discovery and verification.

Do not modify files.

For every proposed change provide:
- task
- priority
- exact file
- exact symbol
- current behavior
- expected behavior
- verified root cause
- exact code/config change
- rationale
- dependencies
- risks
- validation
- documentation impact

SEPARATE:
REQUIRED CHANGES
OPTIONAL CHANGES
MUST-NOT-CHANGE ITEMS

For the Anvil/persona issue:
- preserve working-sector behavior
- avoid broad refactors unless required by the verified root cause
- fix the actual discovery/registration/data-flow defect
- do not change unrelated persona logic
- do not change working sectors merely to make them look like Anvil

Before implementation, call request_approval with one complete implementation plan.

The plan must identify every intended write.

Do not implement anything.
Wait for explicit human approval of the returned plan ID.
