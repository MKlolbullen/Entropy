from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_integrity_manifest(directory: str | Path) -> Path:
    root = Path(directory)
    files = {}
    for name in ("manifest.json", "events.jsonl"):
        path = root / name
        if path.is_file():
            files[name] = {"sha256": sha256_file(path), "size": path.stat().st_size}
    payload = {
        "algorithm": "SHA-256",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }
    output = root / "integrity.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output


def verify_integrity(directory: str | Path) -> tuple[bool, dict[str, str]]:
    root = Path(directory)
    path = root / "integrity.json"
    if not path.is_file():
        return False, {"integrity.json": "missing"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, {"integrity.json": "invalid"}
    status: dict[str, str] = {}
    ok = True
    for name, metadata in payload.get("files", {}).items():
        target = root / name
        if not target.is_file():
            status[name] = "missing"
            ok = False
            continue
        actual = sha256_file(target)
        expected = metadata.get("sha256")
        status[name] = "verified" if actual == expected else "mismatch"
        ok = ok and actual == expected
    return ok, status
