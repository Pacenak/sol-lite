# Shared skill catalogue

SOL-Lite and SOL-Full ship the same offline release in `skill_catalogue/`.
`catalogue.json` records exact upstream commits and evidence hashes, native
package hashes, roles/sectors, dependencies and execution requirements. Original
upstream evidence and licence notices are retained separately from active skills.

The release contains 15 SOL procedures drawn from 11 pinned repositories plus
SOL-native domain workflows. The source roster also records seven reference or
discovery repositories and the deferred utility repository. Articles, service
directories and MCP lists are references, not automatically installed services.

## Everyday use

The engineering baseline includes `sol-engineering-evidence`,
`sol-requirements-discovery` and `sol-skill-authoring`. Lite exposes these to
their declared agent roles. Full installs them through startup-data import and
pins them through existing sector workflow files. Existing local copies survive
startup refreshes and release updates.

In Lite, use the native shell:

```text
/skills catalogue list
/skills catalogue install sol-game-production
/skills catalogue update sol-game-production
/skills catalogue rollback sol-game-production
/skills read sol-game-production references/acceptance.md
```

Catalogue installation retains the normal skill-install permission check. Select
the appropriate agent role first. Invoke a selected skill in a task with
`$sol-game-production`. Agents can use `skill_read` to read a manifest or a
relative reference; reads cannot escape the skill directory.

Both products include an offline operator CLI:

```text
python scripts/skill-catalogue.py check
python scripts/skill-catalogue.py list
python scripts/skill-catalogue.py read sol-engineering-evidence
python scripts/skill-catalogue.py install --pack game --data-root ./data
python scripts/skill-catalogue.py install --pack all --data-root ./data
python scripts/skill-catalogue.py update sol-game-production --data-root ./data
python scripts/skill-catalogue.py rollback sol-game-production --data-root ./data
```

Use the configured Lite data root or Full `DATA_DIR` in place of `./data`.
This CLI is an operator tool; it does not grant runtime tool permissions.
`install` fills missing packages. `update` replaces only an unchanged package
previously managed by the catalogue, saving the previous version. A local
override is reported and left intact. Rollback refuses modified local content
and verifies the saved snapshot before restoring it. The first installation has
no prior release to roll back to.

Full also exposes authenticated `GET /api/skills/catalogue?sector=plg-studio`.
Admins can use `POST /api/skills/catalogue/install` with
`{"pack":"game"}` or `{"names":["sol-game-production"],"update":true}`;
`POST /api/skills/catalogue/rollback/sol-game-production` restores the previous
managed release. Execution remains in the existing Outpost skill invocation
path. Installed Full skills retain the normal owner and sector filtering;
explicit invocation follows Full's existing published-library policy.

## Packs

- `engineering`: grounded implementation, requirements and skill authoring.
- `web`, `design`: stack-aware performance work and scoped visual polish.
- `business`: product discovery, prioritisation and production planning.
- `science`, `research`: statistical analysis and reproducible model evaluation.
- `security`: differential code review and authorized container hardening.
- `game`: engine-aware vertical-slice, asset and build validation procedures.
- `accounting`: source-grounded budgets, decimal calculations and reconciliation.
- `infrastructure`: bounded changes, health checks and rollback.
- `coordination`: evidence-preserving handoff and pack-conflict investigation.
- `integration`: MCP adapter development through the existing runtime host.

Optional procedures install independently of their execution dependencies. The
catalogue reports missing Python modules and commands. Availability is a
prerequisite report, not proof of credentials, network connectivity, a compatible
engine SDK, permissions or successful execution. No model, library, scanner,
account or MCP service is enabled merely by installing a package.

## Authoring and promotion

Users or agents can draft a normal skill through the existing workspace/editor
workflow described in [Adding a skill](../development/adding-a-skill.md). Test it
locally before adding it to a shared release. A draft is not automatically a
trusted package.

Release maintainers select exact upstream inputs with
`scripts/review-skill-sources.py`, inspect bodies and licences, and author SOL
adaptations in `scripts/build-skill-catalogue.py`. The builder records the source
commit, original content hash, package hash, attribution and compatibility.
New supporting resources must be listed in the package file manifest. Large
resources are not automatically injected into the prompt.
Bump the builder's release identifier before publishing changed package content.

Build offline from the reviewed input, then export to the actual Full checkout:

```text
python scripts/build-skill-catalogue.py --review-dir <review-directory>
python scripts/build-skill-catalogue.py --full-root <SOL-Full-checkout>
```

Both loaders use the same standard-library contract module. The export copies
that module and the release byte-for-byte and fills missing baseline sector
pins. Keep old release artifacts in Git; managed installations retain one prior
package snapshot for rollback. Manifest hashes establish integrity against the
reviewed release, not independent publisher authentication. Only an operator's
reviewed repository/release should be promoted.

Before promotion, check explicit/automatic routing, unrelated requests, missing
resources, missing dependencies, content tampering, owner/sector filtering and
local-edit preservation. Run the engineering smoke fixture with real tools:

```text
python scripts/smoke-skill-harness.py --provider scripted --output <new-results-directory>
python scripts/smoke-skill-harness.py --provider ollama --model <installed-model> --output <new-results-directory>
```

The scripted mode proves adapter wiring. Ollama mode records actual model calls,
tool failures, context usage and an independent immutable fixture check for both
control and curated runs. Neither proves general autonomy or zero hallucinations.
Full's live model/provider and domain-specific external integrations require
their own acceptance runs before being advertised as verified capabilities.
