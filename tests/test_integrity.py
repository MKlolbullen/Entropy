from pathlib import Path

from lnkup.core.integrity import verify_integrity, write_integrity_manifest


def test_integrity_detects_tampering(tmp_path: Path):
    (tmp_path / "manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "events.jsonl").write_text("{}\n", encoding="utf-8")
    write_integrity_manifest(tmp_path)
    assert verify_integrity(tmp_path)[0] is True
    (tmp_path / "events.jsonl").write_text("changed\n", encoding="utf-8")
    ok, status = verify_integrity(tmp_path)
    assert ok is False
    assert status["events.jsonl"] == "mismatch"
