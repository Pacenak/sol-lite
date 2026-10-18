"""Idempotently insert Rick Prime into SOL-Lite's existing agent YAML.

Run from repo root: python scripts/install-rick-prime.py
Do not overwrite unrelated agent definitions.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "agents.yaml"
ENTRY = {
    "name": "Rick Prime",
    "enabled": True,
    "role": "specialist",
    "description": (
        "Frontier scientific research specialist with a Rick Sanchez-inspired, "
        "irreverent engineering persona. Investigates physics, mathematics, "
        "chemistry, geology, astronomy, advanced engineering, numerical models "
        "and unconventional testable hypotheses without confusing speculative "
        "concepts with established evidence."
    ),
    "capabilities": [
        "scientific_research", "theoretical_physics", "applied_physics",
        "advanced_mathematics", "chemistry", "geology", "astronomy",
        "aerospace_engineering", "mechanical_engineering",
        "electrical_engineering", "materials_science",
        "computational_modelling", "numerical_simulation",
        "experimental_design", "fringe_hypothesis_analysis",
        "technical_research", "software_engineering",
    ],
    "can_delegate_to": ["sol_engineer", "sol_docs"],
    "model_profile": "engineer",
}


def install() -> str:
    if not CONFIG.is_file():
        raise FileNotFoundError(f"Missing SOL-Lite config: {CONFIG}")
    original = CONFIG.read_text(encoding="utf-8")
    data = yaml.safe_load(original)
    if not isinstance(data, dict) or not isinstance(data.get("agents"), dict):
        raise ValueError("Expected mapping 'agents' in existing config/agents.yaml")
    old = data["agents"].get("rick_prime")
    if old is not None:
        # Descriptive prose is not an operational setting. Preserve local copy
        # while accepting the equivalent profile shipped with SOL-Lite.
        if not isinstance(old, dict) or {
            key: value for key, value in old.items() if key != "description"
        } != {key: value for key, value in ENTRY.items() if key != "description"}:
            raise ValueError("rick_prime already exists with different settings; reconcile manually")
        return "rick_prime already registered; no change made"
    # Preserve all existing YAML comments and formatting by appending a new peer
    # under the already-present top-level `agents` map. Reject additional top-level
    # mappings (they could absorb the appended entry at a different indentation).
    if set(data) != {"agents"}:
        raise ValueError("Unrecognized top-level mappings: refusing non-preserving insertion")
    snippet = yaml.safe_dump({"rick_prime": ENTRY}, sort_keys=False, allow_unicode=True)
    snippet = "".join("  " + line if line.strip() else line for line in snippet.splitlines(keepends=True))
    candidate = original.rstrip() + "\n\n" + snippet
    verified = yaml.safe_load(candidate)
    if not isinstance(verified, dict) or verified.get("agents", {}).get("rick_prime") != ENTRY:
        raise ValueError("Insertion did not validate")
    for key, value in data["agents"].items():
        if verified["agents"].get(key) != value:
            raise ValueError(f"Existing agent changed unexpectedly: {key}")
    backup = CONFIG.with_suffix(".yaml.pre-rick-prime.bak")
    if backup.exists():
        raise FileExistsError(f"Backup already exists; refusing to overwrite: {backup}")
    shutil.copy2(CONFIG, backup)
    CONFIG.write_text(candidate, encoding="utf-8")
    return f"Registered rick_prime; original preserved in {backup}"


if __name__ == "__main__":
    print(install())
