02 — ROOT-CAUSE INVESTIGATION
Mission

Determine the actual technical root cause of a verified defect.

This phase is READ-ONLY.

Do not implement changes.

The goal is causal proof, not plausible explanation.

1. Root-Cause Standard

A root cause must explain:

Why the observed failure occurs.
Why the expected behavior does not occur.
Why the failure is located at the identified implementation point.
Why working paths do not exhibit the same failure.
Why the proposed correction would remove the failure.

A difference is not automatically a root cause.

A suspicious line is not automatically a root cause.

A documentation mismatch is not automatically a root cause.

2. Build the Failure Graph

Construct:

Trigger
 ↓
Entry Point
 ↓
State
 ↓
Transformation
 ↓
Dependency
 ↓
Decision / Filter
 ↓
Output
 ↓
Observed Failure

For every transition identify concrete evidence.

3. Compare With Working Implementations

For issues involving multiple sectors, compare at least two known working sectors.

Build a comparison table:

Layer	Working A	Working B	Failing Path	Difference
Entry	...	...	...	...
State	...	...	...	...
API	...	...	...	...
Backend	...	...	...	...
Registry	...	...	...	...
Filtering	...	...	...	...
Rendering	...	...	...	...

Then determine which differences are causally relevant.

4. Persona / Anvil Investigation

If the defect involves personas:

Inspect:

persona definitions
persona registry
discovery functions
registration
persistence
backend APIs
API clients
frontend state
Anvil components
working sector components
filters
permission policies
MCP policies
filesystem policies
model policies
configuration
feature flags
initialization lifecycle

Explicitly determine:

Where personas originate
→ How they are registered
→ How they are discovered
→ How they are returned
→ How Anvil consumes them
→ How Anvil filters them
→ How Anvil renders them

Then perform the same trace for at least two working sectors.

5. Lifecycle Analysis

Check whether the defect is caused by timing or lifecycle:

initialization before registry load
stale cache
state hydration
asynchronous request ordering
server/client rendering boundary
dependency-array errors
missing refresh
stale closure
lazy loading
route transition
conditional mounting
provider scope

Do not claim lifecycle causality without evidence.

6. Configuration Analysis

Check:

environment variables
defaults
feature flags
policy configuration
sector configuration
persona configuration
API base URLs
server/client configuration boundaries

Distinguish:

[VERIFIED] Configuration exists.

from:

[VERIFIED] Configuration causes this behavior.

7. API Contract Analysis

Verify:

route
HTTP method
parameters
authentication
authorization
request schema
response schema
error behavior
frontend parsing

Check for contract drift between frontend and backend.

8. Test the Causal Hypothesis

Use read-only evidence to challenge the suspected root cause.

Ask:

Does the suspected condition actually occur?
Does removing the condition conceptually explain the observed behavior?
Does the working implementation avoid that condition?
Are there alternative explanations?
Does the evidence distinguish between them?

Do not modify production/source code to test the hypothesis during this phase.

Use existing tests or safe diagnostics where available.

9. Root-Cause Verdict

Use exactly one:

VERIFIED ROOT CAUSE

The evidence establishes causality.

PROBABLE ROOT CAUSE

Strong evidence exists but one or more causal links remain unverified.

UNKNOWN

Insufficient evidence.

Never label a probable cause as verified.

10. Required Root-Cause Record
DEFECT:
REPRODUCTION:
EXPECTED:
ACTUAL:

ROOT CAUSE STATUS:
ROOT CAUSE:

AFFECTED FILES:
AFFECTED SYMBOLS:

EXECUTION PATH:

WORKING PATH COMPARISON:

EVIDENCE:

CONTRADICTING EVIDENCE:

WHY THE FAILURE OCCURS:

WHY WORKING PATHS SUCCEED:

MINIMUM CORRECT FIX:

FILES THAT MUST CHANGE:

FILES THAT MUST NOT CHANGE:

VALIDATION REQUIRED:

REGRESSION RISKS:

OPEN QUESTIONS:
11. Mandatory Stop

Do not modify the workspace.

Do not implement the fix.

Return the verified root cause and an engineering backlog suitable for the planning phase.