"""Fetch immutable upstream evidence for catalogue review; never execute it.

Run with network access: python scripts/review-skill-sources.py <output-directory>
The output is review input, not a trusted release or an installed skill.
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

SOURCES = {
    "anthropics/skills": ["skill-creator", "mcp-builder", "webapp-testing", "frontend-design"],
    "addyosmani/agent-skills": ["spec", "test", "review"],
    "obra/superpowers": ["verification-before-completion"],
    "mattpocock/skills": ["grill-me", "grilling"],
    "vercel-labs/agent-skills": ["react-best-practices"],
    "phuryn/pm-skills": ["create-prd"],
    "JohnWayneeee/ai-agent-skills": ["ui-final-polish"],
    "K-Dense-AI/scientific-agent-skills": ["statistical-analysis"],
    "Orchestra-Research/AI-Research-SKILLs": ["lm-evaluation-harness"],
    "trailofbits/skills": ["differential-review"],
    "mukul975/Anthropic-Cybersecurity-Skills": ["hardening-docker-containers-for-production"],
}


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "SOL-skill-provenance-review"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read(16 * 1024 * 1024 + 1)
    if len(data) > 16 * 1024 * 1024:
        raise ValueError("Upstream response exceeds review size limit")
    return data


def main():
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    for repo, words in SOURCES.items():
        if len(sys.argv) > 2 and repo not in sys.argv[2:]:
            continue
        destination = output / repo.replace("/", "--")
        destination.mkdir(exist_ok=True)
        try:
            commit = json.loads(fetch(f"https://api.github.com/repos/{repo}/commits/HEAD"))["sha"]
            tree = json.loads(fetch(f"https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1"))
            if tree.get("truncated"):
                raise ValueError("Truncated tree; select paths manually")
            paths = [item["path"] for item in tree["tree"] if item["type"] == "blob"]
            skills = [path for path in paths if path.endswith("/SKILL.md")]
            selected = [path for path in skills if any(word in path.lower() for word in words)]
            licences = [path for path in paths if "/" not in path and path.lower().startswith(("license", "licence", "copying", "notice"))]
            # Preserve per-package licence files, when provided, as well.
            parents = {path.rsplit("/", 1)[0] for path in selected}
            licences += [path for path in paths if path.rsplit("/", 1)[0] in parents and path.rsplit("/", 1)[-1].lower().startswith(("license", "licence", "notice"))]
            evidence = []
            for path in sorted(set(selected + licences)):
                content = fetch(f"https://raw.githubusercontent.com/{repo}/{commit}/{path}")
                local = destination / (path + ".txt")
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_bytes(content)
                evidence.append({"path": path, "sha256": hashlib.sha256(content).hexdigest()})
            metadata = {"repository": repo, "commit": commit, "skills": skills, "selected": selected, "evidence": evidence}
            (destination / "review.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            print(repo, commit, json.dumps(selected), flush=True)
        except Exception as error:
            print(repo, "REVIEW FAILED:", str(error), flush=True)


if __name__ == "__main__":
    main()
