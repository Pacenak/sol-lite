"""Inspect, install, update or roll back the offline shared SOL release.

Mutations require an explicit data directory; no network, scripts or services
are activated. This operator CLI does not alter runtime permissions.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "check", "install", "update", "rollback", "read"])
    parser.add_argument("name", nargs="?")
    parser.add_argument("--pack", default="engineering")
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--path", default="SKILL.md")
    parser.add_argument("--sector")
    args = parser.parse_args()
    lite = (ROOT / "src/sol_lite").is_dir()
    if lite:
        sys.path.insert(0, str(ROOT / "src"))
        from sol_lite.skills.catalogue_contract import Catalogue
    else:
        sys.path.insert(0, str(ROOT))
        from services.memory.catalogue_contract import Catalogue
    catalogue = Catalogue(ROOT / "skill_catalogue")
    if args.action == "check":
        result = {"ok": True, "release": catalogue.data["release"], "release_sha256": catalogue.data["release_sha256"], "packages": len(catalogue.entries)}
    elif args.action == "read":
        if not args.name:
            parser.error("read requires a skill name")
        print(catalogue.resource(args.name, args.path))
        return 0
    elif args.action == "list":
        result = [{"name": e["name"], "pack": e["pack"], "default": e["default"], "prerequisites": catalogue.availability(e), "description": e["description"]}
                  for e in catalogue.entries.values() if not args.sector or args.sector in e["sectors"]]
    else:
        if not args.data_root:
            parser.error("mutations require --data-root (Lite data root or Full DATA_DIR)")
        if lite:
            from sol_lite.skills.manager import SkillManager
            manager = SkillManager(ROOT, args.data_root)
            selected = [e["name"] for e in catalogue.entries.values() if e["name"] == args.name] if args.name else [e["name"] for e in catalogue.entries.values() if args.pack == "all" or e["pack"] == args.pack]
            if not selected:
                parser.error("Unknown catalogue skill or pack")
            if args.action == "rollback":
                if not args.name:
                    parser.error("rollback requires a skill name")
                result = manager.rollback_catalogue(args.name)
            else:
                result = [manager.install_catalogue(name, update=args.action == "update") for name in selected]
        else:
            from hub.shared_skill_catalogue import install_pack, rollback
            if args.action == "rollback":
                if not args.name:
                    parser.error("rollback requires a skill name")
                result = rollback(args.data_root, args.name)
            else:
                result = install_pack(args.data_root, pack=args.pack, names=[args.name] if args.name else None, update=args.action == "update")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
