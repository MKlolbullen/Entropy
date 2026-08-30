from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .scope import EngagementScope


@dataclass(slots=True)
class EngagementTemplate:
    name: str
    description: str
    allowed_cidrs: list[str]
    excluded_cidrs: list[str]

    def scope(self) -> EngagementScope:
        return EngagementScope(self.name, self.allowed_cidrs, self.excluded_cidrs)


def built_in_templates() -> list[EngagementTemplate]:
    return [
        EngagementTemplate("Unscoped analysis", "Observe without classifying sources as in-scope.", [], []),
        EngagementTemplate("Private lab", "RFC1918 lab ranges; customize exclusions before use.", ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"], []),
        EngagementTemplate("Documentation lab", "RFC 5737 documentation networks for demos and screenshots.", ["192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24"], []),
    ]


def user_template_dir() -> Path:
    path = Path.home() / ".config" / "lnk-ng" / "engagements"
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_templates() -> list[EngagementTemplate]:
    result = built_in_templates()
    for path in sorted(user_template_dir().glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            result.append(EngagementTemplate(**data))
        except Exception:
            continue
    return result


def save_template(template: EngagementTemplate) -> Path:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in template.name).strip("-") or "template"
    path = user_template_dir() / f"{safe}.json"
    path.write_text(json.dumps(asdict(template), indent=2), encoding="utf-8")
    return path
