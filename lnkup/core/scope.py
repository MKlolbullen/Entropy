from __future__ import annotations

import ipaddress
from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class EngagementScope:
    name: str = "Unscoped analysis"
    allowed_cidrs: list[str] = field(default_factory=list)
    excluded_cidrs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = self.name.strip() or "Unscoped analysis"
        self.allowed_cidrs = _normalize_networks(self.allowed_cidrs)
        self.excluded_cidrs = _normalize_networks(self.excluded_cidrs)

    def classify(self, address: str | None) -> str:
        if not address:
            return "UNKNOWN"
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return "UNKNOWN"
        excluded = [ipaddress.ip_network(value, strict=False) for value in self.excluded_cidrs]
        if any(ip in network for network in excluded):
            return "OUT"
        if not self.allowed_cidrs:
            return "UNKNOWN"
        allowed = [ipaddress.ip_network(value, strict=False) for value in self.allowed_cidrs]
        return "IN" if any(ip in network for network in allowed) else "OUT"

    def to_dict(self) -> dict:
        return asdict(self)


def parse_network_text(value: str) -> list[str]:
    items = [item.strip() for item in value.replace(";", ",").replace("\n", ",").split(",")]
    return _normalize_networks([item for item in items if item])


def _normalize_networks(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        network = ipaddress.ip_network(value.strip(), strict=False)
        text = str(network)
        if text not in normalized:
            normalized.append(text)
    return normalized
