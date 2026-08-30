from __future__ import annotations

import json
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .integrity import verify_integrity


@dataclass(slots=True)
class EvidenceRun:
    run_id: str
    directory: Path
    manifest: dict[str, Any]
    event_count: int
    integrity: str


def list_runs(root: str | Path = "runs") -> list[EvidenceRun]:
    root_path = Path(root)
    if not root_path.is_dir():
        return []
    result: list[EvidenceRun] = []
    for directory in root_path.iterdir():
        manifest_path = directory / "manifest.json"
        if not directory.is_dir() or not manifest_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        events_path = directory / "events.jsonl"
        event_count = sum(1 for line in events_path.open("r", encoding="utf-8", errors="replace") if line.strip()) if events_path.is_file() else 0
        ok, _ = verify_integrity(directory)
        result.append(EvidenceRun(str(manifest.get("run_id") or directory.name), directory, manifest, event_count, "VERIFIED" if ok else "UNVERIFIED"))
    return sorted(result, key=lambda run: run.manifest.get("started_at", ""), reverse=True)


def load_events(run: EvidenceRun) -> list[dict[str, Any]]:
    path = run.directory / "events.jsonl"
    if not path.is_file():
        return []
    events = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def summarize_run(run: EvidenceRun) -> dict[str, Counter]:
    events = load_events(run)
    return {
        "protocol": Counter(event.get("protocol", "SYSTEM") for event in events),
        "event_type": Counter(event.get("event_type", "log") for event in events),
        "scope": Counter(event.get("scope", "UNKNOWN") for event in events),
        "source": Counter(event.get("source") or "unknown" for event in events),
    }


def compare_runs(base: EvidenceRun, current: EvidenceRun) -> dict[str, list[dict[str, Any]]]:
    left = summarize_run(base)
    right = summarize_run(current)
    diff = {}
    for category in left.keys() | right.keys():
        keys = set(left.get(category, {})) | set(right.get(category, {}))
        rows = []
        for key in sorted(keys):
            before = left.get(category, {}).get(key, 0)
            after = right.get(category, {}).get(key, 0)
            if before != after:
                rows.append({"key": key, "base": before, "current": after, "delta": after - before})
        diff[category] = rows
    return diff


def export_bundle(run: EvidenceRun, destination: str | Path) -> Path:
    destination = Path(destination).expanduser()
    if destination.suffix.lower() != ".zip":
        destination = destination.with_suffix(".zip")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ("manifest.json", "events.jsonl", "integrity.json"):
            source = run.directory / name
            if source.is_file() and not source.is_symlink():
                archive.write(source, arcname=f"{run.run_id}/{name}")
    return destination.resolve()
