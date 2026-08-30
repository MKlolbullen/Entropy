from pathlib import Path

from lnkup.core.attestation import attest_run, generate_signing_key, verify_attestation
from lnkup.core.integrity import write_integrity_manifest


def _create_evidence(root: Path) -> Path:
    (root / "manifest.json").write_text("{}", encoding="utf-8")
    (root / "events.jsonl").write_text("{}\n", encoding="utf-8")
    write_integrity_manifest(root)
    private, _ = generate_signing_key(root / "signing.pem")
    attest_run(root, private)
    return private


def test_ed25519_attestation(tmp_path: Path):
    _create_evidence(tmp_path)
    ok, detail = verify_attestation(tmp_path)
    assert ok is True, detail


def test_attestation_rejects_tampered_evidence(tmp_path: Path):
    _create_evidence(tmp_path)
    (tmp_path / "events.jsonl").write_text("tampered\n", encoding="utf-8")
    ok, detail = verify_attestation(tmp_path)
    assert ok is False
    assert "integrity" in detail.lower()
