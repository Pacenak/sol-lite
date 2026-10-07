# 01 — VERIFICATION, REPRODUCTION AND EVIDENCE

## Mission

Challenge the existing baseline and independently verify the reported engineering issue.

This phase is strictly **READ-ONLY**.

The goal is to determine:

1. What is actually broken.
2. Whether the issue can be reproduced.
3. What exact behavior occurs.
4. What exact behavior is expected.
5. Where implementation behavior diverges from expected behavior.
6. What evidence is still missing.

Do not implement a fix.

---

# 1. Evidence Standard

Use:

* `[VERIFIED]`
* `[INFERRED]`
* `[UNKNOWN]`

Also identify the evidence domain:

* `[WORKSPACE]`
* `[LIVE]`
* `[GITEA]`
* `[TEST]`
* `[DOCS]`

Example:

`[VERIFIED][WORKSPACE] Anvil calls getPersonas().`

Do not convert documentation claims into runtime claims.

---

# 2. Start From the Reported Failure

Restate the reported issue precisely.

Identify:

* affected feature
* affected user action
* expected behavior
* observed behavior
* affected component
* reproduction conditions
* known environment

If the report is ambiguous, identify the ambiguity instead of guessing.

---

# 3. Reproduction

Attempt to reproduce the defect using available read-only tools and runtime-safe commands.

Where possible:

* start/use an already available development environment
* query relevant APIs
* inspect application state
* inspect logs
* run existing tests
* inspect browser/runtime evidence
* reproduce the original operation

Do not mutate application state unless explicitly authorized by the task.

If reproduction succeeds:

`[VERIFIED][LIVE] Exact reproduction observed.`

Record:

* command/action
* input
* environment
* response
* output
* error
* timestamp if relevant

If reproduction fails:

`[UNKNOWN] Unable to reproduce with current evidence.`

Do not manufacture a failure.

---

# 4. Trace the Execution Path

Trace the affected behavior from entry point to outcome.

Use this structure:

```
User action
→ UI component
→ state/hook/store
→ API/client
→ HTTP request
→ backend route
→ controller/handler
→ service
→ repository/data source
→ response
→ frontend state
→ rendering
```

Only include layers actually verified.

For each layer record:

* file
* symbol
* input
* output
* transformation
* caller
* consumer

---

# 5. Data-Flow Verification

Determine the exact data entering and leaving each relevant layer.

Check:

* IDs
* names
* types
* arrays
* objects
* null values
* defaults
* filters
* permissions
* feature flags
* configuration
* serialization
* deserialization

Look specifically for:

* dropped records
* incorrect filters
* incorrect defaults
* stale state
* mismatched field names
* inconsistent IDs
* incorrect route parameters
* error swallowing
* race conditions
* loading-order issues

Do not call a suspected issue the root cause yet.

---

# 6. Anvil-Specific Verification

If the issue concerns Anvil/personas, independently trace Anvil.

Then trace at least two working sectors.

For each:

```
Frontend entry
→ state
→ API/client
→ backend route
→ service
→ persona registry/discovery
→ persona data
→ filtering
→ rendering
```

Compare exact implementation.

Compare:

* functions
* hooks
* components
* state variables
* API endpoints
* request parameters
* response parsing
* filtering
* registration
* configuration
* lifecycle
* loading timing
* error handling
* feature flags
* permission checks

Do not conclude that a difference is the root cause merely because it exists.

---

# 7. Tests

Run relevant existing read-only tests where possible.

For each result:

* exact command
* exit code
* relevant output
* what it proves
* what it does not prove

A passing build does not prove a runtime feature works.

A passing unit test does not prove the entire feature works.

---

# 8. Reproduction Matrix

Create a matrix:

| Behavior         | Expected | Actual | Evidence | Status           |
| ---------------- | -------- | ------ | -------- | ---------------- |
| Reported case    | ...      | ...    | ...      | VERIFIED/UNKNOWN |
| Working sector A | ...      | ...    | ...      | ...              |
| Working sector B | ...      | ...    | ...      | ...              |
| Anvil            | ...      | ...    | ...      | ...              |

---

# 9. Root-Cause Candidate List

Only after tracing the implementation, list candidate causes.

For each:

* candidate
* evidence supporting it
* evidence contradicting it
* missing evidence
* confidence

Do not select a root cause until the evidence supports causality.

---

# 10. Required Finding Format

For every confirmed defect:

## Defect

## Reproduction

## Expected Behavior

## Actual Behavior

## Execution Path

## Data Flow

## Verified Evidence

## Contradicting Evidence

## Root-Cause Candidates

## Remaining Unknowns

## Verification Status

---

# 11. Mandatory Stop

Do not modify files.

Do not implement fixes.

Do not claim resolution.

End with:

1. confirmed defects
2. reproducibility status
3. evidence
4. candidate causes
5. verified root cause if one is actually proven
6. unresolved questions
7. recommended next investigation steps
