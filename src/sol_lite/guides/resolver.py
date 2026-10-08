"""Deterministic guide resolver over configured document sources."""
from __future__ import annotations
import json
import re
from pathlib import Path
from .models import Guide, GuideMatch

class GuideResolver:
    def __init__(self, roots: list[str | Path] | None = None):
        self.roots = tuple(Path(p).expanduser().resolve() for p in (roots or []))
        self._guides: list[Guide] = []

    def register(self, guide: Guide) -> None:
        if any(g.identity == guide.identity and g.source == guide.source for g in self._guides):
            raise ValueError(f"Duplicate guide: {guide.identity} from {guide.source}")
        self._guides.append(guide)

    def load(self) -> list[Guide]:
        loaded=[]
        for root in self.roots:
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*.json")):
                try:
                    raw=json.loads(path.read_text(encoding="utf-8"))
                    loaded.append(self._from_mapping(raw, str(path)))
                except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
                    continue
        for guide in loaded:
            try: self.register(guide)
            except ValueError: pass
        return list(self._guides)

    @staticmethod
    def _from_mapping(raw: dict, source: str) -> Guide:
        if not isinstance(raw, dict) or not raw.get("identity"):
            raise ValueError("Guide requires identity")
        def seq(name):
            value=raw.get(name, ())
            return tuple(str(x) for x in value) if isinstance(value, (list, tuple)) else (str(value),)
        return Guide(str(raw["identity"]), str(raw.get("source", source)),
            None if raw.get("version") is None else str(raw["version"]),
            None if raw.get("platform") is None else str(raw["platform"]),
            None if raw.get("target_type") is None else str(raw["target_type"]),
            seq("prerequisites"), seq("procedure"), seq("verification"), seq("rollback"), seq("warnings"),
            {str(k): str(v) for k,v in dict(raw.get("metadata", {})).items()})

    def resolve(self, query: str, *, platform: str | None = None, target_type: str | None = None, limit: int = 5) -> list[GuideMatch]:
        terms={x.lower() for x in re.findall(r"[\w.-]+", query) if len(x)>1}
        matches=[]
        for guide in self._guides:
            score=0.0; reasons=[]
            hay=" ".join((guide.identity,guide.source,guide.platform or "",guide.target_type or "",*guide.prerequisites,*guide.procedure,*guide.verification,*guide.warnings)).lower()
            hits=sum(1 for t in terms if t in hay)
            score += hits / max(1,len(terms))
            if platform and guide.platform and guide.platform.lower()==platform.lower(): score+=0.5; reasons.append("platform")
            if target_type and guide.target_type and guide.target_type.lower()==target_type.lower(): score+=0.5; reasons.append("target_type")
            if hits: reasons.append(f"keyword_hits={hits}")
            if score>0: matches.append(GuideMatch(guide,score,tuple(reasons)))
        return sorted(matches,key=lambda m:(-m.score,m.guide.identity,m.guide.source))[:limit]
