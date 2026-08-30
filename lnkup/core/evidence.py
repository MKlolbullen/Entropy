from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EvidenceRun:
    run_id: str
    directory: Path
    manifest: dict[str, Any]
    event_count: int


def list_runs(root: str | Path = "runs") -> list[EvidenceRun]:
    root_path = Path(root)
    if not root_path.is_dir():
        return []
    result: list[EvidenceRun] = []
    for directory in root_path.iterdir():
        if not directory.is_dir():
            continue
        manifest_path = directory / "manifest.json"
        if not manifest_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        events_path = directory / "events.jsonl"
        event_count = 0
        if events_path.is_file():
            with events_path.open("r", encoding="utf-8", errors="replace") as handle:
                event_count = sum(1 for line in handle if line.strip())
        result.append(EvidenceRun(
            run_id=str(manifest.get("run_id") or directory.name),
            directory=directory,
            manifest=manifest,
            event_count=event_count,
        ))
    return sorted(result, key=lambda run: run.manifest.get("started_at", ""), reverse=True)


def load_events(run: EvidenceRun) -> list[dict[str, Any]]:
    path = run.directory / "events.jsonl"
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def export_bundle(run: EvidenceRun, destination: str | Path) -> Path:
    destination = Path(destination).expanduser()
    if destination.suffix.lower() != ".zip":
        destination = destination.with_suffix(".zip")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ("manifest.json", "events.jsonl"):
            source = run.directory / name
            if source.is_file() and not source.is_symlink():
                archive.write(source, arcname=f"{run.run_id}/{name}")
    return destination.resolve()
