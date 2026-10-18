"""Build/export the reviewed SOL release. Offline; no bundled code executes.

Review input is produced separately by review-skill-sources.py. Once built,
the committed skill_catalogue directory is the immutable release artifact.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("contract", ROOT / "src/sol_lite/skills/catalogue_contract.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)
RELEASE = "2026.10.18.1"
ALL_SECTORS = ["plg-studio", "dev", "client", "home", "ventures", "red-echo", "plg-film", "project-spicy", "immune", "anvil"]

# Native SOL adaptations. These do not depend on upstream commands, scripts,
# root-level references or framework runtimes. Exact inspiration is pinned below.
SPECS = [
    ("engineering-evidence", "engineering", "Implement, repair or refactor software with an evidence-backed plan and validation.",
     ["fix broken code", "implement a feature", "refactor code", "debug software", "create software"],
     ["addyosmani/agent-skills", "obra/superpowers"],
     ["Read supplied file paths exactly as given, then project instructions, source and relevant tests. Do not relocate a named check into a conventional tests directory without evidence. Use available read-only browsing tools to resolve missing paths. Reproduce the defect or establish a baseline before proposing a cause.",
      "Record the requested outcome, scope and acceptance checks. Separate observed facts, inferred causes, assumptions and unknowns. Ask only for missing requirements that materially change implementation.",
      "Plan small changes with the files and checks that prove them. Create a regression test for a behavioral defect when useful; observe its failure for the expected reason. Do not force test-first work for cosmetic changes.",
      "Make the smallest justified edit using the runtime's native tools. Preserve unrelated edits and public contracts. Check dependency/API versions in the project before using them.",
      "Run relevant checks, inspect exit codes and output, then review the diff against the acceptance criteria. A successful write is not a passing test; a later failed check invalidates earlier completion evidence.",
      "Report changed behavior, exact checks and outcomes, remaining uncertainty and blockers. If validation failed, repair within scope or report incomplete. Never replace tool execution with a plausible narrative."],
     ["filesystem.read", "filesystem.write", "terminal"], [], []),
    ("requirements-discovery", "engineering", "Resolve requirements and acceptance criteria without inventing user decisions.",
     ["clarify requirements", "discover requirements", "review this specification"], ["mattpocock/skills"],
     ["Read supplied requirements and project evidence; identify the actual user, problem, constraints and measurable outcome.",
      "List decisions established by evidence and the few unresolved decisions that affect implementation. Investigate repository questions with tools before asking the user.",
      "Ask a focused question about a consequential unknown; for reversible implementation details, state a reasonable assumption and continue within the request.",
      "Write numbered requirements with acceptance checks and explicit exclusions. Trace subsequent edits and tests to those requirements; explain any proposed scope change."],
     ["filesystem.read"], [], []),
    ("skill-authoring", "engineering", "Create and evaluate a portable SOL skill with precise routing and bounded resources.",
     ["create a skill", "author a skill", "edit a skill"], ["anthropics/skills"],
     ["Inspect existing procedures and select a concrete gap. Draft locally under .agents/skills/<name>/SKILL.md in Lite, or use Full's existing skill editor/import path; agent-authored Full skills remain drafts until reviewed.",
      "Use YAML name and description. Explain when to apply the procedure; keep essential steps in the body and conditional detail in relative reference files. Do not invent tools or slash commands.",
      "Define observable success, missing-dependency behavior and failure reporting. Scripts require separate inspection and normal execution permissions.",
      "Test explicit invocation, one natural-language trigger, an unrelated phrase, a missing prerequisite and a failed check. Include only observed results in the review record.",
      "Promote through the catalogue's reviewed build and hash verification. Never treat writing a manifest as permission to activate it globally."],
     ["filesystem.read", "filesystem.write"], [], []),
    ("web-performance", "web", "Investigate React or Next.js performance using the installed stack and measured evidence.",
     ["react performance", "next.js performance", "reduce frontend bundle"], ["vercel-labs/agent-skills"],
     ["Confirm React/Next.js versions and the application build scripts from manifests; do not apply framework-specific changes to an unrelated engine UI.",
      "Measure a representative route or bundle. Investigate request waterfalls and unnecessary payload before low-impact memoization changes.",
      "Change one bottleneck, preserving rendering semantics, authentication, accessibility and cache isolation. Check the installed framework's current API.",
      "Run the application's tests/build and repeat the same measurement. Report environment and before/after observations; no claimed speedup without a comparable run."],
     ["filesystem.read", "filesystem.write", "terminal"], [], ["node"]),
    ("ui-polish", "design", "Polish an existing UI while preserving the approved visual direction and project tokens.",
     ["polish this ui", "improve ui spacing", "review visual design"], ["JohnWayneeee/ai-agent-skills", "anthropics/skills"],
     ["Inspect the rendered target and source. Identify the user's named problem and read the project's approved tokens; do not substitute a reference brand automatically.",
      "Adjust hierarchy, spacing, alignment, readability and action placement within scope. Avoid unrelated redesign or decorative effects that reduce usability.",
      "Check keyboard behavior, contrast and narrow/wide layouts. Inspect a new render after editing when a preview tool exists.",
      "Distinguish source edits, successful build and actual visual inspection. If no renderer is configured, report that limitation rather than claiming visual approval."],
     ["filesystem.read", "filesystem.write"], [], []),
    ("product-production", "business", "Create source-grounded product briefs, priorities and production milestones.",
     ["write a prd", "plan product production", "prioritize product features"], ["phuryn/pm-skills"],
     ["Read provided research and constraints. Establish the problem, intended users and success metric; label missing evidence instead of inventing interviews or market demand.",
      "Define the smallest release that tests the product assumption. Prioritize explicit tradeoffs using evidence, uncertainty and delivery dependencies.",
      "Write requirements, acceptance checks, exclusions, owners and milestones. Estimates are assumptions or ranges unless supported by measured capacity.",
      "Keep source links next to factual claims and separate proposed dates from commitments. Review the brief for unsupported promises and unresolved decisions."],
     ["filesystem.read", "filesystem.write"], [], []),
    ("statistical-research", "science", "Analyze supplied research data with explicit sampling assumptions and reproducible uncertainty estimates.",
     ["analyze statistical data", "compare experimental groups", "statistical power analysis"], ["K-Dense-AI/scientific-agent-skills"],
     ["Define the estimand, units, sampling design and prespecified comparison before examining outcomes. Preserve input data and record provenance.",
      "Inspect missingness, sample sizes, distributions and dependence. Report design limitations; do not let a diagnostic p-value automatically choose the analysis.",
      "Check installed package versions. Calculate effect estimates and uncertainty with reproducible code, fixed random seeds when applicable, and a justified multiplicity policy.",
      "Distinguish exploration, simulation and measured evidence. Save code and exact outputs; a numerical result does not establish causality or replication."],
     ["filesystem.read", "terminal"], ["numpy", "scipy"], []),
    ("model-evaluation", "research", "Compare model or harness changes with reproducible tasks and recorded execution evidence.",
     ["evaluate a model", "benchmark model quality", "compare agent harnesses"], ["Orchestra-Research/AI-Research-SKILLs"],
     ["Define tasks, scoring criteria and a baseline before tuning. Record model identity, provider, version, inference settings, prompt, tools and dataset revision.",
      "Inspect locally available evaluation tools. Use lm_eval only if installed and compatible; do not fabricate benchmark task names or download models implicitly.",
      "Run matched baseline and candidate trials, preserving per-task results, errors, tool calls and context usage. Separate deterministic fixture tests from live model trials.",
      "Report failure rates and uncertainty across repeated runs. Never extrapolate a passing toy task to full production autonomy."],
     ["filesystem.read", "terminal"], ["lm_eval"], []),
    ("security-diff", "security", "Review an authorized code diff for concrete security regressions and bounded coverage.",
     ["security review this diff", "audit security changes"], ["trailofbits/skills"],
     ["Identify the requested revision range and inspect repository context. Focus first on changed trust boundaries, authentication, authorization and sensitive-data flows.",
      "Trace changed inputs to their consumers. Inspect callers and tests before asserting exploitability; give a concrete trigger and source location for each finding.",
      "Validate hypotheses using local, authorized tests. Distinguish confirmed defects, plausible concerns and unreviewed areas; do not invent a clean audit.",
      "Report severity, impact, reproducible evidence and a minimal remediation. State coverage limits and avoid touching unrelated live systems."],
     ["filesystem.read"], [], []),
    ("container-hardening", "security", "Review container configuration and propose verified hardening for an authorized environment.",
     ["harden docker containers", "review container security"], ["mukul975/Anthropic-Cybersecurity-Skills"],
     ["Inventory the actual Dockerfile, runtime configuration, image source and deployment environment. Do not assume a Docker daemon or remote target is available.",
      "Review user privileges, capabilities, writable paths, mounted sockets, secrets and image provenance against the service's functional requirements.",
      "Propose a configuration diff and rollback. Validate with locally configured Docker tooling; never pull a scanner, restart production or push an image merely because a reference procedure mentions it.",
      "Report observed findings and test output. Mark daemon/host controls unverified unless inspected on an authorized host."],
     ["filesystem.read", "terminal"], [], ["docker"]),
    ("game-production", "game", "Plan and validate a game vertical slice using the actual engine project and available build tools.",
     ["plan a game vertical slice", "debug game build", "validate game assets"], [],
     ["Identify the engine and version from the workspace; inspect gameplay code, asset references and project build instructions. Use Full's existing Studio Unreal tools only when configured.",
      "Define a playable slice with input, gameplay state, persistence, UI/audio and observable acceptance checks. Label placeholder assets and missing interfaces.",
      "Implement one slice and validate with the engine's real compiler/test runner. Check state transitions, deterministic replay where applicable, resource lifetime and asset import errors.",
      "For multiplayer, test serialization, authority and disconnect/reconnect behavior under controlled latency; for performance, record measured frame/memory budgets and environment.",
      "A source edit or mock scene is not a playable build. Report missing SDKs, unrun engine tests and device coverage explicitly."],
     ["filesystem.read", "filesystem.write", "terminal"], [], []),
    ("accounting-evidence", "accounting", "Prepare auditable budgets and ledger reconciliations from supplied records.",
     ["reconcile a ledger", "prepare production budget", "audit invoice totals"], [],
     ["Read source records and identify period, currency, units, tax jurisdiction and chart of accounts. Do not invent invoices, balances, exchange rates or tax rules.",
      "Preserve source identifiers and normalize amounts using decimal arithmetic and an explicit rounding policy. Keep missing values unknown rather than replacing them with zero.",
      "Reconcile opening balance plus movements to closing balance; flag duplicates, mismatches and unexplained differences. Write deterministic checks for totals and rounding.",
      "Produce a draft with traceable source rows and unresolved items. Use SOL's existing Odoo import tools only after checking configured schema and permissions; do not post transactions or file returns through this procedure alone."],
     ["filesystem.read", "filesystem.write", "terminal"], [], []),
    ("infrastructure-change", "infrastructure", "Plan and validate authorized host or operating-system configuration changes with rollback.",
     ["plan infrastructure changes", "diagnose server configuration", "plan os maintenance"], [],
     ["Inspect the configured host inventory, environment and actual service configuration using native tools. Unknown targets or production status require clarification before mutation.",
      "Read logs and identify a testable cause. Prepare a bounded diff, dry-run/check command, health check, backup and rollback.",
      "Apply only the authorized change through runtime permissions. Observe real exit status and service health; do not infer success from a timeout or connection loss.",
      "If health regresses, use the authorized rollback or report the blocker. Keep credentials out of prompts, artifacts and logs."],
     ["filesystem.read", "terminal"], [], []),
    ("context-handoff", "coordination", "Preserve grounded requirements, decisions and tool evidence across sessions or fleet handoffs.",
     ["prepare an agent handoff", "summarize task context", "audit skill pack sync"], [],
     ["Read the current task and execution evidence. Record objective, requirement IDs, approved decisions, modified files, checks and exact unresolved failures.",
      "Separate facts from assumptions; link to source paths and revisions. Summarize only inspected material, preserving uncertainty and denied operations.",
      "For skill-pack transfer compare the actual manifest and content hashes; stage untrusted incoming content and report conflicts. Do not claim remote activation from a successful local export.",
      "Write the handoff with a concrete next action. Verify every named file and result, and preserve local edits and owner/sector boundaries."],
     ["filesystem.read", "filesystem.write"], [], []),
    ("mcp-adapter", "integration", "Build an MCP adapter against actual schemas while preserving SOL permissions and native hosting.",
     ["build an mcp adapter", "integrate an mcp server"], ["anthropics/skills"],
     ["Inspect SOL's existing MCP manager, transport and permission policy before designing an adapter; do not create a second host.",
      "Read the target server's official schema and record transport, version, authentication and tool names. Keep absent tools unavailable; repository listings do not establish a connection.",
      "Implement input/output validation, credential references, timeouts and explicit read/write classification. Avoid retrying a timed-out mutation without checking its actual state.",
      "Test a real configured read, an invalid argument and a denied mutation; keep live write tests scoped to a disposable authorized resource. No credentials or external service are enabled by installing this skill."],
     ["filesystem.read", "filesystem.write", "terminal"], [], []),
]

REFERENCES = {
    "VoltAgent/awesome-agent-skills": "discovery",
    "vercel-labs/skills": "installer-reference",
    "VoltAgent/awesome-design-md": "design-reference",
    "ai-boost/awesome-harness-engineering": "architecture-reference",
    "Shubhamsaboo/awesome-llm-apps": "application-reference",
    "punkpeye/awesome-mcp-servers": "connector-discovery",
    "ripienaar/free-for-dev": "service-discovery",
    "g-shevchenko/utility-skills": "deferred-unverified",
}
UPSTREAM_LICENCES = {"anthropics/skills": "Apache-2.0", "trailofbits/skills": "CC-BY-SA-4.0",
                     "mukul975/Anthropic-Cybersecurity-Skills": "Apache-2.0"}


def build(review: Path):
    target = ROOT / "skill_catalogue"
    target.mkdir(exist_ok=True)
    sources, reviews = [], {}
    for repo in sorted({repo for item in SPECS for repo in item[4]}):
        folder = review / repo.replace("/", "--")
        data = json.loads((folder / "review.json").read_text(encoding="utf-8"))
        if not data["selected"]:
            raise ValueError("No inspected skill in " + repo)
        reviews[repo] = data
        notices = ["upstream/" + repo.replace("/", "--") + "/" + e["path"] + ".txt" for e in data["evidence"] if not e["path"].endswith("SKILL.md")]
        sources.append({"repository": repo, "url": "https://github.com/" + repo, "role": "adapted-procedures", "commit": data["commit"], "license": UPSTREAM_LICENCES.get(repo, "MIT"), "license_evidence": notices or ["Skill frontmatter at pinned path"]})
        for evidence in data["evidence"]:
            content = (folder / (evidence["path"] + ".txt")).read_bytes()
            if contract.digest(content) != evidence["sha256"]:
                raise ValueError("Review input changed")
            output = target / "upstream" / repo.replace("/", "--") / (evidence["path"] + ".txt")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(content)
    sources += [{"repository": repo, "url": "https://github.com/" + repo, "role": role} for repo, role in REFERENCES.items()]
    skills = []
    for slug, pack, description, triggers, repos, steps, tools, modules, commands in SPECS:
        name = "sol-" + slug
        sectors = ["plg-studio", "dev", "client", "immune"] if pack in {"security", "infrastructure"} else ["plg-studio", "dev"] if pack == "game" else ALL_SECTORS
        agents = ["sol_engineer", "rick_prime"] if pack in {"engineering", "web", "security", "infrastructure", "game", "integration"} else ["sol_pa", "sol_business"] if pack in {"business", "accounting"} else ["rick_prime", "sol_engineer"] if pack in {"science", "research"} else ["sol_pa", "sol_business", "sol_docs", "sol_engineer", "rick_prime"]
        license_name = "CC-BY-SA-4.0" if slug == "security-diff" else "LicenseRef-SOL"
        upstream = []
        for repo in repos:
            review_data = reviews[repo]
            for path in review_data["selected"]:
                evidence = next(e for e in review_data["evidence"] if e["path"] == path)
                upstream.append({"repository": repo, "commit": review_data["commit"], "path": path, "license": UPSTREAM_LICENCES.get(repo, "MIT"), "sha256": evidence["sha256"], "evidence": "upstream/" + repo.replace("/", "--") + "/" + path + ".txt"})
        folder = target / "packages" / name
        folder.mkdir(parents=True, exist_ok=True)
        # Flat fields are compatible with both Full's minimal YAML parser and Lite.
        frontmatter = {"name": name, "description": description, "version": "1.0.0", "category": "general", "source": "adapted" if upstream else "native", "license": license_name, "license_note": "SOL-native adaptation; upstream evidence and notices are in the shared release. " + ", ".join(repos), "status": "published", "sectors": sectors, "tags": ["sol-catalogue", pack]}
        body = "---\n" + "\n".join(key + ": " + json.dumps(value, ensure_ascii=False) for key, value in frontmatter.items()) + "\n---\n\n"
        body += "## When to Use\n\n" + description + "\n\n## Procedure\n\n"
        body += "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1))
        body += "\n\n## Pitfalls\n\nSkills do not grant permissions or tool access. Report missing prerequisites and failed checks; never manufacture execution evidence.\n\n## Verification\n\nMap each claimed outcome to an observed result. Read [the acceptance rubric](references/acceptance.md) when validating this procedure.\n"
        (folder / "SKILL.md").write_text(body, encoding="utf-8", newline="\n")
        (folder / "references").mkdir(exist_ok=True)
        reference = "# Acceptance rubric\n\n- Success: supply real inputs, use native tools and check the output against the requested outcome. Record tool names and actual results.\n- Missing prerequisite: remove a required tool or dependency; report unavailable with the missing item and do not claim execution.\n- Failure: force a validation error; preserve its evidence and report incomplete until a subsequent relevant check succeeds.\n- Scope: try an unrelated phrase and a forbidden owner/sector; this package must not become an alternate permission path.\n- Evaluation: deterministic contract tests prove routing and integrity only. Live model and external service acceptance remains unverified until run.\n"
        (folder / "references/acceptance.md").write_text(reference, encoding="utf-8", newline="\n")
        files = contract.file_hashes(folder)
        skills.append({"id": "sol/" + slug, "name": name, "description": description, "pack": pack, "version": "1.0.0", "default": pack == "engineering", "runtimes": ["lite", "full"], "agents": agents, "sectors": sectors, "triggers": triggers, "license": license_name, "upstream": upstream, "adaptation": "Native SOL procedure; upstream scripts/resources are not execution dependencies.", "requires_tools": tools, "requires_python": modules, "requires_commands": commands, "files": files, "sha256": contract.json_digest(files), "evaluation": {"contract": "tests/unit/test_shared_catalogue.py and Full tests/test_shared_skill_catalogue.py", "live_model": "unverified", "external_services": "unverified"}})
    evidence_files = {p.relative_to(target).as_posix(): contract.digest(p.read_bytes()) for p in sorted((target / "upstream").rglob("*")) if p.is_file()}
    data = {"schema_version": 1, "release": RELEASE, "sources": sources, "skills": skills, "evidence_files": evidence_files, "background_reading": ["https://www.linkedin.com/pulse/ai-engineering-skills-map-software-fundamentals-andrew-ng-7lnac/", "https://agnt.gg/articles/agents/100-best-ai-agent-skills"]}
    data["release_sha256"] = contract.json_digest(data)
    (target / "catalogue.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    contract.Catalogue(target)
    print("Built", RELEASE, len(skills), "native packages from", len(reviews), "pinned repositories")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path)
    parser.add_argument("--full-root", type=Path)
    args = parser.parse_args()
    if args.review_dir:
        build(args.review_dir)
    catalogue = contract.Catalogue(ROOT / "skill_catalogue")
    if args.full_root:
        full = args.full_root.resolve()
        if not (full / "services/memory/skills.py").is_file():
            raise ValueError("Expected SOL-Full repository")
        shutil.copytree(ROOT / "skill_catalogue", full / "skill_catalogue", dirs_exist_ok=True)
        shutil.copy2(ROOT / "src/sol_lite/skills/catalogue_contract.py", full / "services/memory/catalogue_contract.py")
        contract.Catalogue(full / "skill_catalogue")
        for sector in ALL_SECTORS:
            pins = full / "branches" / sector / "skills/workflow-prompts.import.json"
            if not pins.is_file():
                continue
            data = json.loads(pins.read_text(encoding="utf-8"))
            names = {item["name"] for item in data["skills"]}
            for entry in catalogue.entries.values():
                if entry["default"] and sector in entry["sectors"] and entry["name"] not in names:
                    data["skills"].append({"name": entry["name"], "description": entry["description"], "version": entry["version"], "category": "general", "status": "published", "source": "adapted", "tags": ["sol-catalogue", entry["pack"]], "sectors": entry["sectors"], "content_path": "data/skills/general/" + entry["name"] + "/SKILL.md"})
            pins.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print("Exported identical release", catalogue.data["release_sha256"], "to", full)


if __name__ == "__main__":
    main()
