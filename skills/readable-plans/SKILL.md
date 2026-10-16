---
name: readable-plans
description: >-
  Use when writing an implementation plan, using plan mode, or turning a
  design into steps a person must approve before coding. Use when a plan is
  getting long enough to skip, or when the user asks for a plan, a route,
  or a planning pass before implementation.
---

# Readable plans

A plan is a route someone can approve before the drive. Write that route. The work starts after they say go.

## Before the document

1. Look at the project long enough to see what already exists.
2. If the request is several independent systems, name the split and plan the first system only.
3. Ask one question at a time. Prefer a short set of choices, with one recommendation.
4. When the route depends on a real choice, offer two or three approaches, recommend one, and say why in a few lines.
5. Get a yes on the approach before writing the plan.
6. Stay in planning until they approve the written route.

## The plan

Write this and stop. One or two screens. Fill every section. Three to seven stops. If a stop needs its own route, it is the next plan.

```markdown
# [Name]

**Outcome:** [One sentence you can check when the work is finished.]

**Already true:** [What exists today that this route builds on.]

**Not on this trip:** [Nearby work you are leaving out.]

## Route

1. [What changes.] [Where it lives.] [The check that says this stop is done.]
2. ...

## Decisions

- [Choice already made, one line.]

## Ask before driving

- [A question that would change the route, or "None."]

## Done when

- [Observable result.]
```

Add a short architecture sketch only when two parts have to talk to each other and the route is unclear without it. A few lines, or a small block. Paths belong in the stops.

## After you write it

Read it once as someone who did not write it. Cut any stop that does not change the outcome, and any sentence you would skip. Then ask: "This is the route. Change a stop, or say go."

Save it when the project already keeps plans, at `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`. Otherwise leave it in the conversation until they say where it belongs.

When they say go, implement the stops in order. A source-level checklist is a separate document, written only if they ask for one.

## Example

The density to hit is a real plan you can finish in one sitting: purpose, what is already true, what is out, a numbered route, and checks. This is the whole plan.

```markdown
# Health check for the API

**Outcome:** `GET /health` returns 200 when the database answers, and 503 when it does not.

**Already true:** The API process starts and serves routes. There is no health route.

**Not on this trip:** Metrics, dashboards, and a deep check of downstream queues.

## Route

1. Add `GET /health` that runs the existing database ping. `src/api/health.py` and the route table. A test gets 200 when the ping succeeds.
2. Map a failed ping to 503 with a stable error body. The same test file. A test gets 503 when the ping fails.
3. Document the route and the two status codes. The API doc page. The page names both codes.

## Decisions

- The check pings the database only.
- No authentication on `/health`.

## Ask before driving

- None.

## Done when

- The two tests pass, and the doc page matches them.
```

## SOL-Lite boundary

This skill provides reasoning guidance only. It does not grant filesystem, terminal, repository, network, skill-install, or application permissions. Runtime policy and explicit approvals remain authoritative.
