from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class CorrelationState:
    correlation_id: str
    count: int


class EventCorrelator:
    """Correlate observations by source + queried name inside a short time window."""

    def __init__(self, window_seconds: int = 60) -> None:
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[datetime]] = defaultdict(list)

    def reset(self) -> None:
        self._buckets.clear()

    def correlate(self, event) -> CorrelationState:
        key = "|".join([event.source or "unknown", event.name or ""])
        now = datetime.fromisoformat(event.timestamp)
        cutoff = now.timestamp() - self.window_seconds
        self._buckets[key] = [stamp for stamp in self._buckets[key] if stamp.timestamp() >= cutoff]
        self._buckets[key].append(now)
        token = hashlib.sha256(key.encode()).hexdigest()[:10]
        return CorrelationState(correlation_id=f"corr-{token}", count=len(self._buckets[key]))
