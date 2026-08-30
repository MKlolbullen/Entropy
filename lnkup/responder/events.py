from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class ResponderEvent:
    timestamp: str
    level: str
    protocol: str
    event_type: str
    source: str | None
    identity: str | None
    name: str | None
    scope: str
    correlation_id: str | None
    correlation_count: int
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


_SECRETISH = re.compile(r"(?i)(NTLMv[12]?(?:-SSP)?\s*(?:Hash)?|hash|password|credential)(\s*[:=]\s*)(\S+)")
_IPV4 = re.compile(r"(?<![0-9])((?:\d{1,3}\.){3}\d{1,3})(?![0-9])")
_PROTOCOL = re.compile(r"\[([A-Za-z0-9_-]{2,16})\]")
_USERNAME = re.compile(r"(?i)(?:username|user)\s*[:=]\s*([^\s]+)")
_NAME = re.compile(r"(?i)(?:for\s+name|name)\s*[:=]?\s*([^\s]+)")


def redact_line(line: str) -> str:
    return _SECRETISH.sub(lambda m: f"{m.group(1)}{m.group(2)}<redacted>", line)


def parse_line(line: str) -> ResponderEvent | None:
    clean = line.strip()
    if not clean:
        return None
    safe = redact_line(clean)
    lowered = safe.lower()
    protocol_match = _PROTOCOL.search(safe)
    protocol = protocol_match.group(1).upper() if protocol_match else "SYSTEM"
    source_match = _IPV4.search(safe)
    identity_match = _USERNAME.search(safe)
    name_match = _NAME.search(safe)
    if "poisoned answer" in lowered or ("poison" in lowered and protocol in {"LLMNR", "NBT-NS", "MDNS"}):
        event_type = "name_resolution_observed"
    elif any(term in lowered for term in ("username", "ntlmv1", "ntlmv2", "authentication")):
        event_type = "authentication_observed"
    elif "listening" in lowered or "server started" in lowered:
        event_type = "listener_status"
    elif "query" in lowered or "request" in lowered:
        event_type = "request_observed"
    elif "error" in lowered or "failed" in lowered:
        event_type = "error"
    else:
        event_type = "log"
    level = "ERROR" if event_type == "error" else "WARN" if "warning" in lowered or "warn" in lowered else "INFO"
    return ResponderEvent(
        timestamp=datetime.now(timezone.utc).isoformat(), level=level, protocol=protocol,
        event_type=event_type, source=source_match.group(1) if source_match else None,
        identity=identity_match.group(1) if identity_match else None,
        name=name_match.group(1) if name_match else None, scope="UNKNOWN",
        correlation_id=None, correlation_count=0, message=safe,
    )
