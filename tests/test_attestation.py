from pathlib import Path

from lnkup.core.attestation import attest_run, generate_signing_key, verify_attestation
from lnkup.core.integrity import write_integrity_manifest


def test_ed25519_attestation(tmp_path: Path):
    (tmp_path / "manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "events.jsonl").write_text("{}\n", encoding="utf-8")
    write_integrity_manifest(tmp_path)
    private, _ = generate_signing_key(tmp_path / "signing.pem")
    attest_run(tmp_path, private)
    ok, detail = verify_attestation(tmp_path)
    assert ok is True, detail
