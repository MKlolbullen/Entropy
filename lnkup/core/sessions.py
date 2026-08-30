from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class RunSession:
    run_id: str
    directory: Path
    started_at: str

    @property
    def manifest_path(self) -> Path:
        return self.directory / "manifest.json"

    @property
    def events_path(self) -> Path:
        return self.directory / "events.jsonl"


class RunStore:
    def __init__(self, root: Path | str = "runs") -> None:
        self.root = Path(root)
        self.current: RunSession | None = None

    def start(self, metadata: dict[str, Any] | None = None) -> RunSession:
        now = datetime.now(timezone.utc)
        run_id = f"{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        directory = self.root / run_id
        directory.mkdir(parents=True, exist_ok=False)
        session = RunSession(run_id=run_id, directory=directory, started_at=now.isoformat())
        manifest = {
            "schema": 1,
            "run_id": run_id,
            "started_at": session.started_at,
            "ended_at": None,
            "metadata": metadata or {},
        }
        session.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        session.events_path.touch()
        self.current = session
        return session

    def append_event(self, event: dict[str, Any]) -> None:
        if not self.current:
            return
        record = {"run_id": self.current.run_id, **event}
        with self.current.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def finish(self, metadata: dict[str, Any] | None = None) -> None:
        if not self.current:
            return
        manifest = json.loads(self.current.manifest_path.read_text(encoding="utf-8"))
        manifest["ended_at"] = datetime.now(timezone.utc).isoformat()
        if metadata:
            manifest.setdefault("result", {}).update(metadata)
        self.current.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        self.current = None
