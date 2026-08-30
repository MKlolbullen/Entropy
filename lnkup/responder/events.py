from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ResponderEvent:
    timestamp: str
    level: str
    message: str


_SECRETISH = re.compile(
    r"(?i)(NTLMv[12]?|hash|password|credential)(\s*[:=]\s*)(\S+)"
)


def redact_line(line: str) -> str:
    return _SECRETISH.sub(lambda m: f"{m.group(1)}{m.group(2)}<redacted>", line)


def parse_line(line: str) -> ResponderEvent | None:
    clean = line.strip()
    if not clean:
        return None
    lowered = clean.lower()
    if "error" in lowered or "failed" in lowered:
        level = "ERROR"
    elif "warning" in lowered or "warn" in lowered:
        level = "WARN"
    else:
        level = "INFO"
    return ResponderEvent(
        timestamp=datetime.now().strftime("%H:%M:%S"),
        level=level,
        message=redact_line(clean),
    )
